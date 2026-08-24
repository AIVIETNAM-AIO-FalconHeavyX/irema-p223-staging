from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from src.config import get_settings
from src.preprocess.cleaner import TextCleaner
from src.preprocess.markdown_normalizer import MarkdownNormalizer
from src.preprocess.structure_aware_chunker import StructureAwareChunker, TextChunk
from src.preprocess.structure_normalizer import StructureNormalizer

logger = logging.getLogger(__name__)


class MarkdownProcessingPipeline:
    """
    End-to-end pipeline for:
    1. Cleaning & normalizing raw/extracted Markdown.
    2. Structural normalization (Heading -> Section -> Subsection hierarchy).
    3. Structure-aware chunking (300-600 tokens, preserving tables/lists/code blocks).
    4. Metadata & Context Enrichment.

    Inputs: Raw/Processed Markdown files from `data/processed/markdown/` (kept untouched).
    Outputs:
    - Cleaned Markdown in `data/processed/cleaned_markdown/`
    - Chunk JSON payloads in `data/processed/chunks/`
    """

    def __init__(
        self,
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ):
        self.settings = get_settings()
        base_processed = Path(input_dir or self.settings.processed_data_dir)

        self.input_md_dir = base_processed / "markdown"
        self.output_cleaned_md_dir = base_processed / "cleaned_markdown"
        self.output_chunks_dir = base_processed / "chunks"

    def process_markdown_file(self, file_path: Path) -> tuple[Path, Path] | None:
        """Process a single markdown file end-to-end."""
        if not file_path.exists() or file_path.suffix.lower() != ".md":
            logger.warning(f"Invalid or non-markdown file: {file_path}")
            return None

        try:
            raw_content = file_path.read_text(encoding="utf-8")
            frontmatter, body_text = self._split_frontmatter(raw_content)

            doc_id = frontmatter.get("document_id", TextCleaner.normalize_filename(file_path.stem).upper())
            title = frontmatter.get("title", file_path.stem.replace("_", " ").title())
            role = frontmatter.get("role", "general")
            source = frontmatter.get("source_path", frontmatter.get("source_file", file_path.name))

            # 1. Clean & Normalize Markdown
            cleaned_body = MarkdownNormalizer.normalize(body_text)

            # 2. Normalize Structure & Parse Section Tree
            normalized_body = StructureNormalizer.normalize_headings(cleaned_body)
            sections = StructureNormalizer.parse_structure(normalized_body)
            clean_stem = TextCleaner.normalize_filename(file_path.stem)
            unique_doc_prefix = f"{doc_id}_{clean_stem}"

            # 3. Structure-aware Chunking with Context & Metadata
            chunks: list[TextChunk] = StructureAwareChunker.chunk_sections(
                sections=sections,
                document_id=unique_doc_prefix,
                title=title,
                role=role,
                source=source,
            )

            # 4. Prepare Output Paths (preserving subfolders like Sale/, KeToan/)
            try:
                rel_path = file_path.relative_to(self.input_md_dir)
            except ValueError:
                rel_path = Path(file_path.name)

            out_md_path = self.output_cleaned_md_dir / rel_path
            out_chunks_path = self.output_chunks_dir / rel_path.with_suffix(".json")

            out_md_path.parent.mkdir(parents=True, exist_ok=True)
            out_chunks_path.parent.mkdir(parents=True, exist_ok=True)

            # Assemble cleaned Markdown string with Frontmatter
            frontmatter_yaml = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
            final_md_text = f"---\n{frontmatter_yaml}\n---\n\n{normalized_body}"

            # Save outputs
            out_md_path.write_text(final_md_text, encoding="utf-8")
            chunks_json = json.dumps(
                [c.to_dict() for c in chunks],
                ensure_ascii=False,
                indent=2,
            )
            out_chunks_path.write_text(chunks_json, encoding="utf-8")

            logger.info(
                f"Successfully processed {file_path.name} -> Cleaned MD: {out_md_path.name}, Chunks: {len(chunks)}"
            )
            return out_md_path, out_chunks_path

        except Exception as e:
            logger.error(f"Error processing markdown file {file_path}: {e}", exc_info=True)
            return None

    def run_all(self) -> list[tuple[Path, Path]]:
        """Scan input_md_dir recursively and process all markdown files."""
        results = []
        if not self.input_md_dir.exists():
            logger.warning(f"Input markdown directory does not exist: {self.input_md_dir}")
            return results

        for md_path in self.input_md_dir.rglob("*.md"):
            res = self.process_markdown_file(md_path)
            if res:
                results.append(res)

        return results

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        """Separate YAML Frontmatter from body text."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return meta, body
                except yaml.YAMLError:
                    pass
        return {}, content.strip()
