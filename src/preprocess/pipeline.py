from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from src.config import get_settings
from src.extract.base import BaseExtractor, ExtractedDocument
from src.extract.docx_extractor import DOCXExtractor
from src.extract.pdf_extractor import PDFExtractor
from src.extract.pptx_extractor import PPTXExtractor
from src.extract.video_extractor import VideoExtractor
from src.extract.xlsx_extractor import XLSXExtractor
from src.preprocess.cleaner import TextCleaner
from src.preprocess.image_processor import ImageProcessor
from src.preprocess.markdown_generator import MarkdownGenerator
from src.preprocess.metadata_generator import MetadataGenerator
from src.preprocess.pii_remover import PIIRemover
from src.preprocess.pii_report_generator import PIIReportGenerator

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    PLACEHOLDER_MARKER = "[Trang này chứa nội dung dạng hình ảnh/bảng biểu"

    def __init__(
        self,
        raw_dir: str | Path | None = None,
        processed_dir: str | Path | None = None,
    ):
        self.settings = get_settings()
        self.raw_dir = Path(raw_dir or self.settings.raw_data_dir)
        self.processed_dir = Path(processed_dir or self.settings.processed_data_dir)
        self.markdown_dir = self.processed_dir / "markdown"
        self.metadata_dir = self.processed_dir / "metadata"
        self.pii_reports_dir = self.processed_dir / "pii_reports"

        self.extractors: dict[str, BaseExtractor] = {
            ".pdf": PDFExtractor(),
            ".docx": DOCXExtractor(),
            ".pptx": PPTXExtractor(),
            ".xlsx": XLSXExtractor(),
            ".mp4": VideoExtractor(),
            ".webm": VideoExtractor(),
        }

        self.image_processor = ImageProcessor()
        self.pii_remover = PIIRemover()
        self.role_mapping = self.settings.role_mapping
        self.access_scope_mapping = self.settings.access_scope_mapping

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash for raw input file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"

    def detect_role_and_scope(self, file_path: Path) -> tuple[str, str, list[str]]:
        """Detect document role, category, and access_scope from folder path."""
        try:
            rel_path = file_path.relative_to(self.raw_dir)
            category = rel_path.parts[0]
        except (ValueError, IndexError):
            category = file_path.parent.name

        role = self.role_mapping.get(category, "general")
        access_scope = self.access_scope_mapping.get(category, ["accounting", "sales", "technician"])
        return role, category, access_scope

    def _cleanup_old_output(self, clean_stem: str, rel_parent: Path) -> None:
        """Remove any existing output files with the same stem to avoid stale data."""
        for subdir in [self.markdown_dir, self.metadata_dir, self.pii_reports_dir]:
            out_dir = subdir / rel_parent
            if not out_dir.exists():
                continue
            ext_map = {self.markdown_dir: ".md", self.metadata_dir: ".json", self.pii_reports_dir: ".json"}
            ext = ext_map.get(subdir, ".*")
            target = out_dir / f"{clean_stem}{ext}"
            if target.exists():
                target.unlink()
                logger.info(f"Cleaned old output: {target}")
        # Also clean root-level outputs (legacy location)
        for subdir_name, ext in [("markdown", ".md"), ("metadata", ".json"), ("pii_reports", ".json")]:
            root_file = self.processed_dir / subdir_name / f"{clean_stem}{ext}"
            if root_file.exists():
                root_file.unlink()
                logger.info(f"Cleaned old root-level output: {root_file}")

    def _try_ocr_for_placeholder_sections(self, doc: ExtractedDocument, file_path: Path) -> None:
        """
        Post-extraction pass: if any section contains the image placeholder,
        try OCR on that page's image to replace placeholder with real text.
        """
        if file_path.suffix.lower() != ".pdf":
            return

        try:
            import pymupdf as fitz
        except ImportError:
            try:
                import fitz
            except ImportError:
                return

        placeholder_sections = [
            (i, s) for i, s in enumerate(doc.sections) if s.content and self.PLACEHOLDER_MARKER in s.content
        ]

        if not placeholder_sections:
            return

        logger.info(
            "Found %d placeholder sections in %s, attempting OCR...",
            len(placeholder_sections),
            file_path.name,
        )

        pdf_doc = None
        try:
            pdf_doc = fitz.open(file_path)

            from src.preprocess.image_processor import ImageProcessor

            # Lazy-init ImageProcessor (reuse nếu đã có)
            if not hasattr(self, "_placeholder_image_processor"):
                self._placeholder_image_processor = ImageProcessor()

            for idx, section in placeholder_sections:
                page_num = section.page_num or section.slide_num
                if page_num is None:
                    continue
                page_idx = page_num - 1
                if page_idx < 0 or page_idx >= len(pdf_doc):
                    continue

                page = pdf_doc[page_idx]
                pix = page.get_pixmap(dpi=300, alpha=False)
                img_bytes = pix.tobytes("png")

                # Dùng EasyOCR (bbox-sorted) thay thế Gemini Vision
                ocr_text = self._placeholder_image_processor._run_ocr(img_bytes)

                if ocr_text and len(ocr_text.strip()) >= 20:
                    section.content = ocr_text.strip()
                    logger.info(
                        "Replaced placeholder on page/slide %d with EasyOCR text (%d chars)",
                        page_num,
                        len(ocr_text),
                    )
        except Exception as e:
            logger.warning("Post-extraction OCR failed for %s: %s", file_path.name, e)
        finally:
            if pdf_doc is not None:
                pdf_doc.close()

    def process_file(self, file_path: Path) -> tuple[Path, Path, Path] | None:
        """Process a single file through extraction, PII removal, and output generation."""
        ext = file_path.suffix.lower()
        if ext not in self.extractors:
            logger.info(f"Skipping unsupported file type: {file_path}")
            return None

        role, category, access_scope = self.detect_role_and_scope(file_path)
        logger.info(f"Processing {file_path.name} (Role: {role}, Category: {category})")

        extractor = self.extractors[ext]
        try:
            # 1. Extraction
            doc: ExtractedDocument = extractor.extract(file_path, role=role, category=category)
            doc.access_scope = access_scope
            doc.file_hash = self.compute_file_hash(file_path)

            # 1.5. Post-extraction: replace placeholder sections with OCR
            self._try_ocr_for_placeholder_sections(doc, file_path)

            # 2. Image Processing (OCR)
            for img in doc.images:
                self.image_processor.process_image(img)
                if img.ocr_text:
                    res = self.pii_remover.process(img.ocr_text)
                    img.ocr_text = res.cleaned_text

            # 3. Text PII Detection and Complete Removal across all sections & raw_text
            total_removed_entities: dict[str, int] = {}
            any_pii_detected = False

            for section in doc.sections:
                if section.content:
                    res = self.pii_remover.process(section.content)
                    section.content = res.cleaned_text
                    if res.detected:
                        any_pii_detected = True
                        for k, v in res.removed_counts.items():
                            total_removed_entities[k] = total_removed_entities.get(k, 0) + v

            if doc.raw_text:
                res = self.pii_remover.process(doc.raw_text)
                doc.raw_text = res.cleaned_text
                if res.detected:
                    any_pii_detected = True

            doc.pii_processed = True
            doc.pii_removed = True
            doc.pii_detected = any_pii_detected
            doc.removed_entities = total_removed_entities

            # 4. Output Generation (Markdown, Metadata JSON, PII Report JSON)
            markdown_content = MarkdownGenerator.generate(doc)
            metadata_content = MetadataGenerator.generate_json(doc)
            pii_report_content = PIIReportGenerator.generate_json(
                doc.document_id, doc.pii_detected, doc.removed_entities
            )

            # Prepare relative folder structure
            if file_path.is_relative_to(self.raw_dir):
                rel_parent = file_path.parent.relative_to(self.raw_dir)
            else:
                rel_parent = Path(category)

            clean_stem = TextCleaner.normalize_filename(file_path.stem)

            # Clean old outputs before writing new ones
            self._cleanup_old_output(clean_stem, rel_parent)

            out_md_dir = self.markdown_dir / rel_parent
            out_meta_dir = self.metadata_dir / rel_parent
            out_pii_dir = self.pii_reports_dir / rel_parent

            out_md_dir.mkdir(parents=True, exist_ok=True)
            out_meta_dir.mkdir(parents=True, exist_ok=True)
            out_pii_dir.mkdir(parents=True, exist_ok=True)

            out_md_path = out_md_dir / f"{clean_stem}.md"
            out_meta_path = out_meta_dir / f"{clean_stem}.json"
            out_pii_path = out_pii_dir / f"{clean_stem}.json"

            out_md_path.write_text(markdown_content, encoding="utf-8")
            out_meta_path.write_text(metadata_content, encoding="utf-8")
            out_pii_path.write_text(pii_report_content, encoding="utf-8")

            logger.info(f"Successfully processed: {out_md_path}")

            return out_md_path, out_meta_path, out_pii_path

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            return None

    def run_all(self) -> list[tuple[Path, Path, Path]]:
        """Recursively scan raw_dir and process all supported files."""
        processed_files = []
        if not self.raw_dir.exists():
            logger.warning(f"Raw directory does not exist: {self.raw_dir}")
            return processed_files

        for file_path in self.raw_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.extractors:
                res = self.process_file(file_path)
                if res:
                    processed_files.append(res)

        return processed_files
