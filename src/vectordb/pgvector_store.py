"""PostgreSQL/pgvector dense retrieval with SQL authorization filters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.db.models import DocumentChunk
from src.embedding.embedder import EmbeddingService
from src.vectordb.access_control import allowed_document_roles


class InvalidQueryEmbeddingError(ValueError):
    """Raised when the query embedder does not return a BGE-M3 vector."""


class PgVectorSearchError(RuntimeError):
    """Raised when PostgreSQL dense retrieval fails."""


class PgVectorStore:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
        embedder: EmbeddingService | None = None,
        embedding_dimensions: int = 1024,
    ) -> None:
        self.session_factory = session_factory
        self.embedder = embedder or EmbeddingService()
        self.embedding_dimensions = embedding_dimensions

    @staticmethod
    def _allowed_roles(role: str | None, access_scope: list[str] | None) -> list[str] | None:
        allowed = allowed_document_roles(role, access_scope)
        return sorted(allowed) if allowed else None

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        allowed_roles = self._allowed_roles(role, access_scope)
        if top_k < 1 or not allowed_roles:
            return []
        query_embedding = [float(value) for value in self.embedder.embed_text(query_text)]
        if len(query_embedding) != self.embedding_dimensions:
            raise InvalidQueryEmbeddingError(
                f"expected {self.embedding_dimensions} dimensions, got {len(query_embedding)}"
            )

        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        statement = select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.content,
            DocumentChunk.chunk_metadata.label("metadata"),
            distance.label("distance"),
        )
        statement = statement.where(DocumentChunk.role.in_(allowed_roles))
        statement = statement.order_by(distance).limit(top_k)

        session = self.session_factory()
        try:
            rows = session.execute(statement).mappings().all()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "metadata": row["metadata"] or {},
                    "score": 1.0 - float(row["distance"]),
                    "source_type": "vector",
                }
                for row in rows
            ]
        except Exception as error:
            session.rollback()
            raise PgVectorSearchError("dense retrieval failed") from error
        finally:
            session.close()
