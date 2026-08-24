import yaml

from src.extract.base import ExtractedDocument
from src.preprocess.cleaner import TextCleaner


class MarkdownGenerator:
    @staticmethod
    def generate(doc: ExtractedDocument) -> str:
        """Generate final Markdown string with YAML frontmatter header adhering to SPEC Section 17."""
        yaml_metadata = {
            "document_id": doc.document_id,
            "title": doc.title,
            "source_file": doc.source_file,
            "source_path": doc.source_path,
            "document_type": doc.document_type,
            "role": doc.role,
            "category": doc.category,
            "access_scope": doc.access_scope,
            "language": doc.language,
            "version": doc.version,
            "pages": doc.pages,
            "pii_processed": doc.pii_processed,
            "pii_removed": doc.pii_removed,
            "processed_at": doc.processed_at,
        }

        # Format YAML frontmatter
        yaml_str = yaml.dump(yaml_metadata, sort_keys=False, allow_unicode=True).strip()
        frontmatter = f"---\n{yaml_str}\n---"

        # Format Body
        body_parts = [f"# {doc.title}"]

        for section in doc.sections:
            if section.title and section.title != doc.title:
                heading_prefix = "#" * section.level
                body_parts.append(f"\n{heading_prefix} {section.title}\n")

            cleaned_content = TextCleaner.clean(section.content)
            if cleaned_content:
                body_parts.append(cleaned_content)

        full_markdown = f"{frontmatter}\n\n" + "\n\n".join(body_parts)
        return TextCleaner.clean(full_markdown)
