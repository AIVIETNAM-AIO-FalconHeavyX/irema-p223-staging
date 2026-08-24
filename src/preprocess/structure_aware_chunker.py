from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from src.preprocess.structure_normalizer import AtomicBlock, SectionNode


@dataclass
class ChunkMetadata:
    document: str
    role: str
    source: str
    page: int | None = None
    slide: int | None = None
    section: str | None = None
    subsection: str | None = None
    heading_path: list[str] = field(default_factory=list)
    timestamp: str | None = None


@dataclass
class TextChunk:
    chunk_id: str
    content: str
    raw_content: str
    token_count: int
    metadata: ChunkMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "raw_content": self.raw_content,
            "token_count": self.token_count,
            "metadata": asdict(self.metadata),
        }


class StructureAwareChunker:
    """
    Structure-aware chunking engine:
    - Chunk size: 400 to 800 tokens (~1600-3200 chars).
    - Sliding window overlap: 80 tokens (~10%) giữa các chunk để giảm mất ngữ cảnh.
    - Preserves tables, bullet lists, and code blocks as atomic non-splittable units.
    - Adds rich context headers and JSON metadata to every chunk payload.

    Lý do tăng chunk size:
    - Tiếng Việt tốn ~1.5-1.8 tokens/từ (cao hơn tiếng Anh).
    - Một quy trình nghiệp vụ thường dài 200-400 từ Việt ≈ 300-700 tokens.
    - BAAI/bge-m3 hỗ trợ context window 8192 tokens — có thể encode chunk dài hơn.
    """

    MIN_TOKENS = 400  # Tăng từ 300
    MAX_TOKENS = 800  # Tăng từ 600
    OVERLAP_TOKENS = 80  # ~10% của MAX_TOKENS — phần lấy lại từ chunk trước

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate token count for Vietnamese/English text (~1.3 tokens per word or ~4 chars/token)."""
        if not text:
            return 0
        words = len(text.split())
        chars = len(text)
        return max(1, math.ceil(max(words * 1.35, chars / 3.8)))

    @classmethod
    def chunk_sections(
        cls,
        sections: list[SectionNode],
        document_id: str,
        title: str,
        role: str,
        source: str,
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        chunk_counter = 1

        for sec in sections:
            if not sec.blocks:
                continue

            # Calculate total section tokens
            sec_text = "\n\n".join(b.content for b in sec.blocks)
            sec_tokens = cls.estimate_tokens(sec_text)

            # Extract section/subsection names from heading path
            if len(sec.path) > 1:
                sec_name = sec.path[1]
                sub_name = sec.path[-1] if len(sec.path) > 2 else None
            elif sec.path:
                sec_name = sec.path[0]
                sub_name = None
            else:
                sec_name = sec.title
                sub_name = None

            # If small section (<= MAX_TOKENS), keep as 1 chunk
            if sec_tokens <= cls.MAX_TOKENS:
                chunk_obj = cls._build_chunk(
                    chunk_id=f"{document_id}_chunk_{chunk_counter:03d}",
                    raw_content=sec_text,
                    doc_title=title,
                    role=role,
                    source=source,
                    page=sec.page_num,
                    slide=sec.slide_num,
                    section=sec_name,
                    subsection=sub_name,
                    heading_path=sec.path,
                    timestamp=sec.timestamp,
                )
                chunks.append(chunk_obj)
                chunk_counter += 1
                continue

            # Long section (> 800 tokens): Split across atomic block boundaries with overlap
            block_chunks = cls._split_long_section(sec, cls.MAX_TOKENS)

            for b_text, t_range in block_chunks:
                ts = t_range or sec.timestamp
                chunk_obj = cls._build_chunk(
                    chunk_id=f"{document_id}_chunk_{chunk_counter:03d}",
                    raw_content=b_text,
                    doc_title=title,
                    role=role,
                    source=source,
                    page=sec.page_num,
                    slide=sec.slide_num,
                    section=sec_name,
                    subsection=sub_name,
                    heading_path=sec.path,
                    timestamp=ts,
                )
                chunks.append(chunk_obj)
                chunk_counter += 1

        return chunks

    @classmethod
    def _split_long_section(cls, section: SectionNode, max_tokens: int) -> list[tuple[str, str | None]]:
        """
        Chia section dài thành các chunk với sliding window overlap.

        Overlap: sau mỗi lần emit chunk, giữ lại OVERLAP_TOKENS token cuối
        từ các paragraph blocks làm prefix cho chunk tiếp theo.
        Lưu ý: Bảng biểu và danh sách (atomic) không bao giờ nằm trong overlap.
        """
        result: list[tuple[str, str | None]] = []
        curr_blocks: list[AtomicBlock] = []
        curr_tokens = 0
        timestamps_in_group: list[str] = []

        for block in section.blocks:
            b_tokens = cls.estimate_tokens(block.content)

            # If atomic block is a paragraph that itself exceeds max_tokens
            if b_tokens > max_tokens and block.block_type == "paragraph":
                # Flush existing accumulated blocks first
                if curr_blocks:
                    text = "\n\n".join(b.content for b in curr_blocks)
                    ts_range = cls._format_ts_range(timestamps_in_group)
                    result.append((text, ts_range))
                    # Overlap: giữ lại paragraph blocks cuối đạt <= OVERLAP_TOKENS
                    curr_blocks, curr_tokens, timestamps_in_group = cls._overlap_tail(curr_blocks)

                # Split long paragraph by sentence boundaries
                para_chunks = cls._split_paragraph_by_sentences(block.content, max_tokens)
                for p_text in para_chunks:
                    result.append((p_text, section.timestamp))
                continue

            # If adding this block exceeds MAX_TOKENS, emit current group
            if curr_tokens + b_tokens > max_tokens and curr_blocks:
                text = "\n\n".join(b.content for b in curr_blocks)
                ts_range = cls._format_ts_range(timestamps_in_group)
                result.append((text, ts_range))
                # Overlap: giữ lại paragraph blocks cuối <= OVERLAP_TOKENS làm prefix
                curr_blocks, curr_tokens, timestamps_in_group = cls._overlap_tail(curr_blocks)

            curr_blocks.append(block)
            curr_tokens += b_tokens
            if section.timestamp:
                timestamps_in_group.append(section.timestamp)

        if curr_blocks:
            text = "\n\n".join(b.content for b in curr_blocks)
            ts_range = cls._format_ts_range(timestamps_in_group)
            result.append((text, ts_range))

        return result

    @classmethod
    def _overlap_tail(
        cls,
        blocks: list[AtomicBlock],
    ) -> tuple[list[AtomicBlock], int, list[str]]:
        """
        Từ danh sách blocks đã emit, trả về phần đuôi
        (chỉ paragraph blocks, tổng <= OVERLAP_TOKENS)
        để dùng làm overlap prefix cho chunk tiếp theo.

        Bảng biểu và danh sách không được lấy lại (tánh trùng lặp dữ liệu).
        """
        overlap_blocks: list[AtomicBlock] = []
        overlap_tokens = 0

        # Duyệt từ cuối về đầu
        for block in reversed(blocks):
            if block.block_type != "paragraph":
                continue  # Không overlap bảng, danh sách, code
            b_tokens = cls.estimate_tokens(block.content)
            if overlap_tokens + b_tokens > cls.OVERLAP_TOKENS:
                break
            overlap_blocks.insert(0, block)
            overlap_tokens += b_tokens

        new_timestamps: list[str] = []  # Timestamps sẽ được append lại khi add block mới
        return overlap_blocks, overlap_tokens, new_timestamps

    @classmethod
    def _split_paragraph_by_sentences(cls, text: str, max_tokens: int) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        sub_chunks: list[str] = []
        curr_sent: list[str] = []
        curr_tokens = 0

        for sent in sentences:
            if not sent.strip():
                continue
            s_tokens = cls.estimate_tokens(sent)
            if curr_tokens + s_tokens > max_tokens and curr_sent:
                sub_chunks.append(" ".join(curr_sent))
                curr_sent = []
                curr_tokens = 0

            curr_sent.append(sent)
            curr_tokens += s_tokens

        if curr_sent:
            sub_chunks.append(" ".join(curr_sent))

        return sub_chunks

    @classmethod
    def _build_chunk(
        cls,
        chunk_id: str,
        raw_content: str,
        doc_title: str,
        role: str,
        source: str,
        page: int | None,
        slide: int | None,
        section: str | None,
        subsection: str | None,
        heading_path: list[str],
        timestamp: str | None,
    ) -> TextChunk:
        # Build contextual prefix string
        ctx_parts = [f"Document: {doc_title}", f"Role: {role}"]
        if source:
            ctx_parts.append(f"Source: {source}")
        if page:
            ctx_parts.append(f"Page: {page}")
        if slide:
            ctx_parts.append(f"Slide: {slide}")
        if heading_path:
            ctx_parts.append(f"Section: {' > '.join(heading_path)}")
        elif section:
            ctx_parts.append(f"Section: {section}")
        if timestamp:
            ctx_parts.append(f"Timestamp: {timestamp}")

        ctx_header = f"[{' | '.join(ctx_parts)}]\n\n"
        full_content = f"{ctx_header}{raw_content}"
        token_count = cls.estimate_tokens(full_content)

        meta = ChunkMetadata(
            document=doc_title,
            role=role,
            source=source,
            page=page,
            slide=slide,
            section=section,
            subsection=subsection,
            heading_path=heading_path or [],
            timestamp=timestamp,
        )

        return TextChunk(
            chunk_id=chunk_id,
            content=full_content,
            raw_content=raw_content,
            token_count=token_count,
            metadata=meta,
        )

    @staticmethod
    def _format_ts_range(timestamps: list[str]) -> str | None:
        if not timestamps:
            return None
        if len(timestamps) == 1:
            return timestamps[0]
        return f"{timestamps[0]} - {timestamps[-1]}"
