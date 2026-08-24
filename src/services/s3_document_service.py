"""S3 Document Service — Quét MinIO bucket, đồng bộ DocumentRegistry, và xử lý tài liệu mới."""

from __future__ import annotations

import logging
import tempfile
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from src.cloud.s3_service import s3_service
from src.config import get_settings
from src.db.models import DocStatus, DocumentRegistry

logger = logging.getLogger(__name__)

# Supported file extensions for processing
_SUPPORTED_EXTS = {".pdf", ".docx", ".pptx", ".xlsx", ".mp4", ".webm"}


_s3_ready = False


def is_s3_ready() -> bool:
    """Kiểm tra xem quá trình đồng bộ S3/MinIO lần đầu đã hoàn tất hay chưa."""
    return _s3_ready


def set_s3_ready(status: bool) -> None:
    """Cập nhật cờ sẵn sàng của dịch vụ S3 Document Service."""
    global _s3_ready
    _s3_ready = status


def _safe_unlink(file_path: Path) -> None:
    """Xóa file tạm một cách an toàn trên Windows (thu hồi GC và thử lại nếu bị lock tạm thời)."""
    import gc
    import time

    gc.collect()
    for _ in range(5):
        try:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            return
        except Exception:
            time.sleep(0.1)
            gc.collect()


class S3DocumentService:
    """Đồng bộ và xử lý tài liệu từ MinIO."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.role_mapping = self.settings.role_mapping

    # ------------------------------------------------------------------
    # Sync: Quét MinIO → cập nhật DB registry
    # ------------------------------------------------------------------

    def sync_registry(self, db: Session) -> dict:
        """Quét tất cả objects trong MinIO bucket, so sánh với DB, tạo record mới nếu cần.

        Returns:
            dict với thống kê: new, updated, unchanged, skipped
        """
        stats = {"new": 0, "updated": 0, "unchanged": 0, "skipped": 0}

        try:
            objects = self._list_s3_objects()
        except Exception as e:
            logger.error(f"Không thể kết nối MinIO: {e}")
            return stats

        for obj in objects:
            s3_key = unicodedata.normalize("NFC", obj["Key"])
            filename = s3_key.split("/")[-1]
            ext = Path(filename).suffix.lower()

            # Bỏ qua file không hỗ trợ
            if ext not in _SUPPORTED_EXTS:
                stats["skipped"] += 1
                continue

            # Xác định category và role từ đường dẫn S3
            parts = s3_key.split("/")
            category = parts[0] if len(parts) > 1 else "General_doc"
            role = self.role_mapping.get(category, "general")

            # Tính hash dựa trên ETag (MD5 từ S3) + size
            etag = obj.get("ETag", "").strip('"')
            content_hash = f"s3:{etag}"
            file_size = obj.get("Size", 0)

            # Kiểm tra record trong DB
            existing = db.query(DocumentRegistry).filter(
                DocumentRegistry.s3_key == s3_key
            ).first()

            if existing:
                if existing.content_hash == content_hash:
                    stats["unchanged"] += 1
                else:
                    # File đã thay đổi → đánh dấu lại pending
                    existing.content_hash = content_hash
                    existing.file_size = file_size
                    existing.status = DocStatus.pending
                    existing.error_message = None
                    stats["updated"] += 1
            else:
                # File mới
                doc = DocumentRegistry(
                    s3_key=s3_key,
                    filename=filename,
                    category=category,
                    role=role,
                    file_size=file_size,
                    content_hash=content_hash,
                    status=DocStatus.pending,
                )
                db.add(doc)
                stats["new"] += 1

        db.commit()
        logger.info(
            f"Sync registry: {stats['new']} new, {stats['updated']} updated, "
            f"{stats['unchanged']} unchanged, {stats['skipped']} skipped"
        )
        return stats

    # ------------------------------------------------------------------
    # Process: Download từ S3 → chạy pipeline
    # ------------------------------------------------------------------

    def process_pending(self, db: Session) -> dict:
        """Xử lý tất cả document có status 'pending'.

        Returns:
            dict với thống kê: processed, failed
        """
        from src.preprocess.pipeline import PreprocessingPipeline

        stats = {"processed": 0, "failed": 0}
        pipeline = PreprocessingPipeline()

        pending = db.query(DocumentRegistry).filter(
            DocumentRegistry.status == DocStatus.pending
        ).all()

        if not pending:
            logger.info("Không có document nào cần xử lý.")
            return stats

        logger.info(f"Bắt đầu xử lý {len(pending)} documents từ MinIO...")

        for doc in pending:
            doc.status = DocStatus.processing
            db.commit()

            try:
                # Download file từ S3 về temp
                local_path = self.fetch_to_temp(doc.s3_key)

                # Chạy pipeline xử lý
                pipeline.process_single_file(
                    file_path=local_path,
                    category=doc.category,
                    role=doc.role,
                )

                doc.status = DocStatus.processed
                doc.processed_at = datetime.now(UTC)
                doc.error_message = None
                stats["processed"] += 1
                logger.info(f"✓ Processed: {doc.s3_key}")

            except Exception as e:
                doc.status = DocStatus.failed
                doc.error_message = str(e)[:500]
                stats["failed"] += 1
                logger.error(f"✗ Failed: {doc.s3_key} — {e}")

            finally:
                # Dọn temp file an toàn (chống WinError 32 trên Windows)
                if "local_path" in locals() and local_path is not None:
                    _safe_unlink(local_path)
                db.commit()

        logger.info(f"Xử lý xong: {stats['processed']} OK, {stats['failed']} lỗi")
        return stats

    def retry_failed_documents(self, db: Session, doc_ids: list[int] | None = None) -> int:
        """Chuyển trạng thái các document 'failed' về 'pending' để thử lại.

        Returns:
            Số lượng document được reset về pending
        """
        query = db.query(DocumentRegistry).filter(DocumentRegistry.status == DocStatus.failed)
        if doc_ids:
            query = query.filter(DocumentRegistry.id.in_(doc_ids))

        failed_docs = query.all()
        count = len(failed_docs)
        for doc in failed_docs:
            doc.status = DocStatus.pending
            doc.error_message = None

        db.commit()
        logger.info(f"Đã chuyển {count} tài liệu failed về pending để thử lại.")
        return count

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def fetch_to_temp(self, s3_key: str) -> Path:
        """Download file từ S3 về thư mục tạm. Trả về Path tới file tạm."""
        suffix = Path(s3_key).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="s3doc_") as tmp:
            tmp_path = Path(tmp.name)

        s3_service.s3_client.download_file(
            s3_service.bucket_name,
            s3_key,
            str(tmp_path),
        )
        logger.debug(f"Downloaded {s3_key} → {tmp_path}")
        return tmp_path

    def _list_s3_objects(self) -> list[dict]:
        """Liệt kê tất cả objects trong MinIO bucket."""
        objects = []
        paginator = s3_service.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=s3_service.bucket_name):
            objects.extend(page.get("Contents", []))
        return objects
