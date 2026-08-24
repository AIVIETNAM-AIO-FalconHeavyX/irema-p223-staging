import unittest
from pathlib import Path
from unittest.mock import patch

from src.extract.base import ExtractedDocument
from src.extract.mineru_extractor import MinerUExtractor
from src.extract.pdf_extractor import PDFExtractor


class TestMinerUExtractor(unittest.TestCase):
    def test_mineru_extractor_initialization(self):
        extractor = MinerUExtractor()
        self.assertTrue(extractor.enabled)
        self.assertIn(extractor.device, ["auto", "cpu", "cuda"])

    def test_mineru_extractor_unavailable_graceful_fallback(self):
        dummy_pdf = Path("dummy_test.pdf")

        extractor = MinerUExtractor()
        with patch.object(MinerUExtractor, "is_available", return_value=False):
            result = extractor.extract(dummy_pdf, role="sales", category="Sale")
            self.assertIsNone(result)

    def test_mineru_build_sections(self):
        extractor = MinerUExtractor()
        sample_md = """# Tiêu chuẩn dịch vụ
## Slide 1
Nội dung slide 1

## Slide 2
| Tiêu chuẩn | Không tiêu chuẩn |
| --- | --- |
| Đầu tóc gọn gàng | Nhuộm màu sặc sỡ |
"""
        sections = extractor._build_sections_from_markdown(sample_md)
        self.assertGreaterEqual(len(sections), 2)
        self.assertTrue(any("Slide 1" in s.title for s in sections))
        self.assertTrue(any("Slide 2" in s.title for s in sections))

    def test_pdf_extractor_hybrid_fallback(self):
        dummy_pdf = Path("dummy_fallback.pdf")
        pdf_extractor = PDFExtractor()

        mock_doc = ExtractedDocument(
            document_id="SALE001",
            title="Dummy PDF",
            source_file="dummy.pdf",
            source_path="Sale/dummy.pdf",
            document_type="pdf",
            role="sales",
            category="Sale",
            raw_text="Tiêu chuẩn diện mạo và tác phong nhân viên bán hàng",
        )

        with patch.object(MinerUExtractor, "is_available", return_value=True):
            with patch.object(MinerUExtractor, "extract", return_value=mock_doc):
                res = pdf_extractor.extract(dummy_pdf, role="sales", category="Sale")
                self.assertIsNotNone(res)
                self.assertEqual(res.document_id, "SALE001")
                self.assertIn("Tiêu chuẩn diện mạo", res.raw_text)


if __name__ == "__main__":
    unittest.main()
