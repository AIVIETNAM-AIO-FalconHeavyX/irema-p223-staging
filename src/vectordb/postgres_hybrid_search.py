"""Hybrid retrieval using PostgreSQL/pgvector dense search and BM25."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.vectordb.access_control import allowed_document_roles
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.pgvector_store import PgVectorStore

logger = logging.getLogger(__name__)


class PostgresHybridRetriever:
    def __init__(
        self,
        *,
        vector_store: PgVectorStore | None = None,
        bm25_retriever: BM25Retriever | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.vector_store = vector_store or PgVectorStore()
        settings = get_settings()
        self.bm25_retriever = bm25_retriever or BM25Retriever(index_path=Path(settings.bm25_index_path))
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
    ) -> list[dict[str, Any]]:
        allowed_roles = allowed_document_roles(role, access_scope)
        if top_k < 1 or not allowed_roles:
            return []

        fetch_k = top_k * 3
        try:
            vector_hits = self.vector_store.query(
                query_text=query_text,
                top_k=fetch_k,
                role=role,
                access_scope=access_scope,
            )
        except Exception as error:
            logger.warning("pgvector search failed; using BM25 only: %s", error)
            vector_hits = []

        try:
            bm25_hits = []
            seen_bm25_ids: set[str] = set()
            for lexical_query in dict.fromkeys(retrieval_queries or [query_text]):
                for hit in self.bm25_retriever.query(
                    query_text=lexical_query,
                    top_k=fetch_k,
                    role=role,
                    access_scope=access_scope,
                ):
                    chunk_id = str(hit["chunk_id"])
                    if chunk_id not in seen_bm25_ids:
                        seen_bm25_ids.add(chunk_id)
                        bm25_hits.append(hit)
        except Exception as error:
            logger.warning("BM25 search failed; using pgvector only: %s", error)
            bm25_hits = []

        scores: dict[str, float] = {}
        candidates: dict[str, dict[str, Any]] = {}
        for hits, weight in ((vector_hits, vector_weight), (bm25_hits, bm25_weight)):
            for rank, hit in enumerate(hits, start=1):
                chunk_role = str((hit.get("metadata") or {}).get("role", "general"))
                if chunk_role not in allowed_roles:
                    logger.error("Discarded unauthorized candidate returned by backend: %s", hit.get("chunk_id"))
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
