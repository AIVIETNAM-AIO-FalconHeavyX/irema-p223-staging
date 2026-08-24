import os
import sys
import unicodedata
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Helper to avoid changing all logger.success calls
logger.success = logger.info
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.cloud.s3_service import s3_service
from src.cloud.security_scanner import SecurityScannerError, sanitize_file
from src.config import Settings
from src.db.models import OnboardingStep

settings = Settings()
engine = create_engine(settings.database_url)


def main():
    logger.info("Bắt đầu quá trình Migration tài liệu lên AWS S3 (MinIO)...")

    # 1. Đảm bảo Bucket tồn tại
    s3_service.ensure_bucket_exists()

    with Session(engine) as db:
        steps = db.query(OnboardingStep).all()
        total_uploaded = 0

        for step in steps:
            # resources cột hiện tại là list các dict
            resources = step.resources
            if not resources:
                continue

            updated = False
            for res in resources:
                path_val = res.get("path", "")

                # Bỏ qua nếu đã là URL (http) hoặc không có file
                if path_val.startswith("http") or not path_val:
                    continue

                # Đường dẫn tuyệt đối tới file tĩnh ở local
                # Tránh dùng .name vì path_val có thể chứa thư mục con
                full_path = Path(settings.onboarding_media_dir) / path_val
                if not full_path.exists():
                    full_path = Path(path_val)  # Thử đường dẫn cũ
                if not full_path.exists():
                    # Thử khớp Unicode NFC / NFD cho tên file tiếng Việt
                    target_p = Path(settings.onboarding_media_dir) / path_val
                    parent_dir = target_p.parent
                    found_path = None
                    if parent_dir.exists():
                        target_nfc = unicodedata.normalize("NFC", target_p.name)
                        target_nfd = unicodedata.normalize("NFD", target_p.name)
                        for child in parent_dir.iterdir():
                            c_nfc = unicodedata.normalize("NFC", child.name)
                            c_nfd = unicodedata.normalize("NFD", child.name)
                            if c_nfc in (target_nfc, target_nfd) or c_nfd in (target_nfc, target_nfd):
                                found_path = child
                                break
                    if found_path:
                        full_path = found_path
                    else:
                        logger.warning(f"Không tìm thấy file ở local: {path_val}")
                        continue

                file_ext = full_path.suffix
                new_object_name = f"{uuid.uuid4()}{file_ext}"

                try:
                    logger.info(f"Đang xử lý file: {full_path.name}")
                    # 2. Security Sanitization (MIME & ClamAV)
                    sanitize_file(str(full_path))
                    logger.success(f" - [Bảo mật] File {full_path.name} an toàn.")

                    # 3. Upload lên Cloud
                    s3_service.upload_file(str(full_path), new_object_name)

                    # 4. Tạo S3 URL
                    s3_url = s3_service.get_public_url(new_object_name)

                    # Cập nhật đường dẫn trong PostgreSQL
                    res["path"] = s3_url
                    logger.success(f" - [Đám mây] Đã upload: {s3_url}")
                    updated = True
                    total_uploaded += 1

                except SecurityScannerError as e:
                    logger.error(f" - [Bảo mật] File {full_path.name} bị từ chối: {e}")
                except Exception as e:
                    logger.error(f" - [Lỗi] {full_path.name}: {e}")

            # Cập nhật lại cột JSON
            if updated:
                from sqlalchemy.orm.attributes import flag_modified

                step.resources = resources
                flag_modified(step, "resources")
                db.add(step)

        db.commit()
        logger.info(f"Hoàn thành Migration! Tổng cộng {total_uploaded} file đã được đưa lên Cloud Storage.")


if __name__ == "__main__":
    main()
