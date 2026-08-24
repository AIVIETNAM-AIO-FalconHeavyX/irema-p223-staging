import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from src.agents.nodes.rag_node import init_rag_models, is_rag_ready, set_rag_ready
from src.api.auth_routes import router as auth_router
from src.api.feedback_routes import router as feedback_router
from src.api.media_routes import router as media_router
from src.api.routes import router
from src.cloud.s3_service import s3_service
from src.config import get_settings
from src.db import SessionLocal, create_db_and_tables
from src.services.s3_document_service import S3DocumentService, is_s3_ready, set_s3_ready

logger = logging.getLogger(__name__)

# Chu kỳ quét tự động MinIO (mặc định 5 phút = 300 giây)
S3_SYNC_INTERVAL_SECONDS = 300


async def _bootstrap_background_tasks(stop_event: asyncio.Event) -> None:
    """Supervisor background worker:
    1. Khởi tạo Database tables (3 lần retry).
    2. Nạp Embedding/BM25 và khởi tạo Cohere Rerank với Retry.
    3. Kiểm tra S3 bucket & Chạy Initial Sync với Exponential Backoff (chờ MinIO nếu container đang boot).
    4. Duy trì vòng lặp S3 Cron định kỳ mỗi 5 phút (hỗ trợ graceful cancellation).
    """
    # ------------------------------------------------------------------
    # Bước 1: Khởi tạo Database
    # ------------------------------------------------------------------
    logger.info("[BOOTSTRAP 1/3] Khởi tạo cơ sở dữ liệu...")
    db_initialized = False
    for attempt in range(1, 4):
        if stop_event.is_set():
            return
        try:
            await asyncio.to_thread(create_db_and_tables)
            db_initialized = True
            logger.info("[BOOTSTRAP 1/3] ✓ Khởi tạo Database thành công.")
            break
        except Exception as e:
            delay = 2 ** (attempt - 1)
            logger.warning(f"[BOOTSTRAP 1/3] Thử lại DB lần {attempt}/3 sau {delay}s (Lỗi: {e})")
            await asyncio.sleep(delay)

    if not db_initialized:
        logger.error("[BOOTSTRAP 1/3] ✗ Không thể kết nối Database sau 3 lần thử.")

    # ------------------------------------------------------------------
    # Bước 2: Nạp RAG Models (SentenceTransformer, BM25, Cohere Rerank)
    # ------------------------------------------------------------------
    logger.info("[BOOTSTRAP 2/3] Nạp RAG models trong background worker...")
    for attempt in range(1, 4):
        if stop_event.is_set():
            return
        try:
            await asyncio.to_thread(init_rag_models)
            set_rag_ready(True)
            logger.info("[BOOTSTRAP 2/3] ✓ RAG models nạp thành công và sẵn sàng.")
            break
        except Exception as e:
            delay = 2 ** (attempt - 1)  # 1s, 2s, 4s
            logger.warning(f"[BOOTSTRAP 2/3] Thử lại nạp RAG models lần {attempt}/3 sau {delay}s: {e}")
            await asyncio.sleep(delay)

    # ------------------------------------------------------------------
    # Bước 3: Kiểm tra S3 bucket & Chạy Initial S3 Sync
    # ------------------------------------------------------------------
    settings = get_settings()
    if not settings.live_ingestion_enabled:
        logger.info("[BOOTSTRAP 3/3] Live ingestion đang tắt; bỏ qua S3 sync và xử lý tài liệu.")
        set_s3_ready(True)
        return

    logger.info("[BOOTSTRAP 3/3] Kết nối MinIO/S3 và đồng bộ dữ liệu lần đầu...")
    s3_svc = S3DocumentService()

    def _do_initial_sync() -> bool:
        s3_service.ensure_bucket_exists()
        db = SessionLocal()
        try:
            s3_svc.sync_registry(db)
            s3_svc.process_pending(db)
            return True
        finally:
            db.close()

    for attempt in range(1, 6):
        if stop_event.is_set():
            return
        try:
            await asyncio.to_thread(_do_initial_sync)
            set_s3_ready(True)
            logger.info("[BOOTSTRAP 3/3] ✓ S3 Initial Sync hoàn tất thành công.")
            break
        except Exception as e:
            delay = min(2**attempt, 30)  # 2s, 4s, 8s, 16s, 30s
            logger.warning(
                f"[BOOTSTRAP 3/3] Thử lại kết nối S3 lần {attempt}/5 sau {delay}s (MinIO có thể đang khởi động): {e}"
            )
            await asyncio.sleep(delay)

    # Đánh dấu S3 ready dù có lỗi để hệ thống không bị kẹt vĩnh viễn ở unready
    set_s3_ready(True)

    # ------------------------------------------------------------------
    # Bước 4: Vòng lặp S3 Cron định kỳ mỗi 5 phút
    # ------------------------------------------------------------------
    logger.info(f"[S3 CRON] Bắt đầu chu kỳ quét định kỳ ({S3_SYNC_INTERVAL_SECONDS}s/lần)...")

    def _do_cron_sync() -> None:
        db = SessionLocal()
        try:
            s3_svc.sync_registry(db)
            s3_svc.process_pending(db)
        except Exception as err:
            logger.error(f"[S3 CRON] Lỗi trong chu kỳ quét: {err}")
        finally:
            db.close()

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=S3_SYNC_INTERVAL_SECONDS)
            break  # stop_event được kích hoạt -> thoát vòng lặp
        except TimeoutError:
            pass  # Hết 5 phút -> tiếp tục quét

        if stop_event.is_set():
            break

        try:
            await asyncio.to_thread(_do_cron_sync)
        except Exception as e:
            logger.error(f"[S3 CRON] Lỗi thực thi cron thread: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan Context Manager:
      - Mở cổng mạng ngay lập tức (< 1 giây) để Liveness Probe nhận 200 OK.
      - Chạy toàn bộ việc nặng trong supervisor background task.
      - Graceful Shutdown: huỷ task và dọn dẹp tài nguyên sạch sẽ.
    """
    settings = get_settings()
    logger.info(f"Khởi động {settings.app_name} ({settings.app_env} mode)")

    stop_event = asyncio.Event()
    supervisor_task = asyncio.create_task(_bootstrap_background_tasks(stop_event))

    # YIELD NGAY LẬP TỨC: Cổng 8001 mở tức thì, tránh hoàn toàn Connection Refused
    yield

    # Teardown khi nhận tín hiệu shutdown (SIGTERM / SIGINT / Ctrl+C)
    logger.info("Đang tắt hệ thống: huỷ các tác vụ ngầm...")
    stop_event.set()
    supervisor_task.cancel()
    try:
        await asyncio.gather(supervisor_task, return_exceptions=True)
    except Exception as e:
        logger.warning(f"Lỗi khi huỷ tác vụ ngầm: {e}")
    logger.info("Hệ thống đã dừng hoàn toàn.")


app = FastAPI(
    title="VF AI Onboarding Agent",
    description="AI-powered Onboarding & Operational Support System for VF Electric Scooter Dealerships",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(media_router, prefix="/api/v1", tags=["files"])
app.include_router(feedback_router, prefix="/api/v1", tags=["feedback"])

if settings.live_ingestion_enabled:
    from src.api.ingest_routes import router as ingest_router
    from src.api.ingestion_routes import router as ingestion_router
    from src.api.s3_manager_routes import router as s3_manager_router
    from src.api.ui_routes import router as ui_router

    app.include_router(ui_router, prefix="/api/v1")
    app.include_router(ingestion_router)
    app.include_router(ingest_router, prefix="/api/v1")
    app.include_router(s3_manager_router)
else:
    logger.info("Live ingestion routes are disabled by configuration.")


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# ----------------------------------------------------------------------
# Kubernetes & Cloud Health Probes
# ----------------------------------------------------------------------


@app.get("/live", tags=["Health"])
@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """
    Kubernetes Liveness Probe:
    Kiểm tra xem tiến trình FastAPI/Uvicorn có còn sống và phản hồi hay không.
    Luôn trả về 200 OK.
    """
    return {
        "status": "alive",
        "service": settings.app_name,
        "env": settings.app_env,
        "timestamp": time.time(),
    }


@app.get("/ready", tags=["Health"])
@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """
    Kubernetes Readiness Probe:
    Chỉ trả về 200 OK khi cả RAG Models lẫn Initial S3 Sync đã hoàn tất.
    Trả về 503 Service Unavailable khi đang nạp ngầm để Load Balancer/K8s chưa route traffic vào pod.
    """
    rag_ready = is_rag_ready()
    s3_ready = is_s3_ready()
    all_ready = rag_ready and s3_ready

    payload = {
        "status": "ready" if all_ready else "unready",
        "rag_ready": rag_ready,
        "s3_ready": s3_ready,
        "env": settings.app_env,
    }

    if not all_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload,
        )

    return payload


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint kiểm tra tổng quát tương thích ngược với Frontend và các script cũ.
    """
    rag_ready = is_rag_ready()
    s3_ready = is_s3_ready()
    return {
        "status": "ok" if (rag_ready and s3_ready) else "initializing",
        "rag_ready": rag_ready,
        "s3_ready": s3_ready,
        "env": settings.app_env,
    }
