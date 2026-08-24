import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


class MarkdownNormalizer:
    """
    Clean and normalize extracted/transcribed Markdown for RAG.

    Pipeline:
        1. Unicode normalization
        2. Line-break/control-character normalization
        3. Remove extractor metadata
        4. Remove known placeholder headings
        5. Detect OCR garbage at line/block level
        6. Safe transcript/OCR typo correction
        7. Normalize whitespace
        8. Preserve Markdown structure, tables and lists

    Important:
        - Do NOT aggressively rewrite uncertain OCR text.
        - Remove only high-confidence OCR garbage.
        - Preserve headings, tables, lists and meaningful short text.
    """

    # Only corrections with relatively high confidence.
    WORD_SPLIT_REPLACEMENTS = [
        (r"\bV\s+inFast\b", "VinFast"),
        (r"\bt\s+ình\b", "tình"),
        (r"\bP\s+hụ\b", "Phụ"),
        (r"\bB\s+ảo\b", "Bảo"),
        (r"\bC\s+ác\b", "Các"),
        (r"\bT\s+iêu\b", "Tiêu"),
        (r"\bK\s+hách\b", "Khách"),
        (r"\bH\s+ạng\b", "Hạng"),
        (r"\bg\s+iới\b", "giới"),
        (r"\bn\s+ăm\b", "năm"),
        (r"\bb\s+ằng\b", "bằng"),
        (r"\bd\s+ụng\b", "dụng"),
        (r"\bs\s+ử\b", "sử"),
        (r"\bđ\s+ược\b", "được"),
        (r"\bt\s+hông\b", "thông"),
        (r"\bp\s+hần\b", "phần"),
        (r"\bt\s+rách\b", "trách"),
        (r"\bn\s+hiệm\b", "nhiệm"),
        (r"\bh\s+ợp\b", "hợp"),
        (r"\bđ\s+ồng\b", "đồng"),
        # Very common OCR accent errors
        (r"\bTiéu\b", "Tiêu"),
        (r"\btiéu\b", "tiêu"),
        (r"\bkhách\s+hang\b", "khách hàng"),
        (r"\bchính\s+sach\b", "chính sách"),
        (r"\bbao\s+hanh\b", "bảo hành"),
        (r"\bthoi\s+gian\b", "thời gian"),
        (r"\bquy\s+trinh\b", "quy trình"),
    ]

    # ---------------------------------------------------------------------------
    # Tier 4 — Brand-name OCR correction dictionary
    # ---------------------------------------------------------------------------
    # These are high-confidence substitutions: the wrong form on the left is
    # unambiguously an OCR artifact of the correct form on the right.
    # Keep patterns minimal and specific to avoid false positives.
    # All patterns are compiled case-sensitively (brand names are case-specific).
    BRAND_CORRECTIONS: list[tuple[str, str]] = [
        # VinFast logo: 'S' rendered as '$' in stylised font
        # Variants: "VINFA$T", "VI N F A $ T", "V I N F A S T" etc.
        # Use lookahead instead of \b at end — \b fails when $ is followed
        # by punctuation like '.' or ',' since $ is a non-word char.
        (r"\bVINFA\$T(?=[\s.,;:!?\-\)\]\"']|$)", "VINFAST"),
        (r"\bVinFa\$t(?=[\s.,;:!?\-\)\]\"']|$)", "VinFast"),
        # Space around dollar: "VINFA $ T", "VINFA$ T", "VINFA $T"
        (r"\bVINFA\s*\$\s*T(?=[\s.,;:!?\-\)\]\"']|$)", "VINFAST"),
        # Space-separated logo reading: "VI N F A $ T"
        (r"\bV\s*I\s*N\s*F\s*A\s*\$\s*T(?=[\s.,;:!?\-\)\]\"']|$)", "VINFAST"),
        # Space-separated logo without dollar: "V I N F A S T"
        (r"\bV\s+I\s+N\s+F\s+A\s+S\s+T\b", "VINFAST"),
        # Rare variant: '1' for 'I', 'l' (lowercase L) for 'I'
        (r"\bV[I1l]NFAST\b", "VINFAST"),
        (r"\bV[I1l]NFa[s\$]t\b", "VinFast"),
        # VinGroup family
        (r"\bV[I1l]NGROUP\b", "VINGROUP"),
        (r"\bVinGr0up\b", "VinGroup"),
        # DMS software name
        (r"\bDN1S\b", "DMS"),
        (r"\bD\s+M\s+S\b", "DMS"),
        # XMĐ — electric motorbike model abbreviation
        (r"\bXMĐ\.\b", "XMĐ"),
    ]

    PLACEHOLDER_HEADINGS = re.compile(
        r"^###\s+(?:Title|Content)\s*$",
        flags=re.IGNORECASE,
    )

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""

        # ---------------------------------------------------------
        # 1. Unicode normalization
        # ---------------------------------------------------------
        cleaned = unicodedata.normalize("NFC", text)

        # ---------------------------------------------------------
        # 2. Normalize line breaks
        # ---------------------------------------------------------
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters but preserve \n and \t.
        cleaned = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "",
            cleaned,
        )

        # ---------------------------------------------------------
        # 3. Remove extractor metadata
        # ---------------------------------------------------------
        cleaned = cls._strip_extractor_noise(cleaned)

        # ---------------------------------------------------------
        # 4. Remove known placeholder headings
        # ---------------------------------------------------------
        cleaned = cls._remove_placeholder_headings(cleaned)

        # ---------------------------------------------------------
        # 5. Process OCR garbage at block level
        # ---------------------------------------------------------
        lines = cleaned.split("\n")
        lines = cls._remove_ocr_noise_blocks(lines)

        # ---------------------------------------------------------
        # 6. Deduplicate consecutive headings
        # ---------------------------------------------------------
        lines = cls._deduplicate_headings(lines)

        # ---------------------------------------------------------
        # 7. Safe typo correction
        # ---------------------------------------------------------
        cleaned = "\n".join(lines)
        cleaned = cls._fix_transcript_errors(cleaned)

        # ---------------------------------------------------------
        # 8. Normalize whitespace
        # ---------------------------------------------------------
        lines = [line.rstrip() for line in cleaned.split("\n")]

        cleaned = "\n".join(lines)

        # Maximum 1 blank line between blocks.
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    # =============================================================
    # EXTRACTOR NOISE
    # =============================================================

    @classmethod
    def _strip_extractor_noise(cls, text: str) -> str:
        """
        Remove known extractor-generated metadata/caption blocks.
        """

        # Example:
        # ### Image Caption
        # Extracted image on Page 16: xxx.png
        text = re.sub(
            r"###\s*Image Caption\s*\n*"
            r"(?:Extracted image on "
            r"(?:Page|Slide)\s+\d+:[^\n]*\n*)+",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Standalone extracted-image lines.
        text = re.sub(
            r"Extracted image on "
            r"(?:Page|Slide)\s+\d+:[^\n]*\n?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Empty Image Caption heading.
        text = re.sub(
            r"###\s*Image Caption\s*(?=\n\n|\n#|$)",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # HTML image comments.
        text = re.sub(
            r"<!--\s*image\s*-->",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return text

    @classmethod
    def _remove_placeholder_headings(cls, text: str) -> str:
        """
        Remove extractor placeholders such as:

            ### Title
            ### Content

        Only remove the exact known placeholders.
        """

        lines = text.split("\n")
        result = []

        for line in lines:
            if cls.PLACEHOLDER_HEADINGS.match(line.strip()):
                continue

            result.append(line)

        return "\n".join(result)

    # =============================================================
    # OCR NOISE DETECTION
    # =============================================================

    @classmethod
    def _remove_ocr_noise_blocks(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Detect consecutive OCR-garbage lines as a block.

        This is important because OCR garbage can look like:
            VÀ Bo Whee eh) ` và La an: | Ưr >>.
            NV VN © WSO) 4 ủ:
            ề h a oe SY 4: j Tướng | tế: | ‘ =.
            iS al ba Ce — Eee Leo ...
        """

        result = []
        block = []
        blank_lines = 0
        max_internal_blank_lines = 2

        def flush_block():
            nonlocal block, blank_lines

            if not block:
                return

            if cls._is_ocr_noise_block(block):
                logger.warning(
                    "Removed OCR-corrupted block/slide: %s",
                    " | ".join(line.strip()[:200] for line in block if line.strip()),
                )
            else:
                result.extend(block)

            block = []
            blank_lines = 0

        for line in lines:
            stripped = line.strip()

            # Keep a small number of blank lines inside a candidate
            # region. OCR from one scanned slide can contain empty lines
            # between corrupted text fragments.
            if not stripped:
                if block and blank_lines < max_internal_blank_lines:
                    block.append(line)
                    blank_lines += 1
                else:
                    flush_block()
                    result.append(line)
                continue

            # Markdown structures terminate an OCR candidate region.
            if cls._is_structural_line(stripped):
                flush_block()
                result.append(line)
                continue

            # Do not decide from this line alone. Keep the whole region so
            # that slide-level corruption can be detected from aggregate
            # OCR signals.

            # Tier 3 — Single-line background-image noise detection.
            # Applied before appending so that individual noisy lines from
            # background images are dropped even when the surrounding block
            # would otherwise pass the aggregate test.
            if cls._is_background_image_noise(stripped):
                logger.info(
                    "OCR Tier-3 drop (background noise): %s",
                    stripped[:120],
                )
                continue

            block.append(line)
            blank_lines = 0

        flush_block()

        return result

    @staticmethod
    def _is_background_image_noise(line: str) -> bool:
        """
        Tier 3 — Detect single OCR lines that are likely read from a
        background image (e.g., event-banner text, crowd-scene captions).

        Signatures of background-image noise:
        • High proportion of isolated single digits / two-digit numbers
          mixed with single ASCII letters ("Start 4 5 Zsvk 9 Ginoziyoh ă 5 13")
        • Many consecutive tokens of length 1-2 that are all
          digits or upper-case ASCII (not Vietnamese)
        • At least 4 tokens total (short lines are kept)

        Conservative: only flag a line when multiple signals agree.
        Vietnamese sentences with numbers are NOT flagged because they
        contain long Vietnamese words alongside the digits.
        """
        stripped = line.strip()
        if not stripped:
            return False

        # Structural lines are never background noise.
        if stripped.startswith(("#", "|", "-", "*", "+")):
            return False

        tokens = stripped.split()
        if len(tokens) < 4:  # too short to judge
            return False

        # Count token types
        digit_only = sum(t.isdigit() for t in tokens)
        single_upper = sum(len(t) == 1 and t.isupper() and t.isascii() for t in tokens)
        # Real Vietnamese words: >= 4 chars AND contain at least one
        # Vietnamese diacritical character (non-ASCII letter).
        # Plain ASCII tokens like "Zsvk", "Ginoziyoh" are NOT counted.
        viet_diacritic = re.compile(
            r"[àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắặẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]"
        )
        viet_words = sum(len(re.sub(r"[^\wÀ-ỹĐđ]", "", t)) >= 4 and bool(viet_diacritic.search(t)) for t in tokens)
        # Long pure-ASCII tokens (no Vietnamese diacritic) mixed with digits
        # are a sign of background OCR noise (banner captions, crowd signs).
        pure_ascii_long = sum(len(t) >= 4 and t.isalpha() and t.isascii() for t in tokens)

        total = len(tokens)
        noise_tokens = digit_only + single_upper
        noise_ratio = noise_tokens / total
        viet_ratio = viet_words / total
        ascii_long_ratio = pure_ascii_long / total

        # Noise if majority are digits/single-caps AND very few real Vietnamese
        # words (with diacritics) exist.
        # Extra guard: require at least 1 digit token so that plain
        # unaccented Vietnamese sentences (e.g. "Ngay 6 thang 10 nam 2015")
        # are not flagged just because they lack diacritics.
        if noise_ratio >= 0.45 and viet_ratio <= 0.15 and digit_only >= 1:
            return True

        # Background-image noise: mix of digits + long ASCII tokens
        # (banner text, runner bibs, crowd signage) with no Vietnamese words.
        # Require a high ratio of pure-ASCII long tokens (>= 0.40) to avoid
        # flagging normal unaccented Vietnamese text.
        if digit_only >= 2 and ascii_long_ratio > 0.40 and viet_ratio == 0 and len(tokens) >= 5:
            return True

        # Also flag dense digit streams: "4 5 9 13 22 ..."
        if digit_only / total >= 0.60:
            return True

        return False

    @classmethod
    def _is_ocr_noise_block(cls, lines: list[str]) -> bool:
        """
        Decide whether a group of suspicious lines is OCR garbage.

        Require multiple suspicious signals to avoid deleting
        legitimate short text.
        """

        meaningful = [line.strip() for line in lines if line.strip()]

        if not meaningful:
            return False

        scores = [cls._ocr_noise_score(line) for line in meaningful]

        avg_score = sum(scores) / len(scores)

        high_noise_lines = sum(score >= 0.70 for score in scores)

        # ---------------------------------------------------------
        # 1. Existing high-confidence line/block rules
        # ---------------------------------------------------------

        # One extremely bad line.
        if len(meaningful) == 1:
            return scores[0] >= 0.85

        if avg_score >= 0.65:
            return True

        if high_noise_lines >= 2:
            return True

        suspicious_ratio = sum(score >= 0.55 for score in scores) / len(scores)

        if len(meaningful) >= 3 and suspicious_ratio >= 0.67:
            return True

        # ---------------------------------------------------------
        # 2. Slide-level OCR corruption detection
        # ---------------------------------------------------------
        #
        # Some badly extracted slides contain a mixture of:
        #   - readable OCR fragments
        #   - random symbols
        #   - single-character tokens
        #   - broken words
        #
        # In this situation individual lines may have a low score even
        # though the entire slide is clearly corrupted. We therefore
        # evaluate the whole non-structural region.

        if len(meaningful) >= 3:
            line_stats = [cls._ocr_corruption_features(line) for line in meaningful]

            avg_symbol_ratio = sum(stat["symbol_ratio"] for stat in line_stats) / len(line_stats)

            avg_short_token_ratio = sum(stat["short_token_ratio"] for stat in line_stats) / len(line_stats)

            avg_suspicious_token_ratio = sum(stat["suspicious_token_ratio"] for stat in line_stats) / len(line_stats)

            heavily_corrupted_lines = sum(stat["corrupted"] for stat in line_stats)

            corrupted_line_ratio = heavily_corrupted_lines / len(line_stats)

            # Require several independent signals. This is deliberately
            # conservative so normal Vietnamese paragraphs, lists and
            # technical text are not deleted just because they contain
            # punctuation or short words.
            if (
                corrupted_line_ratio >= 0.50
                and avg_short_token_ratio >= 0.45
                and avg_symbol_ratio >= 0.15
                and avg_suspicious_token_ratio >= 0.20
            ):
                return True

            # Very severe corruption: even if some readable OCR remains,
            # a slide dominated by broken tokens and symbols should be
            # discarded as a whole.
            if (
                len(meaningful) >= 4
                and corrupted_line_ratio >= 0.67
                and avg_short_token_ratio >= 0.55
                and avg_symbol_ratio >= 0.15
            ):
                return True

        return False

    @classmethod
    def _ocr_corruption_features(cls, line: str) -> dict:
        """
        Extract conservative OCR-corruption signals for slide-level
        detection.

        Returns: symbol_ratio, short_token_ratio,
        suspicious_token_ratio and corrupted.
        """

        stripped = line.strip()
        if not stripped:
            return {
                "symbol_ratio": 0.0,
                "short_token_ratio": 0.0,
                "suspicious_token_ratio": 0.0,
                "corrupted": False,
            }

        chars = [c for c in stripped if not c.isspace()]
        total = len(chars)

        if not total:
            return {
                "symbol_ratio": 0.0,
                "short_token_ratio": 0.0,
                "suspicious_token_ratio": 0.0,
                "corrupted": False,
            }

        symbol_ratio = sum(not c.isalnum() for c in chars) / total

        tokens = stripped.split()
        normalized_tokens = [re.sub(r"[^\wÀ-ỹĐđ]", "", token) for token in tokens]

        if not normalized_tokens:
            return {
                "symbol_ratio": symbol_ratio,
                "short_token_ratio": 0.0,
                "suspicious_token_ratio": 0.0,
                "corrupted": False,
            }

        short_token_ratio = sum(len(token) <= 2 for token in normalized_tokens) / len(normalized_tokens)

        suspicious = 0
        for raw_token, token in zip(tokens, normalized_tokens):
            # Tokens made mostly from punctuation/symbols.
            if not token:
                suspicious += 1
                continue

            raw_non_space = [c for c in raw_token if not c.isspace()]

            if raw_non_space:
                raw_symbol_ratio = sum(not c.isalnum() for c in raw_non_space) / len(raw_non_space)

                if raw_symbol_ratio >= 0.50:
                    suspicious += 1
                    continue

            # Very short alphabetic fragments are suspicious when they
            # occur in a symbol-heavy OCR region.
            if len(token) <= 2:
                suspicious += 1
                continue

            # OCR often produces mixed alphanumeric fragments such as
            # "l4", "2=", "DA0C" or similar broken tokens.
            if len(token) <= 4 and re.search(r"[A-Za-zÀ-ỹĐđ]", token) and re.search(r"\d", token):
                suspicious += 1

        suspicious_token_ratio = suspicious / len(tokens)

        # A line is considered heavily corrupted only when multiple
        # signals agree.
        corrupted = (
            (symbol_ratio >= 0.20 and short_token_ratio >= 0.45)
            or (symbol_ratio >= 0.25 and suspicious_token_ratio >= 0.35)
            or (short_token_ratio >= 0.65 and suspicious_token_ratio >= 0.45)
        )

        return {
            "symbol_ratio": symbol_ratio,
            "short_token_ratio": short_token_ratio,
            "suspicious_token_ratio": suspicious_token_ratio,
            "corrupted": corrupted,
        }

    @classmethod
    def _ocr_noise_score(cls, line: str) -> float:
        """
        Return OCR-garbage confidence score in [0, 1].

        Higher = more likely to be garbage.
        """

        stripped = line.strip()

        if not stripped:
            return 0.0

        # Never classify Markdown structure as OCR garbage.
        if cls._is_structural_line(stripped):
            return 0.0

        chars = [c for c in stripped if not c.isspace()]

        if not chars:
            return 0.0

        total = len(chars)

        # ---------------------------------------------------------
        # Character statistics
        # ---------------------------------------------------------

        has_alnum = any(c.isalnum() for c in chars)
        if not has_alnum:
            return 1.0

        symbols = sum(not c.isalnum() for c in chars)

        symbol_ratio = symbols / total

        score = 0.0

        # ---------------------------------------------------------
        # Too many symbols
        # ---------------------------------------------------------

        if symbol_ratio >= 0.35:
            score += 0.25

        if symbol_ratio >= 0.50:
            score += 0.25

        if symbol_ratio >= 0.65:
            score += 0.15

        # ---------------------------------------------------------
        # Token statistics
        # ---------------------------------------------------------

        tokens = stripped.split()

        if not tokens:
            return 0.0

        word_tokens = re.findall(
            r"[A-Za-zÀ-ỹĐđ]+",
            stripped,
        )

        # Very few real words in a relatively long line.
        if len(stripped) >= 15 and len(word_tokens) <= 2:
            score += 0.25

        # ---------------------------------------------------------
        # Single-character token ratio
        # ---------------------------------------------------------

        single_char_tokens = sum(
            1
            for token in tokens
            if len(
                re.sub(
                    r"[^\wÀ-ỹĐđ]",
                    "",
                    token,
                )
            )
            <= 1
        )

        if len(tokens) >= 5:
            single_ratio = single_char_tokens / len(tokens)

            if single_ratio >= 0.40:
                score += 0.20

            if single_ratio >= 0.60:
                score += 0.20

        # ---------------------------------------------------------
        # OCR-specific symbols
        # ---------------------------------------------------------

        if re.search(
            r"[©®™§]",
            stripped,
        ):
            score += 0.20

        if re.search(
            r"[`~^]",
            stripped,
        ):
            score += 0.15

        # Many vertical bars outside tables.
        if stripped.count("|") >= 2:
            score += 0.15

        # ---------------------------------------------------------
        # Repeated punctuation
        # ---------------------------------------------------------

        if re.search(
            r"([^\w\s])\1{2,}",
            stripped,
        ):
            score += 0.20

        # ---------------------------------------------------------
        # Suspicious symbol clusters
        # ---------------------------------------------------------

        if re.search(
            r"[^\w\s]{3,}",
            stripped,
        ):
            score += 0.15

        # ---------------------------------------------------------
        # Excessive mixed garbage patterns
        # ---------------------------------------------------------

        if re.search(r"[©®™§]", stripped) and re.search(r"[|`~^]", stripped) and len(word_tokens) <= 5:
            score += 0.20

        return min(score, 1.0)

    # =============================================================
    # MARKDOWN STRUCTURE
    # =============================================================

    @classmethod
    def _is_structural_line(cls, stripped: str) -> bool:
        """
        Detect Markdown structures that must be preserved.
        """

        # Heading
        if stripped.startswith("#"):
            return True

        # Bullet list
        if re.match(
            r"^[-*+•]\s+\S+",
            stripped,
        ):
            return True

        # Numbered list
        if re.match(
            r"^\d+[.)]\s+\S+",
            stripped,
        ):
            return True

        # Markdown table
        if stripped.startswith("|") and stripped.endswith("|"):
            return True

        # Table separator
        if re.match(
            r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$",
            stripped,
        ):
            return True

        # Horizontal rule
        if re.match(
            r"^[-*_]{3,}$",
            stripped,
        ):
            return True

        return False

    # =============================================================
    # HEADING DEDUPLICATION
    # =============================================================

    @classmethod
    def _deduplicate_headings(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Remove consecutive identical headings.
        """

        result = []
        previous_heading = None

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("#"):
                if stripped == previous_heading:
                    logger.debug(
                        "Removed duplicate heading: %s",
                        stripped,
                    )
                    continue

                previous_heading = stripped

            elif stripped:
                previous_heading = None

            result.append(line)

        return result

    # =============================================================
    # SAFE TEXT CORRECTION
    # =============================================================

    @classmethod
    def _fix_transcript_errors(
        cls,
        text: str,
    ) -> str:
        """
        Apply only high-confidence corrections.

        No semantic guessing or LLM-based rewriting here.
        """

        # 1. Known OCR word splits.
        for pattern, replacement in cls.WORD_SPLIT_REPLACEMENTS:
            text = re.sub(
                pattern,
                replacement,
                text,
            )

        # 2. Remove whitespace before punctuation.
        text = re.sub(
            r"\s+([.,;:!?])(?=\s|$)",
            r"\1",
            text,
        )

        # 3. Normalize multiple spaces inside text.
        text = re.sub(
            r"(?<=\S)[ \t]{2,}(?=\S)",
            " ",
            text,
        )

        # 4. Tier 4 — Brand-name OCR corrections.
        #    Applied last so word-split fixes (step 1) run first.
        for pattern, replacement in cls.BRAND_CORRECTIONS:
            text = re.sub(pattern, replacement, text)

        return text
