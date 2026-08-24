import json

from src.extract.base import DocumentSection, ExtractedDocument, generate_document_id
from src.preprocess.cleaner import TextCleaner
from src.preprocess.markdown_generator import MarkdownGenerator
from src.preprocess.metadata_generator import MetadataGenerator
from src.preprocess.pii_remover import PIIRemover
from src.preprocess.pii_report_generator import PIIReportGenerator
from src.preprocess.pipeline import PreprocessingPipeline


def test_role_and_scope_detection(tmp_path):
    raw_dir = tmp_path / "raw"
    pipeline = PreprocessingPipeline(raw_dir=raw_dir)

    test_cases = [
        (raw_dir / "KeToan" / "sample.pdf", "accounting", "KeToan", ["accounting"]),
        (raw_dir / "Sale" / "sample.pdf", "sales", "Sale", ["sales"]),
        (raw_dir / "KTV" / "sample.pdf", "technician", "KTV", ["technician"]),
        (
            raw_dir / "General_doc" / "sample.pdf",
            "general",
            "General_doc",
            ["accounting", "sales", "technician", "owner", "general"],
        ),
    ]

    for file_path, expected_role, expected_category, expected_scope in test_cases:
        role, category, scope = pipeline.detect_role_and_scope(file_path)
        assert role == expected_role
        assert category == expected_category
        assert scope == expected_scope


def test_pii_remover_vietnamese():
    remover = PIIRemover()
    raw_text = "Khách hàng Nguyễn Văn A\nSĐT: 0912345678\nEmail: nguyenvana@gmail.com\nCCCD: 012345678901\n"
    result = remover.process(raw_text)

    assert result.detected is True
    assert "0912345678" not in result.cleaned_text
    assert "nguyenvana@gmail.com" not in result.cleaned_text
    assert "012345678901" not in result.cleaned_text
    assert "PHONE_NUMBER" in result.removed_counts
    assert "EMAIL_ADDRESS" in result.removed_counts
    assert "ID_NUMBER" in result.removed_counts


def test_pii_report_generator():
    report_json = PIIReportGenerator.generate_json(
        document_id="SALE001",
        pii_detected=True,
        removed_entities={"PERSON": 1, "PHONE_NUMBER": 2, "EMAIL_ADDRESS": 1},
    )
    data = json.loads(report_json)
    assert data["document_id"] == "SALE001"
    assert data["pii_detected"] is True
    assert data["removed_entities"]["PHONE_NUMBER"] == 2
    # Ensure raw PII is never present in report
    assert "0912345678" not in report_json


def test_text_cleaner():
    dirty_text = "  Header Line  \r\n\r\n\r\n* Item 1\r\n* Item 2  \n\n\n\nEnd.  "
    cleaned = TextCleaner.clean(dirty_text)
    assert "* Item 1" not in cleaned
    assert "- Item 1" in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_text_cleaner_image_caption_removal():
    sample_text = (
        "Some content before\n\n"
        "### Image Caption\n\n"
        "Extracted image on Page 16: 3.1 Tiêu chuẩn dịch vụ XMĐ_251121_p16_img1.png\n"
        "Extracted image on Page 16: 3.1 Tiêu chuẩn dịch vụ XMĐ_251121_p16_img2.jpeg\n\n"
        "## Slide 17\n"
    )
    cleaned = TextCleaner.clean(sample_text)
    assert "### Image Caption" not in cleaned
    assert "Extracted image on Page" not in cleaned
    assert "Some content before" in cleaned
    assert "## Slide 17" in cleaned


def test_text_cleaner_ocr_garbage_removal():
    dirty_text = (
        "CHÀO MỪNG ANH CHỊ GIA NHẬP\n"
        ", a £ ~. “ -\n"
        "_ + = z <<.“ .\n"
        "Z a R\n"
        "==. sac: — \\ \\ - —__.\n"
        "ĐẠI GIA ĐÌNH VINGROUP!\n"
    )
    cleaned = TextCleaner.clean(dirty_text)
    assert "CHÀO MỪNG ANH CHỊ GIA NHẬP" in cleaned
    assert "ĐẠI GIA ĐÌNH VINGROUP!" in cleaned
    assert ", a £ ~." not in cleaned
    assert "_ + = z" not in cleaned
    assert "Z a R" not in cleaned


def test_filename_normalization():
    assert TextCleaner.normalize_filename("1. Đơn đặt hàng PO XMĐ") == "1_don_dat_hang_po_xmd"
    assert TextCleaner.normalize_filename("Báo Cáo Tài Chính - 2026") == "bao_cao_tai_chinh_2026"
    assert TextCleaner.normalize_filename("Sales Process - Final") == "sales_process_final"
    assert TextCleaner.normalize_filename("HuongDanKyThuat") == "huongdankythuat"


def test_document_id_generation():
    doc_id_sale = generate_document_id("Sale", "Sales_Process.pdf")
    doc_id_ketoan = generate_document_id("KeToan", "BaoCao.docx")
    assert doc_id_sale.startswith("SALE")
    assert doc_id_ketoan.startswith("KETO")


def test_markdown_and_metadata_generator():
    doc = ExtractedDocument(
        document_id="SALE001",
        title="Sales Process",
        source_file="Sales_Process.pdf",
        source_path="Sale/Sales_Process.pdf",
        document_type="pdf",
        role="sales",
        category="Sale",
        access_scope=["sales"],
        file_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        pages=5,
        pii_processed=True,
        pii_removed=True,
        pii_detected=True,
        sections=[
            DocumentSection(
                title="Overview",
                level=2,
                content="This is the overview section.",
            )
        ],
    )

    md_output = MarkdownGenerator.generate(doc)
    assert md_output.startswith("---")
    assert "document_id: SALE001" in md_output
    assert "role: sales" in md_output
    assert "access_scope" in md_output
    assert "# Sales Process" in md_output
    assert "## Overview" in md_output

    meta_json = MetadataGenerator.generate_json(doc)
    data = json.loads(meta_json)
    assert data["document_id"] == "SALE001"
    assert data["role"] == "sales"
    assert data["access_scope"] == ["sales"]
    assert data["file_hash"].startswith("sha256:")
    assert data["pii_processed"] is True
    assert data["pii_removed"] is True
    assert data["pii_detected"] is True
    assert data["processing_status"] == "success"
