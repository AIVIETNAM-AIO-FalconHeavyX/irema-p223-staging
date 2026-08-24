from __future__ import annotations

import io
import logging

# Avoid PyTorch compilation issues on Windows CPU
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("PYTORCH_JIT", "0")
os.environ.setdefault("OMP_NUM_THREADS", "1")

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    import shutil

    import pytesseract  # type: ignore[import-untyped,import-not-found]

    # Tự động cấu hình tesseract_cmd trên Windows nếu chưa có trong PATH
    if pytesseract and not shutil.which("tesseract"):
        _candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.join(sys.prefix, "Library", "bin", "tesseract.exe"),
            os.path.join(sys.prefix, "Scripts", "tesseract.exe"),
            os.path.join(sys.prefix, "tesseract.exe"),
            r"E:\Anaconda\Library\bin\tesseract.exe",
            r"E:\Anaconda\envs\P-223\Library\bin\tesseract.exe",
        ]
        for _candidate in _candidates:
            if os.path.exists(_candidate):
                pytesseract.pytesseract.tesseract_cmd = _candidate
                _tess_dir = os.path.dirname(_candidate)
                if _tess_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = _tess_dir + os.pathsep + os.environ.get("PATH", "")
                _tessdata = os.path.join(_tess_dir, "tessdata")
                if not os.path.exists(_tessdata) and os.path.exists(os.path.join(sys.prefix, "share", "tessdata")):
                    _tessdata = os.path.join(sys.prefix, "share", "tessdata")
                if os.path.exists(_tessdata):
                    os.environ["TESSDATA_PREFIX"] = _tessdata
                logger.info("Auto-configured Tesseract at %s", _candidate)
                break
except ImportError:
    pytesseract = None
from PIL import Image  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.extract.base import (  # noqa: E402
    BaseExtractor,
    DocumentSection,
    ExtractedDocument,
    ExtractedImage,
    generate_document_id,
)
from src.extract.mineru_extractor import MinerUExtractor  # noqa: E402

logger = logging.getLogger(__name__)


