#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from botocore.exceptions import ClientError

from src.cloud.s3_service import s3_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def empty_bucket():
    """Xóa tất cả các object hiện có trong bucket để làm sạch MinIO."""
    bucket_name = s3_service.bucket_name
    s3_client = s3_service.s3_client

    logger.info(f"Đang lấy danh sách các file trong bucket '{bucket_name}'...")
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)

        objects_to_delete = []
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    objects_to_delete.append({"Key": obj["Key"]})

        if not objects_to_delete:
            logger.info("Bucket đã trống. Không có file nào cần xóa.")
            return

        logger.info(f"Đã tìm thấy {len(objects_to_delete)} file. Tiến hành xóa toàn bộ...")

        # S3 delete_objects takes max 1000 keys per request
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i : i + 1000]
            s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": batch, "Quiet": True})
        logger.info("✅ Đã xóa sạch MinIO bucket.")
    except ClientError as e:
        logger.error(f"Lỗi khi xóa bucket: {e}")


def seed_bucket_from_raw():
    """Quét data/raw và upload lên MinIO, giữ nguyên cấu trúc thư mục."""
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.error(f"Thư mục {raw_dir} không tồn tại!")
        return

    logger.info(f"Đang quét thư mục {raw_dir}...")
    all_files = [f for f in raw_dir.rglob("*") if f.is_file() and not f.name.startswith(".")]

    logger.info(f"Tìm thấy {len(all_files)} file. Tiến hành upload...")

    success_count = 0
    for f in all_files:
        object_key = str(f.relative_to(raw_dir))
        try:
            s3_service.s3_client.upload_file(str(f), s3_service.bucket_name, object_key)
            success_count += 1
            if success_count % 50 == 0:
                logger.info(f"Đã upload {success_count}/{len(all_files)} file...")
        except Exception as e:
            logger.error(f"Lỗi khi upload {object_key}: {e}")

    logger.info(f"✅ Hoàn tất! Đã upload thành công {success_count}/{len(all_files)} file.")


def main():
    logger.info("=================================================================")
    logger.info(" BẮT ĐẦU DỌN DẸP & SEED DỮ LIỆU TỪ DATA/RAW LÊN MINIO ")
    logger.info("=================================================================")

    # 1. Ensure bucket exists
    s3_service.ensure_bucket_exists()

    # 2. Xoá trắng bucket cũ
    empty_bucket()

    # 3. Upload dữ liệu mới giữ nguyên cấu trúc
    seed_bucket_from_raw()


if __name__ == "__main__":
    main()
