from __future__ import annotations

import io
import logging
import math
import re
from statistics import median

from src.config import get_settings
from src.extract.base import ExtractedImage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Quick post-OCR brand-name fixes (applied directly on raw OCR
# text before Tier 4 in the normalizer runs).
# Only the most critical patterns go here — the full dictionary
# lives in MarkdownNormalizer.BRAND_CORRECTIONS.
# ---------------------------------------------------------------
_POST_OCR_BRAND_FIXES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"VINFA\$T", re.IGNORECASE), "VINFAST"),
    (re.compile(r"V\s*I\s*N\s*F\s*A\s*\$\s*T", re.IGNORECASE), "VINFAST"),
    (re.compile(r"VINFA\s*\$\s*T", re.IGNORECASE), "VINFAST"),
]


class ImageProcessor:
    """
    Process images extracted from documents.

    1. Perform local OCR (EasyOCR) if ExtractedImage.ocr_text is empty.
    2. Filter OCR bounding-boxes by:
       - Tier 1: EasyOCR confidence score (drops blurry / uncertain text).
       - Tier 2: Bounding-box height relative to image height (drops tiny
         background watermarks and event-banner captions).
       - Tier 2.5: Text orientation filter (drops text whose rotation angle
         deviates significantly from the dominant direction, e.g. background
         banners reading at 30° while slide content is horizontal).
    3. Sort surviving results top-to-bottom, left-to-right using adaptive
       bucket size based on median bbox height.
    4. Apply quick post-OCR brand-name corrections.
    5. Build deterministic image caption from metadata and OCR text.
    """

    def __init__(self):

        self.settings = get_settings()

        self._ocr_reader = None
        self._ocr_initialized = False

    # =========================================================
    # Public API
    # =========================================================

    def process_image(
        self,
        image: ExtractedImage,
    ) -> ExtractedImage:

        if not image.image_bytes:
            logger.debug(
                "No image bytes: %s",
                image.filename,
            )
            return image

        # -----------------------------------------------------
        # OCR only (Image captioning disabled)
        # -----------------------------------------------------

        if not image.ocr_text:
            image.ocr_text = self._run_ocr(image.image_bytes)

        image.caption = ""

        return image

    # =========================================================
    # EasyOCR
    # =========================================================

    def _get_ocr_reader(self):

        if self._ocr_initialized:
            return self._ocr_reader

        self._ocr_initialized = True

        try:
            import easyocr
            import torch

            use_gpu = torch.cuda.is_available()

            logger.info(f"Initializing EasyOCR Vietnamese + English (GPU={use_gpu})...")

            self._ocr_reader = easyocr.Reader(
                ["vi", "en"],
                gpu=use_gpu,
                download_enabled=True,
            )

        except Exception as e:
            logger.warning(
                "EasyOCR initialization failed: %s",
                e,
            )

            self._ocr_reader = None

        return self._ocr_reader

    # =========================================================
    # Tier 1 + Tier 2 filters
    # =========================================================

    @staticmethod
    def _get_image_height(image_bytes: bytes) -> int | None:
        """Return the pixel height of an image, or None on failure."""
        try:
            from PIL import Image as PILImage

            img = PILImage.open(io.BytesIO(image_bytes))
            return img.height
        except Exception:
            return None

    @staticmethod
    def _bbox_height(bbox: list) -> float:
        """
        Return the pixel height of an EasyOCR bounding box.

        EasyOCR bbox format: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
        So top-y is bbox[0][1] and bottom-y is bbox[2][1].
        """
        return abs(bbox[2][1] - bbox[0][1])

    def _filter_ocr_results(
        self,
        results: list,
        image_bytes: bytes,
    ) -> list:
        """
        Apply two-tier spatial filter to EasyOCR results to suppress
        background text (watermarks, event-banner captions, etc.).

        Tier 1 — Confidence threshold (``ocr_confidence_threshold``):
            EasyOCR assigns each detected region a confidence in [0, 1].
            Foreground slide/document text is typically ≥ 0.5.
            Background noise (blurry, low-contrast) tends to be < 0.35.
            Drop any region below the threshold.

        Tier 2 — Minimum text height ratio (``ocr_min_text_height_ratio``):
            Background watermarks and event-banner captions are physically
            small compared to the image.  Foreground text on a presentation
            slide occupies at least ~1.5 % of the image height.
            Drop any region whose bounding-box height / image_height is
            below this ratio.

        Both thresholds are configurable via ``src/config.py`` or .env:
            OCR_CONFIDENCE_THRESHOLD=0.35
            OCR_MIN_TEXT_HEIGHT_RATIO=0.015
        """
        conf_threshold = self.settings.ocr_confidence_threshold
        height_ratio_threshold = self.settings.ocr_min_text_height_ratio

        # Retrieve image height once for Tier 2
        img_height: int | None = None
        if height_ratio_threshold > 0:
            img_height = self._get_image_height(image_bytes)

        kept = []
        dropped_conf = 0
        dropped_size = 0

        for r in results:
            bbox, text, conf = r[0], r[1], r[2]

            # --- Tier 1: Confidence ---
            if conf < conf_threshold:
                dropped_conf += 1
                logger.debug(
                    "OCR Tier-1 drop (conf=%.2f < %.2f): %r",
                    conf,
                    conf_threshold,
                    str(text)[:60],
                )
                continue

            # --- Tier 2: Bounding-box height ratio ---
            if img_height and img_height > 0:
                h = self._bbox_height(bbox)
                ratio = h / img_height
                if ratio < height_ratio_threshold:
                    dropped_size += 1
                    logger.debug(
                        "OCR Tier-2 drop (h_ratio=%.4f < %.4f): %r",
                        ratio,
                        height_ratio_threshold,
                        str(text)[:60],
                    )
                    continue

            kept.append(r)

        if dropped_conf or dropped_size:
            logger.info(
                "OCR filter: kept %d / %d regions (dropped conf=%d, size=%d)",
                len(kept),
                len(results),
                dropped_conf,
                dropped_size,
            )

        return kept

    # =========================================================
    # Tier 2.5 — Text Orientation Filter
    # =========================================================

    @staticmethod
    def _calculate_bbox_angle(bbox: list) -> float:
        """
        Tính góc xoay (độ) của bounding box dựa trên cạnh trên.

        EasyOCR bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        Cạnh trên: top-left → top-right = bbox[0] → bbox[1]

        Returns:
            Góc tính bằng độ. 0° = nằm ngang, 90° = dọc.
        """
        top_left = bbox[0]
        top_right = bbox[1]
        dx = top_right[0] - top_left[0]
        dy = top_right[1] - top_left[1]
        angle = math.degrees(math.atan2(dy, dx))
        return angle

    @staticmethod
    def _has_table_structure(results: list, bucket_tolerance: float = 25.0) -> bool:
        """
        Heuristic phát hiện cấu trúc bảng trong kết quả OCR.

        Nếu có >= 4 bbox thẳng hàng theo cả X (cùng cột) và Y (cùng hàng),
        coi là có table structure → cho phép text xoay 45°/90° (header cột).

        Args:
            results: Danh sách EasyOCR results [(bbox, text, conf), ...]
            bucket_tolerance: Dung sai pixel để gom cùng cột/hàng.
        """
        if len(results) < 4:
            return False

        # Lấy tọa độ trung tâm
        x_mids = []
        y_mids = []
        for r in results:
            bbox = r[0]
            x_mid = (bbox[0][0] + bbox[2][0]) / 2
            y_mid = (bbox[0][1] + bbox[2][1]) / 2
            x_mids.append(x_mid)
            y_mids.append(y_mid)

        # Đếm số cột: gom X theo bucket
        x_sorted = sorted(x_mids)
        col_count = 1
        for i in range(1, len(x_sorted)):
            if x_sorted[i] - x_sorted[i - 1] > bucket_tolerance:
                col_count += 1

        # Đếm số hàng: gom Y theo bucket
        y_sorted = sorted(y_mids)
        row_count = 1
        for i in range(1, len(y_sorted)):
            if y_sorted[i] - y_sorted[i - 1] > bucket_tolerance:
                row_count += 1

        # Nếu có ít nhất 2 cột × 2 hàng → table structure
        return col_count >= 2 and row_count >= 2

    def _filter_by_orientation(
        self,
        results: list,
        orientation_threshold: float | None = None,
    ) -> list:
        """
        Tier 2.5 — Loại bỏ text có hướng khác biệt rõ rệt so với dominant
        direction (ví dụ: text background xoay 30° trên slide ngang).

        Ngoại lệ:
        - Bảng tính: giữ lại text 40°-95° (header cột xoay 45°/90°)
        - Kết quả quá ít (< 3 bbox): không filter

        Args:
            results: OCR results sau Tier 1+2
            orientation_threshold: Ngưỡng góc lệch tối đa (độ). Default từ config.
        """
        if len(results) < 3:
            return results

        if orientation_threshold is None:
            orientation_threshold = self.settings.ocr_orientation_threshold

        # Tính góc của mỗi bbox
        angles = [self._calculate_bbox_angle(r[0]) for r in results]

        # Tìm dominant angle = median
        dominant_angle = median(angles)

        # Kiểm tra table structure
        has_table = self._has_table_structure(results)

        kept = []
        dropped = 0

        for r, angle in zip(results, angles):
            diff = abs(angle - dominant_angle)

            if diff <= orientation_threshold:
                # Trong phạm vi cho phép
                kept.append(r)
            elif has_table and 40 <= abs(angle) <= 95:
                # Ngoại lệ: bảng tính với header cột xoay 45°/90°
                kept.append(r)
                logger.debug(
                    "OCR Tier-2.5 keep (table exception, angle=%.1f°): %r",
                    angle,
                    str(r[1])[:60],
                )
            else:
                dropped += 1
                logger.debug(
                    "OCR Tier-2.5 drop (angle=%.1f° vs dominant=%.1f°): %r",
                    angle,
                    dominant_angle,
                    str(r[1])[:60],
                )

        if dropped:
            logger.info(
                "OCR Tier-2.5 orientation filter: kept %d / %d (dropped %d, dominant=%.1f°, threshold=%.1f°, table=%s)",
                len(kept),
                len(results),
                dropped,
                dominant_angle,
                orientation_threshold,
                has_table,
            )

        return kept

    # =========================================================
    # Adaptive spatial sort
    # =========================================================

    @staticmethod
    def _sort_ocr_results_top_to_bottom(results: list) -> list:
        """
        Sắp xếp kết quả EasyOCR theo thứ tự đọc tự nhiên:
        top → bottom, cùng hàng thì left → right.

        Mỗi phần tử trong results có dạng:
            (bbox, text, confidence)
        Trong đó bbox = [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            - r[0][0] = top-left  = [x1, y1]
            - r[0][2] = bot-right = [x2, y2]

        Chiến lược — Adaptive Bucket:
        - Tính median chiều cao bbox → xác định kích thước tự nhiên của text
        - Bucket size = max(median_height × 0.5, 5px)
        - Gom vào bucket để tránh lệch pixel giữa các text cùng dòng
        - Trong cùng bucket, sort theo X trung bình → left → right

        Ưu điểm so với bucket cố định 20px:
        - Phù hợp mọi resolution ảnh (low-res, high-res, 300dpi scan)
        - Grid layout (4×2 ô) được đọc đúng thứ tự:
          ô1→ô2→ô3→ô4 (hàng 1), ô5→ô6→ô7→ô8 (hàng 2)
        """
        if not results:
            return results

        # Tính median chiều cao bbox
        heights = sorted(abs(r[0][2][1] - r[0][0][1]) for r in results)
        median_h = heights[len(heights) // 2] if heights else 20.0

        # Bucket size tự thích ứng: nửa chiều cao chữ, tối thiểu 5px
        bucket_size = max(median_h * 0.5, 5.0)

        def sort_key(r):
            bbox = r[0]
            y_mid = (bbox[0][1] + bbox[2][1]) / 2  # Y trung bình
            x_mid = (bbox[0][0] + bbox[2][0]) / 2  # X trung bình
            # Gom Y thành bucket adaptive
            row_bucket = round(y_mid / bucket_size)
            return (row_bucket, x_mid)

        return sorted(results, key=sort_key)

    # =========================================================
    # Post-OCR brand-name quick fix
    # =========================================================

    @staticmethod
    def _apply_post_ocr_brand_fixes(text: str) -> str:
        """
        Sửa nhanh các lỗi OCR brand-name phổ biến nhất trực tiếp
        trên raw OCR text, trước khi Tier 4 (MarkdownNormalizer)
        chạy. Chỉ gồm 2-3 pattern critical.
        """
        for pattern, replacement in _POST_OCR_BRAND_FIXES:
            text = pattern.sub(replacement, text)
        return text

    # =========================================================
    # Tier 3 — Color-Contrast Filter (Background Text Suppression)
    # =========================================================

    @staticmethod
    def _calc_bbox_center(bbox: list) -> tuple[int, int]:
        """Return pixel center (x, y) of an EasyOCR bounding box."""
        x_mid = int((bbox[0][0] + bbox[2][0]) / 2)
        y_mid = int((bbox[0][1] + bbox[2][1]) / 2)
        return x_mid, y_mid

    def _filter_by_contrast(
        self,
        results: list,
        image_bytes: bytes,
    ) -> list:
        """
        Tier 3 — Color-Contrast filter.

        Loại bỏ text có màu quá gần với màu nền (background).
        Phương pháp:
        1. Lấy màu tại tâm bbox (text center).
        2. Lấy màu nền = mean pixel xung quanh bbox (margin 5px).
        3. Tính luminance difference theo công thức ITU-R BT.601.
        4. Nếu diff < `ocr_contrast_threshold`, drop.

        Thực tế:
        - Foreground slide text (trắng/đen nếu nền tối): diff thường > 80.
        - Background decorative text (cùng tông): diff thường < 30.
        - Watermark mờ: diff ~ 15–40.
        """
        threshold = self.settings.ocr_contrast_threshold
        if threshold <= 0:
            return results  # Tất tính năng

        try:
            from PIL import Image as PILImage

            img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
            img_arr = None

            # Lazy import numpy — chỉ cần khi có contrast filter
            try:
                import numpy as np

                img_arr = np.array(img)
            except ImportError:
                logger.debug("Tier 3 contrast filter skipped: numpy not available.")
                return results

            h_img, w_img = img_arr.shape[:2]

            def lum(rgb: tuple) -> float:
                """Luminance ITU-R BT.601: 0.299R + 0.587G + 0.114B"""
                r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
                return 0.299 * r + 0.587 * g + 0.114 * b

            kept: list = []
            dropped = 0

            for r in results:
                bbox = r[0]
                # Tâm bbox
                cx, cy = self._calc_bbox_center(bbox)

                # Pixel tâm text
                cx_c = max(0, min(cx, w_img - 1))
                cy_c = max(0, min(cy, h_img - 1))
                text_pixel = img_arr[cy_c, cx_c]
                text_lum = lum(text_pixel)

                # Background: pixel margin 5px ngoài bbox (lingual corner)
                x1 = max(0, int(bbox[0][0]) - 5)
                y1 = max(0, int(bbox[0][1]) - 5)
                x2 = min(w_img - 1, int(bbox[2][0]) + 5)
                y2 = min(h_img - 1, int(bbox[2][1]) + 5)

                # Lấy mẫu pixel tại các góc ngoài (4 corners outside bbox)
                corners = [
                    img_arr[y1, x1] if y1 >= 0 and x1 >= 0 else text_pixel,
                    img_arr[y1, x2] if y1 >= 0 and x2 < w_img else text_pixel,
                    img_arr[y2, x1] if y2 < h_img and x1 >= 0 else text_pixel,
                    img_arr[y2, x2] if y2 < h_img and x2 < w_img else text_pixel,
                ]
                bg_lum = float(np.mean([lum(c) for c in corners]))

                diff = abs(text_lum - bg_lum)

                if diff < threshold:
                    dropped += 1
                    logger.debug(
                        "OCR Tier-3 drop (lum_diff=%.1f < %.1f): %r",
                        diff,
                        threshold,
                        str(r[1])[:60],
                    )
                else:
                    kept.append(r)

            if dropped:
                logger.info(
                    "OCR Tier-3 contrast filter: kept %d / %d (dropped %d, threshold=%.1f)",
                    len(kept),
                    len(results),
                    dropped,
                    threshold,
                )
            return kept

        except Exception as e:
            logger.debug("Tier 3 contrast filter error (skipping): %s", e)
            return results

    # =========================================================
    # Deskew — Auto-rotate image before OCR
    # =========================================================

    def _deskew_image(self, image_bytes: bytes) -> bytes:
        """
        Tự động deskew (xoay thẳng) ảnh bị lệch trước khi chạy OCR.

        Phương pháp:
        1. Chuyển sang grayscale + threshold nhị phân.
        2. Tìm góc xoay bằng minAreaRect (OpenCV) hoặc hộp bao chữ.
        3. Nếu góc trong phạm vi (-20°, 20°) và khác 0, xoay lại.
        4. Fallback: PIL rotate nếu OpenCV không có.

        Returns:
            image_bytes có thể đã được rotate (hoặc nguyên bản nếu không dùng được).
        """
        if not self.settings.ocr_deskew_enabled:
            return image_bytes

        try:
            from PIL import Image as PILImage

            img = PILImage.open(io.BytesIO(image_bytes))
            width, height = img.size

            # Chỉ deskew nếu ảnh đủ lớn (tránh deskew thumbnail)
            if width < 100 or height < 100:
                return image_bytes

            angle = 0.0

            try:
                import cv2
                import numpy as np

                img_gray = img.convert("L")
                arr = np.array(img_gray)

                # Binary threshold
                _, binary = cv2.threshold(arr, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                # Tìm contours
                coords = np.column_stack(np.where(binary > 0))
                if len(coords) >= 10:
                    rect = cv2.minAreaRect(coords)
                    angle_cv = rect[-1]
                    # minAreaRect trả về góc trong [-90, 0]
                    if angle_cv < -45:
                        angle = 90 + angle_cv
                    else:
                        angle = angle_cv

            except ImportError:
                # OpenCV không có: không deskew
                return image_bytes

            # Chỉ xoay nếu góc đáng kể (> 0.5°) và trong giới hạn an toàn (-20°, 20°)
            if abs(angle) > 0.5 and abs(angle) < 20.0:
                rotated = img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
                buf = io.BytesIO()
                rotated.save(buf, format=img.format or "PNG")
                buf.seek(0)
                logger.info("Deskew: rotated %.2f° (%dx%d → %dx%d)", angle, width, height, *rotated.size)
                return buf.read()

        except Exception as e:
            logger.debug("Deskew failed (skipping): %s", e)

        return image_bytes

    # =========================================================
    # Main OCR runner
    # =========================================================

    def _run_ocr(
        self,
        image_bytes: bytes,
    ) -> str:
        """
        Chạy EasyOCR với detail=1 để lấy bounding box,
        áp dụng bộ lọc Tier 1+2+2.5+3 để loại background text,
        sau đó sắp xếp top→bottom, left→right trước khi join văn bản.
        Cuối cùng apply post-OCR brand-name fixes.

        Pipeline:
            [Deskew] → [EasyOCR] → [Tier 1: Confidence] → [Tier 2: Size]
            → [Tier 2.5: Orientation] → [Tier 3: Contrast] → [Sort] → [Brand fix]
        """
        # Bước 0: Deskew nếu có (scanned PDF bị lệch)
        image_bytes = self._deskew_image(image_bytes)

        reader = self._get_ocr_reader()

        if reader is not None:
            try:
                # detail=1: trả về list[(bbox, text, confidence)]
                results = reader.readtext(
                    image_bytes,
                    detail=1,
                )

                if results:
                    # Áp dụng Tier 1 (confidence) + Tier 2 (font size)
                    results = self._filter_ocr_results(results, image_bytes)

                if results:
                    # Áp dụng Tier 2.5 (orientation filter)
                    results = self._filter_by_orientation(results)

                if results:
                    # Áp dụng Tier 3 (color-contrast filter)
                    results = self._filter_by_contrast(results, image_bytes)

                if results:
                    # Sắp xếp theo thứ tự đọc tự nhiên (adaptive bucket)
                    results_sorted = self._sort_ocr_results_top_to_bottom(results)

                    text = " ".join(str(r[1]).strip() for r in results_sorted if str(r[1]).strip()).strip()

                    if text:
                        # Post-OCR brand-name quick fix
                        text = self._apply_post_ocr_brand_fixes(text)
                        return text

            except Exception as e:
                logger.warning(
                    "EasyOCR failed: %s",
                    e,
                )

        return ""
