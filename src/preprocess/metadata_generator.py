import json

from src.extract.base import ExtractedDocument


class MetadataGenerator:
    @staticmethod
    def generate_dict(doc: ExtractedDocument) -> dict:
        """Generate JSON metadata dict for the processed document adhering to SPEC Section 18."""
        return {
            "document_id": doc.document_id,
            "title": doc.title,
            "source_file": doc.source_file,
            "source_path": doc.source_path,
            "file_hash": doc.file_hash,
            "document_type": doc.document_type,
            "content_type": doc.content_type,
            "role": doc.role,
            "category": doc.category,
            "access_scope": doc.access_scope,
            "language": doc.language,
            "version": doc.version,
            "pages": doc.pages,
            "slides": doc.slides,
            "duration_seconds": doc.duration_seconds,
            "pii_processed": doc.pii_processed,
            "pii_removed": doc.pii_removed,
            "pii_detected": doc.pii_detected,
            "processing_status": doc.processing_status,
            "processing_errors": doc.processing_errors,
            "processed_at": doc.processed_at,
        }

    @staticmethod
    def generate_json(doc: ExtractedDocument, indent: int = 4) -> str:
        """Generate formatted JSON string for the processed document metadata."""
        meta_dict = MetadataGenerator.generate_dict(doc)
        return json.dumps(meta_dict, ensure_ascii=False, indent=indent)
