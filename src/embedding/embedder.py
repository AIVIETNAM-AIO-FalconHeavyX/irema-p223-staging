import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service using Sentence-Transformers.

    Default model: BAAI/bge-m3
    - Đa ngôn ngữ (100+ ngôn ngữ, bao gồm tiếng Việt)
    - 1024 chiều vector (thay vì 384 của all-MiniLM-L6-v2)
    - Context window: 8192 tokens (thay vì 256)
    - Kích thước: ~2.3GB (tải lần đầu ~5-10 phút, cache sau đó)
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

        # Lấy số chiều vector — thử nhiều cách để tương thích các phiên bản
        if hasattr(self.model, "get_embedding_dimension"):
            self.embedding_dim = self.model.get_embedding_dimension()
        elif hasattr(self.model, "get_sentence_embedding_dimension"):
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        else:
            # Fallback: encode 1 chuỗi mẫu để xác định dimension
            sample = self.model.encode("test", normalize_embeddings=True)
            self.embedding_dim = len(sample)

        logger.info(f"Embedding model loaded: {self.model_name} | dim={self.embedding_dim}")

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        if not text:
            return [0.0] * self.embedding_dim
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.tolist() if isinstance(vec, np.ndarray) else list(vec)

    def embed_documents(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """
        Embed a list of text strings into float vectors in batches.
        batch_size=16 để tránh OOM khi chạy trên CPU với model lớn (bge-m3).
        """
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist() if isinstance(embeddings, np.ndarray) else [list(v) for v in embeddings]
