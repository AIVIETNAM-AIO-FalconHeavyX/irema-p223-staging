import logging
import pickle
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from src.config import get_settings
from src.vectordb.access_control import allowed_document_roles

logger = logging.getLogger(__name__)

# Kiểm tra underthesea một lần duy nhất khi module được load
_UNDERTHESEA_AVAILABLE: bool | None = None


def _check_underthesea() -> bool:
    """Kiểm tra underthesea có thể import được không. Cache kết quả."""
    global _UNDERTHESEA_AVAILABLE
    if _UNDERTHESEA_AVAILABLE is None:
        try:
            from underthesea import word_tokenize  # noqa: F401

            _UNDERTHESEA_AVAILABLE = True
            logger.info("BM25 sẽ dùng underthesea word_tokenize cho tiếng Việt.")
        except ImportError:
            _UNDERTHESEA_AVAILABLE = False
            logger.warning(
                "underthesea chưa cài — BM25 sẽ dùng whitespace tokenizer. Cài bằng: pip install underthesea"
            )
    return _UNDERTHESEA_AVAILABLE


class BM25Retriever:
    """
    BM25 retriever for exact-match and keyword-based search.
    Supports serialization and role-based filtering.

    Tokenizer: underthesea word_tokenize (tiếng Việt) với fallback whitespace split.
    """

    def __init__(self, index_path: str | Path | None = None):
        self.index_path = Path(index_path or get_settings().bm25_index_path)
        self.bm25: BM25Okapi | None = None
        self.chunks: list[dict[str, Any]] = []

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Tách từ văn bản tiếng Việt & tiếng Anh cho BM25.

        Ưu tiên:
        1. underthesea.word_tokenize() — hiểu từ ghép tiếng Việt
           Ví dụ: "hệ thống" → ["hệ_thống"] (1 token, giữ nghĩa)
        2. Fallback: re.sub + split (behavior cũ, dùng khi underthesea chưa cài)

        underthesea trả về chuỗi với từ ghép nối bởi "_":
            "hệ thống quản lý pin" → "hệ_thống quản_lý pin"
        """
        if not text:
            return []

        text_lower = text.lower().strip()

        if _check_underthesea():
            try:
                from underthesea import word_tokenize

                # format="text" trả về chuỗi, từ ghép được nối bằng "_"
                tokenized_str = word_tokenize(text_lower, format="text")
                tokens = [t for t in tokenized_str.split() if len(t) > 1]
                return tokens
            except Exception as e:
                logger.debug("underthesea tokenize lỗi: %s — dùng fallback", e)

        # Fallback: whitespace tokenizer (behavior cũ)
        cleaned = re.sub(r"[^\w\s]", " ", text_lower)
        return [w for w in cleaned.split() if len(w) > 1]

    def build_index(self, chunks: list[dict[str, Any]]) -> int:
        """Build BM25 index over clean chunk content."""
        if not chunks:
            return 0

        self.chunks = chunks
        corpus = [self.tokenize(c.get("content", "")) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

        # Save index to file
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"chunks": self.chunks, "corpus": corpus}, f)

        logger.info(f"Built and saved BM25 index with {len(chunks)} chunks to {self.index_path}.")
        return len(chunks)

    def load_index(self) -> bool:
        """Load BM25 index from file."""
        if not self.index_path.exists():
            logger.warning(f"BM25 index path does not exist: {self.index_path}")
            return False

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.chunks = data["chunks"]
            corpus = data["corpus"]
            self.bm25 = BM25Okapi(corpus)

        logger.info(f"Loaded BM25 index with {len(self.chunks)} chunks from {self.index_path}.")
        return True

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform keyword BM25 search.
        Enforces role-based access filtering.
        """
        if not self.bm25 or not self.chunks:
            if not self.load_index():
                return []

        tokens = self.tokenize(query_text)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        allowed_roles = allowed_document_roles(role, access_scope)
        if not allowed_roles:
            return []

        scored_chunks = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue

            chunk = self.chunks[idx]
            chunk_role = chunk.get("metadata", {}).get("role", "general")

            if chunk_role not in allowed_roles:
                continue

            scored_chunks.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "metadata": chunk.get("metadata", {}),
                    "score": float(score),
                    "source_type": "bm25",
                }
            )

        # Sort by BM25 score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
