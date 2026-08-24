import json

from src.preprocess.markdown_normalizer import MarkdownNormalizer
from src.preprocess.markdown_pipeline import MarkdownProcessingPipeline
from src.preprocess.structure_aware_chunker import StructureAwareChunker
from src.preprocess.structure_normalizer import StructureNormalizer


def test_markdown_normalizer_ocr_and_noise_removal():
    raw_md = (
        "--- \n"
        "title: Sample Doc\n"
        "---\n"
        "# Sample Doc\n\n"
        "., ~ ° = >>\n"
        "===...---\n"
        "NV VN © WSO) 4 ủ :\n\n"
        "### Image Caption\n"
        "Extracted image on Page 1: image1.png\n\n"
        "## Nội dung chính\n\n"
        "Nội dung V inFast chính sach tốt.\n"
    )
    cleaned = MarkdownNormalizer.normalize(raw_md)
    assert "., ~ ° = >>" not in cleaned
    assert "===...---" not in cleaned
    assert "### Image Caption" not in cleaned
    assert "VinFast" in cleaned
    assert "chính sách" in cleaned


def test_markdown_normalizer_heading_deduplication():
    raw_md = (
        "## 00:00\n\n## 00:00\n\nNội dung video phân đoạn 1.\n\n## 00:30\n\n## 00:30\n\nNội dung video phân đoạn 2.\n"
    )
    cleaned = MarkdownNormalizer.normalize(raw_md)
    assert cleaned.count("## 00:00") == 1
    assert cleaned.count("## 00:30") == 1


def test_structure_normalizer_table_and_list_atomic_blocks():
    md_text = (
        "# Title\n\n"
        "## Section 1\n\n"
        "| Hạng mục | Thời gian |\n"
        "|---|---|\n"
        "| Xe máy | 6 năm |\n"
        "| Pin LFP | 8 năm |\n\n"
        "- Item 1\n"
        "- Item 2\n"
        "- Item 3\n"
    )
    sections = StructureNormalizer.parse_structure(md_text)
    assert len(sections) == 1
    sec = sections[0]
    assert sec.title == "Section 1"
    assert len(sec.blocks) == 2

    # Table block assertion
    assert sec.blocks[0].block_type == "table"
    assert "| Xe máy | 6 năm |" in sec.blocks[0].content

    # List block assertion
    assert sec.blocks[1].block_type == "list"
    assert "- Item 1" in sec.blocks[1].content


def test_structure_aware_chunker_metadata():
    sections = StructureNormalizer.parse_structure(
        "# Tiêu chuẩn dịch vụ\n\n"
        "## Slide 5\n\n"
        "### 5. Thời gian bảo hành\n\n"
        "| Hạng mục | Bảo hành |\n"
        "|---|---|\n"
        "| Xe máy | 6 năm |\n"
    )
    chunks = StructureAwareChunker.chunk_sections(
        sections=sections,
        document_id="SALE003",
        title="3.1 Tiêu chuẩn dịch vụ XMĐ",
        role="sales",
        source="Sale/3.1_tieu_chuan.pdf",
    )
    assert len(chunks) >= 1
    c = chunks[0]
    assert c.chunk_id == "SALE003_chunk_001"
    assert "Document: 3.1 Tiêu chuẩn dịch vụ XMĐ" in c.content
    assert "Role: sales" in c.content
    assert "Slide: 5" in c.content
    assert c.metadata.role == "sales"
    assert c.metadata.slide == 5
    assert c.metadata.section == "Slide 5"
    assert c.metadata.subsection == "5. Thời gian bảo hành"


def test_markdown_processing_pipeline_e2e(tmp_path):
    input_base = tmp_path / "processed"
    input_md_dir = input_base / "markdown" / "Sale"
    input_md_dir.mkdir(parents=True, exist_ok=True)

    sample_md_file = input_md_dir / "test_doc.md"
    sample_md_file.write_text(
        "---\n"
        "document_id: TEST001\n"
        "title: Test Procedure\n"
        "role: sales\n"
        "source_path: Sale/test_doc.pdf\n"
        "---\n\n"
        "# Test Procedure\n\n"
        "## Section 1\n\n"
        "V inFast chính sach tốt.\n\n"
        "| Col1 | Col2 |\n"
        "|---|---|\n"
        "| Val1 | Val2 |\n",
        encoding="utf-8",
    )

    pipeline = MarkdownProcessingPipeline(input_dir=input_base, output_dir=input_base)
    results = pipeline.run_all()

    assert len(results) == 1
    out_md, out_chunks = results[0]

    assert out_md.exists()
    assert out_chunks.exists()

    # Verify existing input file was NOT mutated/overwritten
    assert "V inFast" in sample_md_file.read_text(encoding="utf-8")

    # Verify cleaned markdown output
    cleaned_md_text = out_md.read_text(encoding="utf-8")
    assert "VinFast" in cleaned_md_text
    assert "chính sách" in cleaned_md_text

    # Verify chunk JSON output
    chunks_data = json.loads(out_chunks.read_text(encoding="utf-8"))
    assert len(chunks_data) >= 1
    assert chunks_data[0]["chunk_id"] == "TEST001_test_doc_chunk_001"
    assert chunks_data[0]["metadata"]["role"] == "sales"
