from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ExtractedImage:
    filename: str
    image_bytes: bytes | None = None
    page_num: int | None = None
    slide_num: int | None = None
    sheet_name: str | None = None
    ocr_text: str | None = None
    caption: str | None = None


@dataclass
class DocumentSection:
    title: str = ""
    level: int = 1
    content: str = ""
    section_type: str = "text"  # 'text', 'table', 'slide', 'transcript', 'image'
    page_num: int | None = None
    slide_num: int | None = None
    sheet_name: str | None = None


@dataclass
class ExtractedDocument:
    document_id: str
    title: str
    source_file: str
    source_path: str
    document_type: str
    role: str
    category: str
    access_scope: list[str] = field(default_factory=list)
    file_hash: str = ""
    content_type: str = "document"
    language: str = "vi"
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    processed_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    pages: int = 1
    slides: int | None = None
    duration_seconds: float | None = None
    pii_processed: bool = True
    pii_removed: bool = True
    pii_detected: bool = False
    removed_entities: dict[str, int] = field(default_factory=dict)
    processing_status: str = "success"
    processing_errors: list[str] = field(default_factory=list)
    sections: list[DocumentSection] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    raw_text: str = ""


def generate_document_id(category: str, filename: str) -> str:
    """Generate deterministic document ID e.g., SALE001, KETOAN002, etc."""
    prefix = category.upper()[:4]
    # Extract existing numbers or hash filename
    numbers = re.findall(r"\d+", filename)
    if numbers:
        num_str = f"{int(numbers[0]):03d}"
    else:
        # Simple hash modulo 1000
        num_str = f"{abs(hash(filename)) % 1000:03d}"
    return f"{prefix}{num_str}"


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path, role: str, category: str) -> ExtractedDocument:
        """Extract content from a file into a structured ExtractedDocument."""
        pass
