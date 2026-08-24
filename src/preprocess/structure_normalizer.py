from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class AtomicBlock:
    """Represents an atomic text block (paragraph, table, list, code block) that cannot be split."""

    block_type: str  # 'paragraph', 'table', 'list', 'code'
    content: str
    token_count: int = 0


@dataclass
class SectionNode:
    """Represents a structural section node containing metadata and atomic blocks."""

    title: str
    level: int
    page_num: int | None = None
    slide_num: int | None = None
    sheet_name: str | None = None
    timestamp: str | None = None
    path: list[str] = field(default_factory=list)  # Ancestor heading hierarchy path
    blocks: list[AtomicBlock] = field(default_factory=list)


class StructureNormalizer:
    """
    Normalizes markdown structure:
    - Standardizes heading hierarchy (# H1 -> ## H2 -> ### H3).
    - Detects special headers (Slide, Page, Video Timestamp, Sheet).
    - Preserves tables, bullet lists, and code blocks as atomic blocks.
    - Strips leftover extractor caption/tag noise from headers.
    """

    @classmethod
    def normalize_headings(cls, text: str) -> str:
        """
        Clean header text and adjust heading levels so hierarchy progresses sequentially.
        """
        lines = text.split("\n")
        normalized_lines = []
        heading_stack = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Clean up noise from heading text
                match = re.match(r"^(#+)\s*(.*)", stripped)
                if match:
                    hashes, title = match.groups()
                    cleaned_title = cls._clean_heading_title(title)
                    if cleaned_title:
                        raw_level = len(hashes)
                        # Normalize level progression
                        if not heading_stack:
                            norm_level = 1 if raw_level == 1 else 2
                        else:
                            last_level = heading_stack[-1]
                            if raw_level > last_level + 1:
                                norm_level = last_level + 1
                            else:
                                norm_level = max(1, raw_level)

                        heading_stack.append(norm_level)
                        norm_hashes = "#" * norm_level
                        normalized_lines.append(f"{norm_hashes} {cleaned_title}")
                    continue

            normalized_lines.append(line)

        return "\n".join(normalized_lines)

    @classmethod
    def parse_structure(cls, text: str) -> list[SectionNode]:
        """
        Parse normalized markdown into a list of SectionNode objects,
        each containing atomic blocks (tables, lists, paragraphs, code).
        """
        lines = text.split("\n")
        sections: list[SectionNode] = []
        current_path: list[str] = []

        current_section = SectionNode(title="Document Root", level=1, path=[])

        idx = 0
        n = len(lines)

        while idx < n:
            line = lines[idx]
            stripped = line.strip()

            if not stripped:
                idx += 1
                continue

            # 1. Heading Detection
            if stripped.startswith("#"):
                match = re.match(r"^(#+)\s*(.*)", stripped)
                if match:
                    hashes, title = match.groups()
                    level = len(hashes)
                    cleaned_title = cls._clean_heading_title(title)

                    # Update ancestor path context
                    while current_path and len(current_path) >= level:
                        current_path.pop()
                    current_path.append(cleaned_title)

                    # Save non-empty current section before creating a new one
                    if current_section.blocks:
                        sections.append(current_section)

                    # Detect special header metadata
                    page_num = cls._extract_page_num(cleaned_title) or current_section.page_num
                    slide_num = cls._extract_slide_num(cleaned_title) or current_section.slide_num
                    timestamp = cls._extract_timestamp(cleaned_title) or current_section.timestamp
                    sheet_name = cls._extract_sheet_name(cleaned_title) or current_section.sheet_name

                    current_section = SectionNode(
                        title=cleaned_title,
                        level=level,
                        page_num=page_num,
                        slide_num=slide_num,
                        timestamp=timestamp,
                        sheet_name=sheet_name,
                        path=list(current_path),
                        blocks=[],
                    )

                    idx += 1
                    continue

            # 2. Code Block Detection (Atomic)
            if stripped.startswith("```"):
                code_lines = [line]
                idx += 1
                while idx < n:
                    code_lines.append(lines[idx])
                    if lines[idx].strip().startswith("```"):
                        idx += 1
                        break
                    idx += 1
                code_content = "\n".join(code_lines)
                current_section.blocks.append(AtomicBlock(block_type="code", content=code_content))
                continue

            # 3. Table Detection (Atomic)
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = []
                while idx < n and lines[idx].strip().startswith("|") and lines[idx].strip().endswith("|"):
                    table_lines.append(lines[idx])
                    idx += 1
                table_content = "\n".join(table_lines)
                current_section.blocks.append(AtomicBlock(block_type="table", content=table_content))
                continue

            # 4. List Block Detection (Atomic)
            if cls._is_list_item(stripped):
                list_lines = []
                while idx < n and (
                    cls._is_list_item(lines[idx].strip()) or (lines[idx].startswith("  ") and lines[idx].strip())
                ):
                    list_lines.append(lines[idx])
                    idx += 1
                list_content = "\n".join(list_lines)
                current_section.blocks.append(AtomicBlock(block_type="list", content=list_content))
                continue

            # 5. Paragraph Block (Atomic unit per contiguous text paragraph)
            para_lines = []
            while idx < n:
                curr_stripped = lines[idx].strip()
                if (
                    not curr_stripped
                    or curr_stripped.startswith("#")
                    or curr_stripped.startswith("```")
                    or (curr_stripped.startswith("|") and curr_stripped.endswith("|"))
                    or cls._is_list_item(curr_stripped)
                ):
                    break
                para_lines.append(lines[idx])
                idx += 1

            if para_lines:
                para_content = "\n".join(para_lines)
                current_section.blocks.append(AtomicBlock(block_type="paragraph", content=para_content))

        if current_section.blocks or current_section.title != "Document Root":
            sections.append(current_section)

        return sections

    @staticmethod
    def _clean_heading_title(title: str) -> str:
        """Strip trailing HTML comments or caption noise from heading text."""
        cleaned = re.sub(r"<!?--.*?--?>", "", title).strip()
        cleaned = re.sub(r"!+--.*$", "", cleaned).strip()
        return cleaned or title.strip()

    @staticmethod
    def _is_list_item(line: str) -> bool:
        return bool(re.match(r"^[-*+•]\s+\S+", line) or re.match(r"^\d+[.)]\s+\S+", line))

    @staticmethod
    def _extract_page_num(title: str) -> int | None:
        match = re.search(r"\bPage\s+(\d+)\b", title, re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_slide_num(title: str) -> int | None:
        match = re.search(r"\bSlide\s+(\d+)\b", title, re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_timestamp(title: str) -> str | None:
        match = re.search(r"\b(\d{2}:\d{2}(?::\d{2})?)\b", title)
        return match.group(1) if match else None

    @staticmethod
    def _extract_sheet_name(title: str) -> str | None:
        match = re.search(r"\bSheet:\s*(.+)$", title, re.IGNORECASE)
        return match.group(1).strip() if match else None
