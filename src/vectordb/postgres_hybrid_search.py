"""Hosted hybrid retrieval: pgvector + PostgreSQL lexical search + RRF."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.vectordb.access_control import allowed_document_roles
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.pgvector_store import PgVectorStore
from src.vectordb.postgres_lexical_store import PostgresLexicalStore

logger = logging.getLogger(__name__)


class PostgresHybridRetriever:
    def __init__(
        self,
        *,
        vector_store: PgVectorStore | None = None,
        lexical_store: PostgresLexicalStore | None = None,
        bm25_retriever: BM25Retriever | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.vector_store = vector_store or PgVectorStore()
        settings = get_settings()
        self.bm25_retriever = bm25_retriever
        self.lexical_store = lexical_store
        if self.lexical_store is None and self.bm25_retriever is None:
            # Keep BM25 only when explicitly running the local/legacy backend.
            # Production Railway settings select PostgreSQL lexical retrieval.
            if getattr(settings, "retrieval_backend", None) == "postgres":
                self.lexical_store = PostgresLexicalStore()
            else:
                self.bm25_retriever = BM25Retriever(index_path=Path(settings.bm25_index_path))
        self.rrf_k = rrf_k

    def search(
        self,
        query_text: str,
        top_k: int = 10,
        role: str | None = None,
        access_scope: list[str] | None = None,
        retrieval_queries: list[str] | None = None,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        lexical_weight: float | None = None,
    ) -> list[dict[str, Any]]:
        allowed_roles = allowed_document_roles(role, access_scope)
        if top_k < 1 or not allowed_roles:
            return []
        if lexical_weight is not None:
            bm25_weight = lexical_weight
        fetch_k = top_k * 3
        try:
            vector_hits = self.vector_store.query(
                query_text=query_text, top_k=fetch_k, role=role, access_scope=access_scope
            )
        except Exception as error:
            logger.warning("pgvector search failed; using lexical only: %s", error)
            vector_hits = []

        lexical_hits: list[dict[str, Any]] = []
        try:
            seen: set[str] = set()
            for lexical_query in dict.fromkeys(retrieval_queries or [query_text]):
                if self.lexical_store is not None:
                    hits = self.lexical_store.query(
                        query_text=lexical_query, top_k=fetch_k, role=role, access_scope=access_scope
                    )
                elif self.bm25_retriever is not None:
                    hits = self.bm25_retriever.query(
                        query_text=lexical_query, top_k=fetch_k, role=role, access_scope=access_scope
                    )
                else:
                    hits = []
                for hit in hits:
                    chunk_id = str(hit["chunk_id"])
                    if chunk_id not in seen:
                        seen.add(chunk_id)
                        lexical_hits.append(hit)
        except Exception as error:
            logger.warning("lexical search failed; using pgvector only: %s", error)

        scores: dict[str, float] = {}
        candidates: dict[str, dict[str, Any]] = {}
        for hits, weight in ((vector_hits, vector_weight), (lexical_hits, bm25_weight)):
            for rank, hit in enumerate(hits, start=1):
                metadata = hit.get("metadata") or {}
                chunk_role = str(metadata.get("role", hit.get("role", "general")))
                if chunk_role not in allowed_roles:
                    logger.warning("Discarded unauthorized candidate returned by backend: %s", hit.get("chunk_id"))
                    continue
                chunk_id = str(hit["chunk_id"])
                scores[chunk_id] = scores.get(chunk_id, 0.0) + weight / (self.rrf_k + rank)
                candidates.setdefault(chunk_id, hit)

        ordered_ids = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
        results: list[dict[str, Any]] = []
        for chunk_id in ordered_ids[:top_k]:
            result = candidates[chunk_id].copy()
            result["rrf_score"] = scores[chunk_id]
            results.append(result)
        return results
