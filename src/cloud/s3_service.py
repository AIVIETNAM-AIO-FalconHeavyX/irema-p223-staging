import logging
import re

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()


class S3Service:
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.aws_s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    def ensure_bucket_exists(self) -> None:
        """Ensure the configured bucket exists without changing its privacy."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 Bucket '{self.bucket_name}' đã tồn tại.")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                logger.info(f"S3 Bucket '{self.bucket_name}' chưa có. Đang tạo mới...")
                # R2 uses region "auto"; us-east-1 and auto both omit the
                # AWS-specific LocationConstraint payload.
                if settings.aws_region in ("auto", "us-east-1"):
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
                    )
                logger.info(f"Đã tạo private bucket '{self.bucket_name}' thành công.")
            else:
                raise e

    def upload_file(self, file_path: str, object_name: str) -> str:
        """Upload một file từ local lên S3.

        Args:
            file_path: Đường dẫn file ở local.
            object_name: Tên file trên S3 (thường là UUID).

        Returns:
            object_name (để lưu vào database).
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            return object_name
        except ClientError as e:
            logger.error(f"Lỗi khi upload file {file_path} lên S3: {e}")
            raise

    def get_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """Tạo URL dùng một lần (presigned URL) để Frontend tải file.

        Mặc định URL hết hạn sau 1 giờ.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            logger.error(f"Lỗi khi tạo presigned URL cho {object_name}: {e}")
            raise

    def get_public_url(self, object_name: str) -> str:
        """Compatibility alias that returns a temporary private-object URL."""
        return self.get_presigned_url(object_name)

    # ------------------------------------------------------------------
    # Phương thức dành cho Track 2: Upload file đã xử lý lên MinIO
    # ------------------------------------------------------------------

    def upload_raw_file(self, local_path: str, role: str, filename: str) -> str:
        """Upload file thô (PDF, DOCX...) lên MinIO dưới prefix raw/<role>/filename.

        Returns:
            object_key dạng: raw/<role>/<filename>
        """
        object_key = f"raw/{role}/{filename}"
        self.s3_client.upload_file(local_path, self.bucket_name, object_key)
        logger.info(f"Đã upload file thô: {object_key}")
        return object_key

    def upload_processed_md(self, local_path: str, role: str, filename: str) -> str:
        """Upload file Markdown đã xử lý (PII removed) lên MinIO dưới prefix processed/<role>/filename.md.

        Args:
            local_path: Đường dẫn file .md trên máy local.
            role: Vai trò (ví dụ: 'sales', 'accounting').
            filename: Tên file (ví dụ: 'sample.md').

        Returns:
            object_key dạng: processed/<role>/<filename>
        """
        if not filename.endswith(".md"):
            filename = filename + ".md"
        object_key = f"processed/{role}/{filename}"
        self.s3_client.upload_file(local_path, self.bucket_name, object_key)
        logger.info(f"Đã upload file Markdown đã xử lý: {object_key}")
        return object_key

    def list_raw_objects(self, role: str | None = None) -> list[str]:
        """Liệt kê tất cả các object key của file thô (raw) trên MinIO.

        Args:
            role: Nếu có, chỉ liệt kê file của role đó (ví dụ: 'sales').
                  Nếu None, liệt kê tất cả mọi role.

        Returns:
            Danh sách object_key (ví dụ: ['raw/sales/sample.pdf', ...])
        """
        prefix = f"raw/{role}/" if role else "raw/"
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            keys = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key != prefix:  # ignore directory itself if present
                    keys.append(key)
            return keys
        except ClientError as e:
            logger.error(f"Lỗi khi list raw objects: {e}")
            return []

    def get_latest_version(self, base_object_key: str) -> str:
        """
        Tìm phiên bản mới nhất của file trên MinIO.
        Ví dụ: base_object_key = 'General_doc/TaiLieuChung/1. Tài liệu.pdf'
        Nếu trên MinIO có '1. Tài liệu v2.pdf', hàm sẽ trả về key của v2.
        """
        parts = base_object_key.split("/")
        prefix = "/".join(parts[:-1]) + "/" if len(parts) > 1 else ""
        filename = parts[-1]

        if "." not in filename:
            return base_object_key

        name_no_ext, ext = filename.rsplit(".", 1)
        pattern = re.compile(
            re.escape(name_no_ext) + r"(?:[-_\s]*(?:v|version\s*)(\d+))?\." + re.escape(ext), re.IGNORECASE
        )

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            max_version = -1
            latest_key = base_object_key

            for obj in response.get("Contents", []):
                key = obj["Key"]
                f_name = key.replace(prefix, "")
                match = pattern.match(f_name)
                if match:
                    version = match.group(1)
                    version_num = int(version) if version else 0
                    if version_num >= max_version:
                        max_version = version_num
                        latest_key = key
            return latest_key
        except Exception as e:
            logger.debug(f"Lỗi khi get_latest_version (offline/fallback): {e}")
            return base_object_key

    def list_processed_mds(self, role: str | None = None) -> list[str]:
        """Liệt kê tất cả các object key của file .md đã xử lý trên MinIO.

        Args:
            role: Nếu có, chỉ liệt kê file của role đó (ví dụ: 'sales').
                  Nếu None, liệt kê tất cả mọi role.

        Returns:
            Danh sách object_key (ví dụ: ['processed/sales/sample.md', ...])
        """
        prefix = f"processed/{role}/" if role else "processed/"
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        keys = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".md"):
                keys.append(key)
        return keys

    def download_to_temp(self, object_key: str, local_path: str) -> None:
        """Tải một object từ MinIO về đường dẫn local_path.

        Args:
            object_key: Đường dẫn object trên MinIO (ví dụ: 'processed/sales/sample.md').
            local_path: Đường dẫn đích trên máy local để lưu file.
        """
        self.s3_client.download_file(self.bucket_name, object_key, local_path)
        logger.info(f"Đã tải file từ MinIO: {object_key} → {local_path}")

    def explore_bucket(self, prefix: str = "") -> list:
        """Lấy danh sách thư mục và file trong bucket tại một prefix (giống lệnh ls)."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix, Delimiter="/")
            items = []

            # Thêm thư mục (CommonPrefixes)
            for cp in response.get("CommonPrefixes", []):
                items.append(
                    {
                        "name": cp["Prefix"].split("/")[-2] + "/",
                        "path": cp["Prefix"],
                        "is_dir": True,
                        "size": 0,
                        "last_modified": None,
                    }
                )

            # Thêm file (Contents)
            for obj in response.get("Contents", []):
                # Bỏ qua chính thư mục hiện tại nếu nó được trả về như 1 object
                if obj["Key"] == prefix:
                    continue
                items.append(
                    {
                        "name": obj["Key"].split("/")[-1],
                        "path": obj["Key"],
                        "is_dir": False,
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat() if obj.get("LastModified") else None,
                    }
                )

            return items
        except Exception as e:
            logger.error(f"Lỗi khi explore_bucket: {e}")
            return []

    def delete_object(self, object_key: str) -> bool:
        """Xoá một file khỏi S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            logger.error(f"Lỗi khi xoá {object_key}: {e}")
            return False

    def object_exists(self, object_key: str) -> bool:
        """Kiểm tra xem file có tồn tại trên S3 không (thử cả NFC và NFD)."""
        import unicodedata

        candidates = [object_key, unicodedata.normalize("NFC", object_key), unicodedata.normalize("NFD", object_key)]
        for candidate in dict.fromkeys(candidates):
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=candidate)
                return True
            except ClientError:
                continue
            except Exception:
                pass
        return False

    def upload_file_with_metadata(self, file_path: str, object_key: str, metadata: dict) -> str:
        """Upload file kèm user-defined metadata."""
        try:
            extra_args = {"Metadata": metadata}
            self.s3_client.upload_file(file_path, self.bucket_name, object_key, ExtraArgs=extra_args)
            return object_key
        except ClientError as e:
            logger.error(f"Lỗi khi upload có metadata cho {object_key}: {e}")
            raise


# Khởi tạo instance S3Service dùng chung (Singleton)
s3_service = S3Service()
