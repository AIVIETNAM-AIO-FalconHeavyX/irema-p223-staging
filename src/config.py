from functools import lru_cache
from typing import Literal

from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings

    SettingsConfigDict = None


class Settings(BaseSettings):
    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )
    else:
        model_config = {"extra": "ignore"}

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8001, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    # Keep document upload/reindexing disabled until the worker-backed pipeline
    # and durable ingestion job state are ready for production.
    live_ingestion_enabled: bool = False
    # Retained only for backwards-compatible configuration parsing. Automatic
    # startup ingestion is intentionally disabled; use the admin run API.
    legacy_startup_ingestion: bool = False

    # LLM
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    cohere_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    gemini_model_name: str = "gemini-1.5-flash"
    rerank_model_name: str = "rerank-v4.0-pro"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Langfuse (Localhost Tracing — 100% Privacy)
    langfuse_enabled: bool = True
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # Braintrust (Evaluation & Benchmark)
    braintrust_api_key: str = ""
    braintrust_project_name: str = "p223-agent"
    braintrust_tracing_enabled: bool = False

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Security
    jwt_secret_key: str = ""
    resend_api_key: str = ""
    email_from: str = ""
    frontend_url: str = "http://localhost:5173"
    invite_ttl_hours: int = Field(default=72, ge=1, le=720)

    # AWS S3 (MinIO)
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    aws_region: str = "auto"
    aws_s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket_name: str = "vinfast-onboarding"

    # Security (ClamAV)
    clamav_host: str = "localhost"
    clamav_port: int = 3310

    # Kho tài liệu onboarding phục vụ qua API /api/v1/files (tương đối so với gốc repo)
    onboarding_media_dir: str = "data/raw"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"
    retrieval_backend: Literal["legacy", "postgres"] = "legacy"
    bm25_index_path: str = "./data/bm25_index.pkl"

    # Preprocessing Pipeline
    raw_data_dir: str = "Data/raw"
    processed_data_dir: str = "Data/processed"
    role_mapping: dict[str, str] = Field(
        default_factory=lambda: {
            "KeToan": "accounting",
            "Sale": "sales",
            "KTV": "technician",
            "Manager": "owner",
            "General_doc": "general",
            "Huong_dan_DMS": "general",
        }
    )
    access_scope_mapping: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "KeToan": ["accounting"],
            "Sale": ["sales"],
            "KTV": ["technician"],
            "Manager": ["accounting", "sales", "technician", "owner", "general"],
            "General_doc": ["accounting", "sales", "technician", "owner", "general"],
            "Huong_dan_DMS": ["accounting", "sales", "technician", "owner", "general"],
        }
    )
    pii_enabled: bool = True
    pii_remove: bool = True
    pii_confidence_threshold: float = 0.7
    pii_entities: list[str] = Field(
        default_factory=lambda: [
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "ID_NUMBER",
            "BANK_ACCOUNT",
            "CREDIT_CARD",
            "ADDRESS",
            "CUSTOMER_ID",
            "EMPLOYEE_ID",
            "VEHICLE_PLATE",
            "USERNAME",
            "PASSWORD",
        ]
    )
    video_model: str = "large-v3"
    video_language: str = "vi"

    # MinerU Configuration
    mineru_enabled: bool = True
    mineru_device: str = "auto"  # "auto", "cpu", "cuda"
    chandra_enabled: bool = False

    whisper_download_root: str = "./models/whisper"  # Model sẽ được tải về đây và dùng offline các lần sau

    # OCR post-filter thresholds (Tier 1 & 2 background-text suppression)
    ocr_confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    ocr_min_text_height_ratio: float = Field(default=0.015, ge=0.0, le=1.0)
    ocr_orientation_threshold: float = Field(default=15.0, ge=0.0, le=90.0)

    # OCR Tier 3 — Color-contrast filter (background text suppression)
    # Loại bỏ text mà màu sắc quá gần với màu nền (luminance difference thấp)
    # Giá trị 0-255: text với lum_diff < threshold bị loại. 0 = tắt tính năng.
    ocr_contrast_threshold: float = Field(default=30.0, ge=0.0, le=255.0)

    # OCR Deskew — Tự động xoay thẳng ảnh bị nghiêng trước khi chạy OCR
    # Giúp cải thiện đáng kể độ chính xác OCR trên scanned PDF bị scan lệch.
    ocr_deskew_enabled: bool = True

    # Cohere relevance scores are normalized to [0, 1]. Keep zero as the
    # deployment default until the project ground-truth set calibrates a
    # stricter domain threshold.
    reranker_min_score: float = Field(default=0.0, ge=0.0, le=1.0)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env == "production" and not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be set in production")
    if settings.app_env == "production" and settings.database_url.startswith("sqlite"):
        raise RuntimeError("Production requires PostgreSQL; SQLite is not allowed")
    return settings
