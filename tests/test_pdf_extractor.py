import pymupdf as fitz

from src.extract.pdf_extractor import PDFExtractor


def test_pdf_extractor_initialization():
    extractor = PDFExtractor()
    assert extractor.FULL_PAGE_IMAGE_RATIO == 0.90
    assert extractor.MIN_TEXT_QUALITY == 0.35


def test_pdf_extraction_fallback_to_pymupdf(tmp_path):
    # Create a minimal sample PDF
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World! Day la tai lieu kiem thu PDFExtractor.")
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    extracted_doc = extractor.extract(pdf_path, role="general", category="General_doc")

    assert extracted_doc is not None
    assert extracted_doc.document_type == "pdf"
    assert extracted_doc.pages == 1
    assert "Hello World" in extracted_doc.raw_text
