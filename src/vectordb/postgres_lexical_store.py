"""PostgreSQL lexical retrieval using the Vietnamese-safe simple configuration."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.db.models import DocumentChunk
from src.vectordb.access_control import allowed_document_roles


class PostgresLexicalSearchError(RuntimeError):
    """Raised when PostgreSQL lexical retrieval fails."""


class PostgresLexicalStore:
    def __init__(self, *, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _allowed_roles(role: str | None, access_scope: list[str] | None) -> list[str] | None:
        allowed = allowed_document_roles(role, access_scope)
        return sorted(allowed) if allowed else None

    @staticmethod
    def _or_query(query_text: str) -> str:
        tokens = [token for token in re.findall(r"[\w]+", query_text, flags=re.UNICODE) if token]
        return " | ".join(tokens)

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_query = query_text.strip()
        allowed_roles = self._allowed_roles(role, access_scope)
        if not normalized_query or top_k < 1 or not allowed_roles:
            return []

        simple_config = literal_column("'simple'")
        document_vector = func.to_tsvector(simple_config, func.coalesce(DocumentChunk.content, ""))
        query = func.to_tsquery(simple_config, self._or_query(normalized_query))
        score = func.ts_rank_cd(document_vector, query)
        statement = select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.content,
            DocumentChunk.chunk_metadata.label("metadata"),
            score.label("score"),
        ).where(document_vector.op("@@")(query))
        statement = statement.where(DocumentChunk.role.in_(allowed_roles))
        statement = statement.order_by(score.desc()).limit(top_k)

        session = self.session_factory()
        try:
            rows = session.execute(statement).mappings().all()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "metadata": row["metadata"] or {},
                    "score": float(row["score"]),
                    "source_type": "lexical",
                }
                for row in rows
            ]
        except Exception as error:
            session.rollback()
            raise PostgresLexicalSearchError("lexical retrieval failed") from error
        finally:
            session.close()


class EnhancedPostgresLexicalStore(PostgresLexicalStore):
    """Benchmark variant combining FTS with accent-insensitive trigram ranking."""

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_query = query_text.strip()
        allowed_roles = self._allowed_roles(role, access_scope)
        if not normalized_query or top_k < 1 or not allowed_roles:
            return []

        simple_config = literal_column("'simple'")
        document_vector = func.to_tsvector(simple_config, func.coalesce(DocumentChunk.content, ""))
        query = func.to_tsquery(simple_config, self._or_query(normalized_query))
        fts_score = func.ts_rank_cd(document_vector, query)
        normalized_content = func.unaccent(func.lower(DocumentChunk.content))
        normalized_input = func.unaccent(func.lower(normalized_query))
        trigram_score = func.word_similarity(normalized_input, normalized_content)
        score = (fts_score + trigram_score).label("score")
        statement = select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.content,
            DocumentChunk.chunk_metadata.label("metadata"),
            score,
        ).where(document_vector.op("@@")(query) | (trigram_score > 0.15))
        statement = statement.where(DocumentChunk.role.in_(allowed_roles))
        statement = statement.order_by(score.desc()).limit(top_k)

        session = self.session_factory()
        try:
            rows = session.execute(statement).mappings().all()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "metadata": row["metadata"] or {},
                    "score": float(row["score"]),
                    "source_type": "lexical_enhanced",
                }
                for row in rows
            ]
        except Exception as error:
            session.rollback()
            raise PostgresLexicalSearchError("lexical retrieval failed") from error
        finally:
            session.close()
