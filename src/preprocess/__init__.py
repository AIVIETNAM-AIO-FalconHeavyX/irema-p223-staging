"""Preprocessing API with lazy imports for optional ingestion dependencies."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "TextCleaner": "src.preprocess.cleaner",
    "ImageProcessor": "src.preprocess.image_processor",
    "MarkdownGenerator": "src.preprocess.markdown_generator",
    "MarkdownNormalizer": "src.preprocess.markdown_normalizer",
    "MarkdownProcessingPipeline": "src.preprocess.markdown_pipeline",
    "MetadataGenerator": "src.preprocess.metadata_generator",
    "PIIRemover": "src.preprocess.pii_remover",
    "PIIReportGenerator": "src.preprocess.pii_report_generator",
    "PreprocessingPipeline": "src.preprocess.pipeline",
    "StructureAwareChunker": "src.preprocess.structure_aware_chunker",
    "StructureNormalizer": "src.preprocess.structure_normalizer",
}

__all__ = [
    "TextCleaner",
    "ImageProcessor",
    "MarkdownGenerator",
    "MetadataGenerator",
    "PIIRemover",
    "PIIReportGenerator",
    "PreprocessingPipeline",
    "MarkdownNormalizer",
    "StructureNormalizer",
    "StructureAwareChunker",
    "MarkdownProcessingPipeline",
]


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