class ChandraOCRHandler:
    """
    Lazy loader for Chandra OCR 2 Vision-Language Model.
    https://huggingface.co/datalab-to/chandra-ocr-2
    """

    MODEL_ID = "datalab-to/chandra-ocr-2"

    _processor = None
    _model = None
    _device = None
    _initialized = False

    @classmethod
    def get_model_and_processor(cls):
        if cls._initialized:
            return cls._processor, cls._model, cls._device

        cls._initialized = True
        try:
            import torch  # type: ignore[import-untyped,import-not-found]
            from transformers import (  # type: ignore[import-untyped,import-not-found]
                AutoModelForCausalLM,
                AutoProcessor,
            )

            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

            logger.info("Loading Chandra OCR 2 (%s) on %s...", cls.MODEL_ID, cls._device)

            cls._processor = AutoProcessor.from_pretrained(cls.MODEL_ID, trust_remote_code=True)
            cls._model = (
                AutoModelForCausalLM.from_pretrained(
                    cls.MODEL_ID,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype,
                )
                .to(cls._device)
                .eval()
            )
            logger.info("Chandra OCR 2 loaded successfully.")
        except Exception as e:
            logger.warning("Failed to load Chandra OCR 2: %s. Will fallback.", e)
            cls._processor = None
            cls._model = None
            cls._device = None

        return cls._processor, cls._model, cls._device

    @classmethod
    def process_image(cls, image: Image.Image) -> str:
        processor, model, device = cls.get_model_and_processor()
        if processor is None or model is None:
            raise RuntimeError("Chandra OCR 2 model is unavailable.")

        import torch

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": "OCR:"},
                ],
            }
        ]

        prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[prompt], images=[image], return_tensors="pt").to(device)

        with torch.inference_mode():
            generated_ids = model.generate(**inputs, max_new_tokens=1024)

        generated_text = processor.batch_decode(
            generated_ids[:, inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
        )[0]

        return generated_text.strip()


class PDFExtractor(BaseExtractor):
    """
    Hybrid 3-Tier PDF extraction strategy (offline, no external API):

    Tier 1: MinerU (Magic-PDF) — Best layout analysis, table reconstruction.
    Tier 2: Chandra OCR 2    — Vision-Language OCR for image-heavy pages.
    Tier 3: PyMuPDF + EasyOCR (bbox-sorted) + Tesseract — Final fallback.
    """

    FULL_PAGE_IMAGE_RATIO = 0.90
    MIN_NATIVE_TEXT_LENGTH = 20
    MIN_TEXT_QUALITY = 0.35

    def __init__(self):
        self.mineru_extractor = MinerUExtractor()

    # =========================================================
    # Public API
    # =========================================================

    def extract(
        self,
        file_path: Path,
        role: str,
        category: str,
    ) -> ExtractedDocument:

        logger.info("Starting PDF extraction for: %s", file_path.name)

        # -----------------------------------------------------
        # Tier 1: MinerU Pipeline (Layout + Table Reconstruction)
        # -----------------------------------------------------
        if MinerUExtractor.is_available():
            mineru_result = self.mineru_extractor.extract(file_path, role, category)
            if mineru_result is not None and self._is_satisfactory_result(mineru_result):
                logger.info("Tier 1 MinerU extraction succeeded for: %s", file_path.name)
                return mineru_result

        # -----------------------------------------------------
        # Tier 2: Chandra OCR 2
        # -----------------------------------------------------
        chandra_result = self._try_chandra_ocr_extract(file_path, role, category)
        if chandra_result is not None:
            logger.info("Tier 2 Chandra OCR extraction succeeded for: %s", file_path.name)
            return chandra_result

        # -----------------------------------------------------
        # Tier 3: PyMuPDF + Gemini Vision / EasyOCR / Tesseract fallback
        # -----------------------------------------------------
        logger.info("Falling back to PyMuPDF + Vision OCR for: %s", file_path.name)
        return self._pymupdf_extract(file_path, role, category)

    def _is_satisfactory_result(self, doc: ExtractedDocument) -> bool:
        """Evaluate if extracted document meets quality threshold."""
        if not doc.raw_text or len(doc.raw_text.strip()) < 20:
            return False
        return self._text_quality(doc.raw_text) >= self.MIN_TEXT_QUALITY

    # =========================================================
    # Preflight detection
    # =========================================================

    def _is_image_based_pdf(
        self,
        file_path: Path,
    ) -> bool:
        """
        Detect PDF where pages are primarily images.

        Strong signal:
            image covers >= 90% of page.

        Secondary signal:
            page contains image + almost no native text.
        """

        doc = None

        try:
            doc = fitz.open(file_path)

            if len(doc) == 0:
                return False

            for page_idx in range(len(doc)):
                page = doc[page_idx]

                if self._is_full_page_image(page):
                    logger.info(
                        "Page %d is a full-page image.",
                        page_idx + 1,
                    )
                    return True

                page_text = page.get_text("text").strip()
                image_list = page.get_images(full=True)

                if image_list and len(page_text) < 10:
                    logger.info(
                        "Page %d is likely image-based (text=%d chars, images=%d).",
                        page_idx + 1,
                        len(page_text),
                        len(image_list),
                    )
                    return True

        except Exception as e:
            logger.warning(
                "Failed to inspect PDF image structure %s: %s",
                file_path.name,
                e,
            )

        finally:
            if doc is not None:
                doc.close()

        return False

    def _is_full_page_image(
        self,
        page: fitz.Page,
    ) -> bool:
        """
        Detect an image covering most of the page.
        """

        page_area = page.rect.width * page.rect.height

        if page_area <= 0:
            return False

        image_list = page.get_images(full=True)

        if not image_list:
            return False

        for image_info in image_list:
            xref = image_info[0]

            try:
                rects = page.get_image_rects(xref)

                for rect in rects:
                    image_area = rect.width * rect.height

                    ratio = image_area / page_area

                    if ratio >= self.FULL_PAGE_IMAGE_RATIO:
                        return True

            except Exception as e:
                logger.debug(
                    "Could not inspect image xref=%s on page=%d: %s",
                    xref,
                    page.number + 1,
                    e,
                )

        return False

    # =========================================================
    # Chandra OCR 2 Extraction
    # =========================================================

    def _try_chandra_ocr_extract(
        self,
        file_path: Path,
        role: str,
        category: str,
    ) -> ExtractedDocument | None:
        settings = get_settings()
        if not getattr(settings, "chandra_enabled", False):
            return None

        doc = None
        try:
            logger.info(
                "Running Chandra OCR 2 extraction for: %s",
                file_path.name,
            )

            doc = fitz.open(file_path)
            total_pages = len(doc)

            if total_pages == 0:
                return None

            sections: list[DocumentSection] = []
            images: list[ExtractedImage] = []
            raw_pages: list[str] = []

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]

                pix = page.get_pixmap(dpi=300, alpha=False)
                img_bytes = pix.tobytes("png")
                page_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

                page_text = ChandraOCRHandler.process_image(page_image)
                raw_pages.append(page_text)

                if page_text:
                    sections.append(
                        DocumentSection(
                            title=f"Page {page_num}",
                            level=2,
                            content=page_text,
                            section_type="text",
                            page_num=page_num,
                        )
                    )

                self._extract_images_from_page(
                    doc=doc,
                    page=page,
                    page_num=page_num,
                    file_path=file_path,
                    output=images,
                )

            full_text = "\n\n".join(raw_pages).strip()

            if len(full_text) < 10:
                logger.warning(
                    "Chandra OCR 2 returned very little text for %s",
                    file_path.name,
                )
                return None

            quality = self._text_quality(full_text)

            if quality < self.MIN_TEXT_QUALITY:
                logger.warning(
                    "Chandra OCR 2 output has low text quality (%.2f): %s",
                    quality,
                    file_path.name,
                )
                return None

            title = self._make_title(file_path)
            doc_id = generate_document_id(
                category,
                file_path.name,
            )

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
                raw_text=full_text,
            )

        except Exception as e:
            logger.warning(
                "Chandra OCR 2 extraction failed for %s: %s",
                file_path.name,
                e,
            )
            return None

        finally:
            if doc is not None:
                doc.close()

    # =========================================================
    # PyMuPDF extraction
    # =========================================================

    def _pymupdf_extract(
        self,
        file_path: Path,
        role: str,
        category: str,
    ) -> ExtractedDocument:

        doc = fitz.open(file_path)

        total_pages = len(doc)

        sections: list[DocumentSection] = []
        images: list[ExtractedImage] = []
        raw_pages: list[str] = []

        is_presentation = self._check_is_presentation(doc)

        try:
            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]

                # -------------------------------------------------
                # 1. Native text (with table structure preservation)
                # -------------------------------------------------

                native_text = self._extract_page_text_with_tables(page).strip()

                # -------------------------------------------------
                # 2. Detect image page
                # -------------------------------------------------

                full_page_image = self._is_full_page_image(page)

                # -------------------------------------------------
                # 3. Decide OCR
                # -------------------------------------------------

                if self._needs_ocr(
                    native_text,
                    full_page_image,
                    page,
                ):
                    logger.info(
                        "OCR required for page %d: full_page_image=%s, chars=%d",
                        page_num,
                        full_page_image,
                        len(native_text),
                    )

                    ocr_text = self._ocr_page(page)

                    if self._valid_ocr(
                        ocr_text,
                        native_text,
                        full_page_image,
                    ):
                        page_text = ocr_text
                    else:
                        page_text = native_text

                else:
                    page_text = native_text

                page_text = page_text.strip()

                raw_pages.append(page_text)

                # -------------------------------------------------
                # 4. Extract embedded images
                # -------------------------------------------------

                self._extract_images_from_page(
                    doc=doc,
                    page=page,
                    page_num=page_num,
                    file_path=file_path,
                    output=images,
                )

                # -------------------------------------------------
                # 5. Build section (ALWAYS — never skip a page)
                # -------------------------------------------------

                # If page has no text but has images, create an
                # image-reference placeholder so slide numbering
                # stays continuous and RAG knows content exists.
                if not page_text:
                    has_images = bool(page.get_images(full=True))
                    if has_images:
                        page_text = (
                            "[Trang này chứa nội dung dạng hình ảnh/bảng biểu. "
                            "Nội dung chưa được trích xuất tự động — "
                            "cần xử lý thủ công hoặc cải thiện tài liệu gốc.]"
                        )
                        logger.warning(
                            "Page %d: no text extracted (image-only). Added placeholder.",
                            page_num,
                        )
                    else:
                        page_text = "[Trang trống]"

                section = self._build_section(
                    page_text=page_text,
                    page_num=page_num,
                    is_presentation=is_presentation,
                )

                sections.append(section)

        finally:
            doc.close()

        title = self._make_title(file_path)

        return ExtractedDocument(
            document_id=generate_document_id(
                category,
                file_path.name,
            ),
            title=title,
            source_file=file_path.name,
            source_path=(f"{category}/{file_path.name}"),
            document_type="pdf",
            role=role,
            category=category,
            pages=total_pages,
            sections=sections,
            images=images,
            raw_text="\n\n".join(raw_pages),
        )

    def _extract_page_text_with_tables(self, page: fitz.Page) -> str:
        """Trích xuất văn bản trên trang kết hợp phát hiện và bảo toàn bảng biểu Markdown chuẩn xác."""
        try:
            tabs = page.find_tables()
            if not tabs or len(tabs.tables) == 0:
                return page.get_text("text").strip()

            table_markdowns: list[str] = []
            table_rects: list[fitz.Rect] = []

            for tab in tabs.tables:
                try:
                    md = tab.to_markdown(clean=True)
                    if md and md.strip():
                        table_markdowns.append(md.strip())
                        table_rects.append(fitz.Rect(tab.bbox))
                except Exception:
                    pass

            if not table_markdowns:
                return page.get_text("text").strip()

            # Lấy blocks văn bản ngoài bảng và sắp xếp theo trục y0
            blocks = page.get_text("blocks")
            combined_elements: list[tuple[float, str, str]] = []

            for b in blocks:
                b_rect = fitz.Rect(b[:4])
                b_text = b[4].strip()
                if not b_text:
                    continue
                # Kiểm tra block có nằm trong vùng bảng không
                in_table = any(
                    b_rect.intersects(t_rect)
                    and (b_rect in t_rect or (b_rect & t_rect).get_area() > 0.4 * b_rect.get_area())
                    for t_rect in table_rects
                )
                if not in_table:
                    combined_elements.append((float(b[1]), "text", b_text))

            for t_idx, tab in enumerate(tabs.tables):
                if t_idx < len(table_markdowns):
                    combined_elements.append((float(tab.bbox[1]), "table", table_markdowns[t_idx]))

            combined_elements.sort(key=lambda x: x[0])
            result_text = "\n\n".join(elem[2] for elem in combined_elements)
            return result_text.strip()
        except Exception as e:
            logger.debug(f"Table extraction fallback to standard text: {e}")
            return page.get_text("text").strip()

    # =========================================================
    # OCR
    # =========================================================

    def _needs_ocr(
        self,
        native_text: str,
        full_page_image: bool,
        page: fitz.Page | None = None,
    ) -> bool:

        if full_page_image:
            return True

        if not native_text:
            return True

        if len(native_text) < self.MIN_NATIVE_TEXT_LENGTH:
            return True

        quality = self._text_quality(native_text)

        if quality < self.MIN_TEXT_QUALITY:
            return True

        # If page has images but very little text, likely image-heavy slide
        if page is not None:
            image_list = page.get_images(full=True)
            if len(image_list) >= 2 and len(native_text) < 100:
                return True

        return False

    def _ocr_page(
        self,
        page,
    ) -> str:
        """
        OCR một trang PDF khi không có text native đủ chất lượng.

        Tier 1: EasyOCR (bbox-sorted) — Tốt nhất cho tiếng Việt có dấu.
        Tier 2: Tesseract OCR          — Offline fallback, cần cài binary.
        """
        # Render trang → ảnh 300 DPI
        try:
            pix = page.get_pixmap(dpi=300, alpha=False)
            image_bytes = pix.tobytes("png")
            page_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            logger.warning(
                "Failed to render page %d to image: %s",
                page.number + 1,
                e,
            )
            return ""

        # --- Tier 1: EasyOCR với bbox sorting ---
        try:
            from src.preprocess.image_processor import ImageProcessor

            if not hasattr(self, "_image_processor"):
                self._image_processor = ImageProcessor()
            easy_text = self._image_processor._run_ocr(image_bytes)
            if easy_text and self._text_quality(easy_text) >= self.MIN_TEXT_QUALITY:
                logger.info(
                    "Page %d: using EasyOCR bbox-sorted (%d chars).",
                    page.number + 1,
                    len(easy_text),
                )
                return easy_text
        except Exception as e:
            logger.warning(
                "EasyOCR failed on page %d: %s",
                page.number + 1,
                e,
            )

        # --- Tier 2: Tesseract OCR ---
        if pytesseract is not None:
            try:
                tesseract_text = pytesseract.image_to_string(
                    page_image,
                    lang="vie+eng",
                    config="--psm 6",
                ).strip()
                if tesseract_text:
                    logger.info(
                        "Page %d: using Tesseract OCR (%d chars).",
                        page.number + 1,
                        len(tesseract_text),
                    )
                return tesseract_text
            except Exception as e:
                logger.warning(
                    "Tesseract OCR failed on page %d: %s",
                    page.number + 1,
                    e,
                )

        return ""

    def _text_density(self, page: fitz.Page) -> float:
        """
        Compute alphanumeric character density for a page's native text.
        Used to decide whether to send the page to Gemini Vision for quality improvement
        even when PyMuPDF returns some text (e.g. PDF slides with broken reading order).

        Returns: ratio of alphanumeric chars in [0.0, 1.0].
        """
        text = page.get_text("text").strip()
        return self._text_quality(text)

    def _valid_ocr(
        self,
        ocr_text: str,
        native_text: str,
        full_page_image: bool,
    ) -> bool:

        if not ocr_text:
            return False

        quality = self._text_quality(ocr_text)

        if quality < self.MIN_TEXT_QUALITY:
            return False

        alnum_count = sum(c.isalnum() for c in ocr_text)

        if alnum_count < 10:
            return False

        # For screenshot/scanned pages, valid OCR
        # should replace missing native text.
        if full_page_image:
            return True

        native_quality = self._text_quality(native_text)

        # Good native text should not be replaced
        # by OCR unnecessarily.
        if native_quality >= 0.50:
            return False

        return True

    def _text_quality(
        self,
        text: str,
    ) -> float:

        text = text.strip()

        if not text:
            return 0.0

        alnum = sum(c.isalnum() for c in text)

        return alnum / len(text)

    # =========================================================
    # Image extraction
    # =========================================================

    def _extract_images_from_page(
        self,
        doc: fitz.Document,
        page: fitz.Page,
        page_num: int,
        file_path: Path,
        output: list[ExtractedImage],
    ):

        image_list = page.get_images(full=True)

        for index, image_info in enumerate(
            image_list,
            start=1,
        ):
            xref = image_info[0]

            try:
                base_image = doc.extract_image(xref)

                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                filename = f"{file_path.stem}_p{page_num}_img{index}.{image_ext}"

                output.append(
                    ExtractedImage(
                        filename=filename,
                        image_bytes=image_bytes,
                        page_num=page_num,
                    )
                )

            except Exception as e:
                logger.warning(
                    "Failed to extract image from page %d: %s",
                    page_num,
                    e,
                )

    # =========================================================
    # Section construction
    # =========================================================

    def _build_section(
        self,
        page_text: str,
        page_num: int,
        is_presentation: bool,
    ) -> DocumentSection:

        if not is_presentation:
            return DocumentSection(
                title=f"Page {page_num}",
                level=2,
                content=page_text,
                section_type="text",
                page_num=page_num,
            )

        lines = [line.strip() for line in page_text.splitlines() if line.strip()]

        if not lines:
            title = f"Slide {page_num}"
            content = ""
        else:
            title = lines[0]
            content = "\n".join(lines[1:])

        parts = [f"### Title\n\n{title}"]

        if content:
            parts.append(f"### Content\n\n{content}")

        return DocumentSection(
            title=f"Slide {page_num}",
            level=2,
            content="\n\n".join(parts),
            section_type="slide",
            page_num=page_num,
        )

    # =========================================================
    # Presentation detection
    # =========================================================

    def _check_is_presentation(
        self,
        doc: fitz.Document,
    ) -> bool:

        if len(doc) == 0:
            return False

        sample_size = min(
            len(doc),
            5,
        )

        landscape_count = 0

        for i in range(sample_size):
            rect = doc[i].rect

            if rect.width > rect.height:
                landscape_count += 1

        return landscape_count > (sample_size / 2)

    # =========================================================
    # Helpers
    # =========================================================

    def _make_title(
        self,
        file_path: Path,
    ) -> str:

        return file_path.stem.replace("_", " ").replace("-", " ")
