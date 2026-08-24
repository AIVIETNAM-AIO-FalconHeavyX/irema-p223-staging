from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from src.config import get_settings
from src.extract.base import (
    BaseExtractor,
    DocumentSection,
    ExtractedDocument,
    ExtractedImage,
    generate_document_id,
)

logger = logging.getLogger(__name__)


class MinerUExtractor(BaseExtractor):
    """
    MinerU (Magic-PDF) High-Precision Document Extractor.
    Extracts complex PDFs (tables, multi-column layouts, formulas, images) to clean Markdown.
    Supports both Python API (mineru/magic_pdf) and CLI execution.
    """

    def __init__(self):
        self.settings = get_settings()
        self.enabled = getattr(self.settings, "mineru_enabled", True)
        self.device = getattr(self.settings, "mineru_device", "auto")

    @classmethod
    def is_available(cls) -> bool:
        """Check if mineru or magic_pdf package / CLI is available in the environment."""
        # 1. Check python import
        try:
            import mineru  # noqa: F401

            return True
        except ImportError:
            pass

        try:
            import magic_pdf  # noqa: F401

            return True
        except ImportError:
            pass

        # 2. Check CLI command in PATH
        if shutil.which("mineru") or shutil.which("magic-pdf"):
            return True

        return False

    def extract(self, file_path: Path, role: str, category: str) -> ExtractedDocument | None:
        """
        Extract PDF content using MinerU pipeline.
        Returns ExtractedDocument on success or None on failure.
        """
        if not self.enabled:
            logger.info("MinerU extraction is disabled in configuration.")
            return None

        if not self.is_available():
            logger.info("MinerU is not installed or unavailable in this environment.")
            return None

        logger.info("Starting MinerU extraction for: %s", file_path.name)

        temp_dir = tempfile.mkdtemp(prefix="mineru_extract_")
        try:
            # 1. Try Python API first
            extracted = self._extract_via_python_api(file_path, Path(temp_dir), role, category)
            if extracted:
                return extracted

            # 2. Try CLI execution
            extracted = self._extract_via_cli(file_path, Path(temp_dir), role, category)
            if extracted:
                return extracted

            return None

        except Exception as e:
            logger.warning("MinerU extraction failed for %s: %s", file_path.name, e)
            return None

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_via_python_api(
        self, file_path: Path, output_dir: Path, role: str, category: str
    ) -> ExtractedDocument | None:
        """Extract using modern MinerU or magic_pdf Python API."""
        try:
            # Attempt modern mineru package
            import importlib

            if importlib.util.find_spec("mineru"):
                try:
                    from mineru.pipeline import MinerUPipeline

                    pipeline = MinerUPipeline(device=self.device if self.device != "auto" else None)
                    pipeline.run(str(file_path), output_dir=str(output_dir))
                    return self._parse_mineru_output(output_dir, file_path, role, category)
                except Exception as e:
                    logger.debug("MinerUPipeline Python API failed: %s", e)

            # Attempt legacy magic_pdf package
            if importlib.util.find_spec("magic_pdf"):
                try:
                    from magic_pdf.pipe.UNIPipe import UNIPipe
                    from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter

                    image_dir = output_dir / "images"
                    image_dir.mkdir(parents=True, exist_ok=True)
                    image_writer = DiskReaderWriter(str(image_dir))

                    with open(file_path, "rb") as f:
                        pdf_bytes = f.read()

                    pipe = UNIPipe(pdf_bytes=pdf_bytes, model_list=[], image_writer=image_writer)
                    pipe.pipe_classify()
                    pipe.pipe_analyze()
                    pipe.pipe_parse()
                    md_content = pipe.pipe_mk_markdown()

                    md_path = output_dir / f"{file_path.stem}.md"
                    md_path.write_text(md_content, encoding="utf-8")
                    return self._parse_mineru_output(output_dir, file_path, role, category)
                except Exception as e:
                    logger.debug("magic_pdf UNIPipe Python API failed: %s", e)

        except Exception as e:
            logger.debug("Python API extraction encountered error: %s", e)

        return None

    def _extract_via_cli(self, file_path: Path, output_dir: Path, role: str, category: str) -> ExtractedDocument | None:
        """Run mineru / magic-pdf CLI command."""
        cli_cmd = shutil.which("mineru") or shutil.which("magic-pdf")
        if not cli_cmd:
            return None

        cmd = [cli_cmd, "-p", str(file_path), "-o", str(output_dir)]
        if self.device == "cpu":
            cmd.extend(["-m", "pipeline"])

        logger.info("Executing MinerU CLI: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if proc.returncode != 0:
            logger.warning("MinerU CLI exited with code %d: %s", proc.returncode, proc.stderr)
            return None

        return self._parse_mineru_output(output_dir, file_path, role, category)

    def _parse_mineru_output(
        self, output_dir: Path, file_path: Path, role: str, category: str
    ) -> ExtractedDocument | None:
        """Find and parse markdown and assets generated by MinerU."""
        # MinerU usually outputs <output_dir>/<stem>/auto/<stem>.md or <output_dir>/<stem>.md
        md_files = list(output_dir.rglob("*.md"))
        if not md_files:
            logger.warning("No markdown file produced by MinerU in %s", output_dir)
            return None

        # Pick the main markdown file
        main_md_file = max(md_files, key=lambda f: f.stat().st_size)
        content = main_md_file.read_text(encoding="utf-8").strip()

        if len(content) < 20:
            logger.warning("MinerU markdown output is too short (%d chars).", len(content))
            return None

        # Parse sections (by page / slide or markdown headings)
        sections = self._build_sections_from_markdown(content)
        total_pages = max(len(sections), 1)

        # Collect images
        images: list[ExtractedImage] = []
        for img_path in output_dir.rglob("*.*"):
            if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                try:
                    images.append(
                        ExtractedImage(
                            filename=img_path.name,
                            image_bytes=img_path.read_bytes(),
                            page_num=None,
                        )
                    )
                except Exception:
                    pass

        title = file_path.stem.replace("_", " ").replace("-", " ")
        doc_id = generate_document_id(category, file_path.name)

        return ExtractedDocument(
            document_id=doc_id,
            title=title,
            source_file=file_path.name,
            source_path=f"{category}/{file_path.name}",
            document_type="pdf",
            role=role,
            category=category,
            pages=total_pages,
            sections=sections,
            images=images,
            raw_text=content,
        )

    def _build_sections_from_markdown(self, markdown_text: str) -> list[DocumentSection]:
        """Split markdown content into logical sections or slides."""
        # Check if content has slide/page separators like "## Slide X" or "---" or "## "
        lines = markdown_text.splitlines()
        sections: list[DocumentSection] = []
        current_title = "Document Content"
        current_lines: list[str] = []
        page_counter = 1

        for line in lines:
            if line.startswith("# ") or line.startswith("## ") or line.startswith("---"):
                if current_lines:
                    sec_text = "\n".join(current_lines).strip()
                    if sec_text:
                        sections.append(
                            DocumentSection(
                                title=current_title,
                                level=2,
                                content=sec_text,
                                section_type="text",
                                page_num=page_counter,
                            )
                        )
                        page_counter += 1
                    current_lines = []
                if line.startswith("#"):
                    current_title = line.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            sec_text = "\n".join(current_lines).strip()
            if sec_text:
                sections.append(
                    DocumentSection(
                        title=current_title,
                        level=2,
                        content=sec_text,
                        section_type="text",
                        page_num=page_counter,
                    )
                )

        if not sections:
            sections.append(
                DocumentSection(
                    title="Main Content",
                    level=1,
                    content=markdown_text,
                    section_type="text",
                    page_num=1,
                )
            )

        return sections
