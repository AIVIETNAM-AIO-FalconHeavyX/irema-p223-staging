"""Truy cập file tài liệu onboarding trong data/raw một cách an toàn."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from src.config import get_settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Bảng MIME type tối thiểu cho các định dạng file trong kho tài liệu.
_MIME_BY_SUFFIX: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
MIME_TYPES = _MIME_BY_SUFFIX

# Định dạng trình duyệt xem trực tiếp được (còn lại sẽ cho tải về).
INLINE_SUFFIXES = {".mp4", ".webm", ".pdf"}


def media_root() -> Path:
    """Thư mục gốc chứa tài liệu onboarding (mặc định data/raw)."""
    configured = Path(get_settings().onboarding_media_dir)
    root = configured if configured.is_absolute() else PROJECT_ROOT / configured
    return root.resolve()


def resolve_media_path(relative_path: str) -> Path:
    """Ghép đường dẫn tương đối vào media_root và chặn path traversal.

    Trả về đường dẫn tuyệt đối đã resolve. Ném ValueError nếu đường dẫn thoát ra
    ngoài thư mục gốc (ví dụ chứa "../") — bắt buộc vì path đến từ URL người dùng.
    """
    if relative_path.startswith("s3://"):
        relative_path = relative_path[5:]

    root = media_root()
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Đường dẫn nằm ngoài kho tài liệu onboarding.")

    if candidate.is_file():
        return candidate

    norm_name = normalize_path(candidate.name)

    if candidate.parent.exists():
        for p in candidate.parent.iterdir():
            if p.is_file() and normalize_path(p.name) == norm_name:
                return p.resolve()

    # Fallback: recursive search in root directory for matching filename
    for p in root.rglob("*"):
        if p.is_file() and normalize_path(p.name) == norm_name:
            return p.resolve()

    return candidate


def normalize_path(relative_path: str) -> str:
    """Chuẩn hoá Unicode về NFC để so khớp tên file tiếng Việt.

    macOS lưu tên file ở dạng NFD ("ề" = e + dấu), trình duyệt gửi lên NFC.
    Không chuẩn hoá thì phép so sánh chuỗi với catalog sẽ trượt.
    """
    return unicodedata.normalize("NFC", relative_path).strip("/")


def guess_media_type(path: Path) -> str:
    return _MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream")


def is_inline_viewable(path: Path) -> bool:
    return path.suffix.lower() in INLINE_SUFFIXES


def describe_file(path: Path) -> str:
    """Chuỗi mô tả ngắn cho UI, ví dụ "PDF · 2.1 MB"."""
    if not path.is_file():
        return "Không tìm thấy tệp"
    size = path.stat().st_size
    if size >= 1024 * 1024:
        readable = f"{size / (1024 * 1024):.1f} MB"
    else:
        readable = f"{max(1, size // 1024)} KB"
    return f"{path.suffix.lstrip('.').upper()} · {readable}"
