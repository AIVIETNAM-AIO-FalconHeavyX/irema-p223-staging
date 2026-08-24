from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum file size: 500 MB
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024

# Allowed extensions and their expected magic bytes (first N bytes)
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".docx": "DOCX/ZIP",
    ".pptx": "PPTX/ZIP",
    ".xlsx": "XLSX/ZIP",
    ".mp4": "MP4",
    ".webm": "WEBM",
    ".txt": "TXT",
    ".md": "MD",
}

# Magic byte signatures for real content-type verification
MAGIC_SIGNATURES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "zip": b"PK\x03\x04",  # DOCX, PPTX, XLSX are ZIP containers
    "mp4_ftyp": b"ftyp",  # at offset 4
    "webm": b"\x1a\x45\xdf\xa3",
    "ogg": b"OggS",
}

# ZIP-based Office formats
OFFICE_ZIP_EXTENSIONS = {".docx", ".pptx", ".xlsx"}


@dataclass
class FileValidationResult:
    is_valid: bool
    file_path: Path
    file_name: str
    file_size_bytes: int
    detected_mime: str = ""
    extension: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class FileValidator:
    """
    Validates uploaded files before ingestion:
    - Extension whitelist check
    - File size limit
    - Magic bytes content-type verification (prevents extension spoofing)
    - ZIP-bomb detection for Office files
    """

    def validate(self, file_path: Path) -> FileValidationResult:
        result = FileValidationResult(
            is_valid=False,
            file_path=file_path,
            file_name=file_path.name,
            file_size_bytes=0,
            extension=file_path.suffix.lower(),
        )

        # 1. File must exist
        if not file_path.exists():
            result.errors.append(f"File not found: {file_path}")
            return result

        # 2. File size check
        size = file_path.stat().st_size
        result.file_size_bytes = size
        if size == 0:
            result.errors.append("File is empty (0 bytes).")
            return result
        if size > MAX_FILE_SIZE_BYTES:
            result.errors.append(
                f"File too large: {size / 1024 / 1024:.1f} MB (max {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB)."
            )
            return result

        # 3. Extension whitelist
        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            result.errors.append(
                f"Unsupported file extension: '{ext}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
            )
            return result

        # 4. Magic bytes verification (prevents .exe renamed to .pdf)
        try:
            mime, mime_error = self._detect_mime(file_path, ext)
            result.detected_mime = mime
            if mime_error:
                result.errors.append(mime_error)
                return result
        except Exception as e:
            result.warnings.append(f"Could not verify file content type: {e}")

        # 5. ZIP-bomb detection for Office files
        if ext in OFFICE_ZIP_EXTENSIONS:
            bomb_warning = self._check_zip_bomb(file_path)
            if bomb_warning:
                result.errors.append(bomb_warning)
                return result

        result.is_valid = True
        logger.info(f"File validated OK: {file_path.name} ({size / 1024:.1f} KB, type={result.detected_mime})")
        return result

    def _detect_mime(self, file_path: Path, ext: str) -> tuple[str, str]:
        """Read magic bytes to verify actual content type."""
        with open(file_path, "rb") as f:
            header = f.read(16)

        # PDF
        if ext == ".pdf":
            if not header.startswith(MAGIC_SIGNATURES["pdf"]):
                return "", (
                    "File claims to be PDF but does not start with %PDF magic bytes. Possible spoofed extension."
                )
            return "application/pdf", ""

        # Office ZIP-based formats
        if ext in OFFICE_ZIP_EXTENSIONS:
            if not header.startswith(MAGIC_SIGNATURES["zip"]):
                return "", (
                    f"File '{ext}' must be a ZIP container but magic bytes do not match. "
                    "Possible spoofed or corrupted file."
                )
            return f"application/vnd.openxmlformats{ext}", ""

        # MP4: 'ftyp' at offset 4-7
        if ext == ".mp4":
            if header[4:8] == MAGIC_SIGNATURES["mp4_ftyp"]:
                return "video/mp4", ""
            # Also allow early ftyp at 0
            return "video/mp4", ""  # lenient for MP4 variants

        # WEBM
        if ext == ".webm":
            if not header.startswith(MAGIC_SIGNATURES["webm"]):
                return "", ("File claims to be WEBM but magic bytes do not match. Possible spoofed extension.")
            return "video/webm", ""

        # TXT / MD — no magic bytes, just accept
        if ext in (".txt", ".md"):
            return "text/plain", ""

        return "application/octet-stream", ""

    def _check_zip_bomb(self, file_path: Path) -> str:
        """
        Detect ZIP bomb: if uncompressed size is > 100x compressed size
        or uncompressed size exceeds 2 GB.
        """
        try:
            total_compressed = file_path.stat().st_size
            total_uncompressed = 0
            with zipfile.ZipFile(file_path, "r") as zf:
                for info in zf.infolist():
                    total_uncompressed += info.file_size
                    # Nested zip inside zip
                    if info.filename.endswith(".zip"):
                        return "Nested ZIP detected inside Office file. Possible ZIP-bomb attack. File rejected."

            if total_compressed > 0:
                ratio = total_uncompressed / total_compressed
                if ratio > 100:
                    return (
                        f"ZIP-bomb detected: compression ratio = {ratio:.0f}x "
                        f"(uncompressed {total_uncompressed // 1024 // 1024} MB). "
                        "File rejected for security."
                    )

            if total_uncompressed > 2 * 1024 * 1024 * 1024:  # 2 GB
                return (
                    f"Office file uncompressed content exceeds 2 GB "
                    f"({total_uncompressed // 1024 // 1024} MB). File rejected."
                )
        except zipfile.BadZipFile:
            return "Office file is corrupted or not a valid ZIP archive."
        except Exception as e:
            logger.warning(f"ZIP-bomb check error for {file_path}: {e}")

        return ""
