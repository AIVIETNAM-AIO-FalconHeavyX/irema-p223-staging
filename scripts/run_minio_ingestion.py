#!/usr/bin/env python3
import logging
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.rag_ingestion_pipeline import run_ingestion_pipeline
from src.cloud.s3_service import s3_service
from src.config import get_settings
from src.db import SessionLocal
from src.db.models import OnboardingStep
from src.preprocess.pipeline import PreprocessingPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_object_key(url_or_path: str, bucket_name: str) -> str | None:
    """Trích xuất object_key từ URL MinIO hoặc đường dẫn file."""
    if not url_or_path:
        return None
    if url_or_path.startswith("http"):
        parsed = urlparse(url_or_path)
        path = parsed.path.lstrip("/")
        # Nếu path bắt đầu bằng bucket_name (ví dụ: vinfast-onboarding/xxx.pdf)
        if path.startswith(bucket_name + "/"):
            return path[len(bucket_name) + 1 :]
        return path
    return url_or_path.lstrip("/")


def main():
    logger.info("=================================================================")
    logger.info("☁️ BẮT ĐẦU CLOUD-NATIVE INGESTION PIPELINE (MINIO + DB -> RAG)")
    logger.info("=================================================================")

    settings = get_settings()
    bucket_name = settings.s3_bucket_name

    # Thư mục tạm để chứa file raw tải từ MinIO
    tmp_raw_dir = Path("data/tmp_raw")
    if tmp_raw_dir.exists():
        shutil.rmtree(tmp_raw_dir)
    tmp_raw_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    downloaded_count = 0
    skipped_count = 0

    try:
        # 1. Lấy toàn bộ các bước và tài liệu từ PostgreSQL
        steps = db.query(OnboardingStep).all()
        logger.info(f"🔎 Tìm thấy {len(steps)} bài học Onboarding trong PostgreSQL.")

        for step in steps:
            role = (step.role_target or "general").lower()
            role_dir = tmp_raw_dir / role
            role_dir.mkdir(parents=True, exist_ok=True)

            resources = step.resources or []
            for res in resources:
                path_val = res.get("path", "")
                name_val = res.get("name", "").strip() or "document"
                # Làm sạch tên file để lưu ở local
                clean_name = "".join(c for c in name_val if c.isalnum() or c in (" ", "_", "-", ".")).strip()

                object_key = extract_object_key(path_val, bucket_name)
                if not object_key or not object_key.endswith(
                    (".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".mp4", ".txt")
                ):
                    continue

                ext = Path(object_key).suffix
                local_file_name = f"{clean_name}{ext}" if not clean_name.endswith(ext) else clean_name
                local_path = role_dir / local_file_name

                # Tải từ MinIO
                try:
                    s3_service.download_to_temp(object_key, str(local_path))
                    downloaded_count += 1
                except Exception as e:
                    logger.warning(f"Không thể tải object {object_key} từ MinIO: {e}")
                    skipped_count += 1

        logger.info(
            f"\n✅ Đã tải thành công {downloaded_count} tài liệu từ MinIO về {tmp_raw_dir} (bỏ qua/lỗi: {skipped_count})."
        )

        if downloaded_count == 0:
            logger.error("❌ Không có tài liệu nào được tải từ MinIO. Dừng pipeline.")
            return

        # 2. Chạy PreprocessingPipeline (Bóc tách dữ liệu -> Markdown)
        logger.info("\n⚙️ Bước 2: Bóc tách tài liệu thô thành Markdown...")
        pipeline = PreprocessingPipeline(
            raw_dir=str(tmp_raw_dir), processed_dir=settings.processed_data_dir, upload_to_minio=False
        )
        results = pipeline.run_all()
        logger.info(f"✅ Đã bóc tách {len(results)} file thành Markdown.")

        # 3. Chạy RAG Ingestion Pipeline (Clean -> Chunk -> ChromaDB + BM25)
        logger.info("\n⚙️ Bước 3: Chạy Pipeline tinh chỉnh, Chunking và VectorDB...")
        run_ingestion_pipeline(upload_minio=True)

    finally:
        db.close()
        # 4. Dọn dẹp thư mục tạm
        logger.info(f"\n🧹 Đang dọn dẹp thư mục tạm {tmp_raw_dir}...")
        if tmp_raw_dir.exists():
            shutil.rmtree(tmp_raw_dir)
        logger.info("🎉 HOÀN TẤT TOÀN BỘ QUÁ TRÌNH INGESTION!")


if __name__ == "__main__":
    main()
