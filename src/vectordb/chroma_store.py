import logging
from pathlib import Path
from typing import Any

import chromadb

from src.config import get_settings
from src.embedding.embedder import EmbeddingService
from src.vectordb.access_control import allowed_document_roles

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    ChromaDB Vector Store implementation for semantic vector search.
    Enforces persistent storage and metadata-based role filtering.
    """

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str = "rag_chunks",
        embedder: EmbeddingService | None = None,
    ):
        settings = get_settings()
        self.persist_dir = str(persist_dir or settings.chroma_persist_dir)
        self.collection_name = collection_name
        self.embedder = embedder or EmbeddingService()

        # Initialize persistent ChromaDB client
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)

        # Kiểm tra và xử lý dimension mismatch trước khi lấy collection
        self._ensure_collection_compatible()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _ensure_collection_compatible(self) -> None:
        """
        Kiểm tra xem collection hiện tại có cùng embedding dimension với model không.
        Nếu khác (ví dụ: cũ 384 dims, mới 1024 dims) → xóa collection cũ.
        Xử lý này cần thiết khi đổi từ all-MiniLM-L6-v2 (384) sang bge-m3 (1024).
        """
        try:
            col = self.client.get_collection(self.collection_name)
            count = col.count()
            if count == 0:
                return  # Collection rỗng, không cần kiểm tra

            # Lấy 1 vector mẫu để xem dimension
            sample = col.peek(limit=1)
            if not sample.get("embeddings") or not sample["embeddings"]:
                return

            stored_dim = len(sample["embeddings"][0])
            expected_dim = self.embedder.embedding_dim

            if stored_dim != expected_dim:
                logger.warning(
                    "ChromaDB dimension mismatch: stored=%d, model=%d (%s). "
                    "Xóa collection cũ để rebuild với model mới...",
                    stored_dim,
                    expected_dim,
                    self.embedder.model_name,
                )
                self.client.delete_collection(self.collection_name)
                logger.info(
                    "Đã xóa collection '%s'. Sẽ tạo lại khi add_chunks().",
                    self.collection_name,
                )
        except Exception:
            # Collection chưa tồn tại hoặc lỗi không quan trọng → bỏ qua
            pass

    def add_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """
        Add a list of chunk dictionaries to ChromaDB.
        Each chunk dict must have 'chunk_id', 'content', and 'metadata'.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []
        texts_to_embed = []

        seen_ids = set()

        for chunk in chunks:
            raw_id = chunk["chunk_id"]
            chunk_id = raw_id
            counter = 1
            while chunk_id in seen_ids:
                chunk_id = f"{raw_id}_v{counter}"
                counter += 1
            seen_ids.add(chunk_id)

            content = chunk["content"]
            meta = chunk.get("metadata", {})

            # Clean metadata for ChromaDB scalar constraints
            cleaned_meta = {}
            for k, v in meta.items():
                if v is None:
                    continue
                if isinstance(v, list):
                    cleaned_meta[k] = " > ".join(str(item) for item in v)
                elif isinstance(v, (str, int, float, bool)):
                    cleaned_meta[k] = v
                else:
                    cleaned_meta[k] = str(v)

            cleaned_meta["raw_content"] = chunk.get("raw_content", content)[:1000]

            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(cleaned_meta)
            texts_to_embed.append(content)

        logger.info(f"Generating embeddings for {len(texts_to_embed)} chunks...")
        embeddings = self.embedder.embed_documents(texts_to_embed)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Successfully indexed {len(ids)} chunks into ChromaDB collection '{self.collection_name}'.")
        return len(ids)

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic similarity vector search.
        Enforces role-based access filtering.
        """
        allowed_roles = allowed_document_roles(role, access_scope)
        if not allowed_roles:
            return []

        query_embedding = self.embedder.embed_text(query_text)

        # Build metadata filter
        where_filter = {"role": {"$in": sorted(allowed_roles)}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        if results and results["ids"] and results["ids"][0]:
            for idx in range(len(results["ids"][0])):
                doc_id = results["ids"][0][idx]
                doc_text = results["documents"][0][idx]
                meta = results["metadatas"][0][idx]
                distance = results["distances"][0][idx]
                # Convert distance to similarity score
                similarity = 1.0 - distance

                hits.append(
                    {
                        "chunk_id": doc_id,
                        "content": doc_text,
                        "metadata": meta,
                        "score": similarity,
                        "distance": distance,
                        "source_type": "vector",
                    }
                )

        return hits

    def reset(self):
        """Clear collection contents."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.warning(f"Reset exception: {e}")
