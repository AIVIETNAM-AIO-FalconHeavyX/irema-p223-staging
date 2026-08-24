import re
import unicodedata


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # 1. Normalize Unicode (NFC standard)
        cleaned = unicodedata.normalize("NFC", text)

        # 2. Fix carriage returns & CRLF to standard LF
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Remove control / non-printable characters
        # Preserve tab and newline.
        cleaned = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "",
            cleaned,
        )

        # 4. Remove placeholder image caption blocks

        # Docling format:
        #
        # ## Extracted Image Captions
        #
        # ### 3.1 Tiêu chuẩn dịch vụ XMĐ_251121_p1_img1.jpeg
        #
        # Image 3.1 Tiêu chuẩn dịch vụ XMĐ_251121_p1_img1.jpeg on Page 1.
        #
        cleaned = re.sub(
            r"##\s*Extracted Image Captions\s*\n+"
            r"(?:"
            r"###\s*[^\n]+\n+"
            r"Image\s+\d+(?:\.\d+)?\s+[^\n]+\s+on\s+(?:Page|Slide)\s+\d+\.\s*\n*"
            r")+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # Remove individual Docling image caption blocks
        cleaned = re.sub(
            r"###\s*[^\n]+\n+"
            r"Image\s+\d+(?:\.\d+)?\s+[^\n]+\s+on\s+(?:Page|Slide)\s+\d+\.\s*\n*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"###\s*Image Caption\s*\n*"
            r"(?:Extracted image on (?:Page|Slide)\s+\d+:[^\n]*\n*)+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"Extracted image on (?:Page|Slide)\s+\d+:[^\n]*\n?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"###\s*Image Caption\s*(?=\n\n|\n#|$)",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # 5. Remove obvious OCR garbage lines
        lines = cleaned.split("\n")
        lines = [line for line in lines if not TextCleaner._is_ocr_noise_line(line)]

        # 6. Normalize excessive blank lines
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 7. Clean trailing whitespace per line
        lines = [line.rstrip() for line in cleaned.split("\n")]

        # 8. Remove duplicate contiguous header/footer lines
        lines = TextCleaner._deduplicate_headers_footers(lines)

        # 9. Normalize bullet list formats
        normalized_lines = []

        for line in lines:
            stripped = line.strip()

            if re.match(
                r"^[\*\+•]\s+",
                stripped,
            ):
                normalized_lines.append(
                    re.sub(
                        r"^[\*\+•]\s+",
                        "- ",
                        line,
                    )
                )
            else:
                normalized_lines.append(line)

        final_text = "\n".join(normalized_lines).strip()

        return final_text

    @staticmethod
    def _is_ocr_noise_line(line: str) -> bool:
        """
        Detect obvious OCR garbage while preserving
        legitimate Markdown, Vietnamese text, numbers,
        technical terms and short valid lines.

        Examples of noise:
            , a £ ~. “ -
            _ + = z <<.“ .
            ==. sac: — \\ \\ - —__.
        """

        stripped = line.strip()

        if not stripped:
            return False

        # -------------------------------------------------
        # Never remove valid Markdown structures
        # -------------------------------------------------

        if stripped.startswith("#"):
            return False

        if re.match(r"^[-*+•]\s+\S+", stripped):
            return False

        if re.match(r"^\d+[.)]\s+\S+", stripped):
            return False

        if stripped.startswith("|") and stripped.endswith("|"):
            return False

        # Markdown horizontal rule
        if re.match(r"^[-*_]{3,}$", stripped):
            return False

        # -------------------------------------------------
        # Very short lines are usually meaningful titles,
        # codes or numbers. Only remove them when they are
        # clearly symbol garbage.
        # -------------------------------------------------

        if len(stripped) <= 2:
            return False

        # -------------------------------------------------
        # Count meaningful characters
        # -------------------------------------------------

        alnum_count = sum(char.isalnum() for char in stripped)

        symbol_count = sum(not char.isalnum() and not char.isspace() for char in stripped)

        total_non_space = sum(not char.isspace() for char in stripped)

        if total_non_space == 0:
            return False

        symbol_ratio = symbol_count / total_non_space

        # -------------------------------------------------
        # Strong OCR garbage signal:
        #
        # Mostly symbols and very little alphanumeric
        # content.
        # -------------------------------------------------

        if len(stripped) >= 5 and alnum_count <= 2 and symbol_ratio >= 0.60:
            return True

        # -------------------------------------------------
        # Lines consisting almost entirely of punctuation
        # / symbols.
        # -------------------------------------------------

        if len(stripped) >= 5 and alnum_count == 0 and symbol_count >= 3:
            return True

        # -------------------------------------------------
        # Detect suspicious repeated symbol patterns.
        #
        # Examples:
        #   ==. --- ___
        #   <<.“ . —__
        # -------------------------------------------------

        repeated_symbols = re.search(
            r"([^\w\s])\1{2,}",
            stripped,
            flags=re.UNICODE,
        )

        if repeated_symbols and alnum_count <= 3 and len(stripped) >= 5:
            return True

        # Isolated single characters separated by spaces (e.g., "Z a R")
        if re.match(r"^(?:[a-zA-Z0-9]\s+){2,}[a-zA-Z0-9]$", stripped):
            return True

        return False

    @staticmethod
    def _deduplicate_headers_footers(
        lines: list[str],
    ) -> list[str]:
        """Detect and remove identical repeated page
        header/footer lines.
        """

        if len(lines) < 20:
            return lines

        line_counts: dict[str, int] = {}

        for line in lines:
            s = line.strip()

            if s and len(s) < 60 and not s.startswith("#") and not s.startswith("|"):
                line_counts[s] = line_counts.get(s, 0) + 1

        # Identify lines repeated >= 3 times.
        repeated_lines = {line for line, count in line_counts.items() if count >= 3}

        result = []

        for line in lines:
            if line.strip() in repeated_lines:
                continue

            result.append(line)

        return result

    @staticmethod
    def normalize_filename(stem: str) -> str:
        """
        Normalize filename stem:
        - Lowercase
        - Remove Vietnamese diacritics / accents
        - Replace spaces and special characters with '_'
        """

        if not stem:
            return "document"

        s = stem.replace("đ", "d").replace("Đ", "D")

        s = unicodedata.normalize(
            "NFD",
            s,
        )

        s = "".join(c for c in s if unicodedata.category(c) != "Mn")

        s = unicodedata.normalize(
            "NFC",
            s,
        ).lower()

        s = re.sub(
            r"[^\w]+",
            "_",
            s,
        )

        s = re.sub(
            r"_{2,}",
            "_",
            s,
        )

        return s.strip("_") or "document"
