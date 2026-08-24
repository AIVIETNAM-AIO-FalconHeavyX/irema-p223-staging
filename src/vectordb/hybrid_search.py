import logging
from typing import Any

from src.vectordb.access_control import allowed_document_roles
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Retriever combining Vector Search (ChromaDB) and Keyword Search (BM25)
    using Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        bm25_retriever: BM25Retriever | None = None,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
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
        """
        Perform hybrid retrieval combining vector similarity and BM25 scores via RRF.
        """
        allowed_roles = allowed_document_roles(role, access_scope)
        if top_k < 1 or not allowed_roles:
            return []

        # Retrieve candidate lists from vector DB and BM25 (fetch extra candidates for fusion)
        fetch_k = top_k * 3

        try:
            vector_hits = self.vector_store.query(
                query_text=query_text,
                top_k=fetch_k,
                role=role,
                access_scope=access_scope,
            )
        except Exception as e:
            logger.warning(f"Vector search failed: {e}. Falling back to BM25.")
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
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}.")
            bm25_hits = []

        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        # Process vector ranks
        for rank, hit in enumerate(vector_hits, start=1):
            if str((hit.get("metadata") or {}).get("role", "general")) not in allowed_roles:
                logger.error("Discarded unauthorized vector candidate: %s", hit.get("chunk_id"))
                continue
            doc_id = hit["chunk_id"]
            rrf_score = vector_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score
            doc_map[doc_id] = hit

        # Process BM25 ranks
        for rank, hit in enumerate(bm25_hits, start=1):
            if str((hit.get("metadata") or {}).get("role", "general")) not in allowed_roles:
                logger.error("Discarded unauthorized BM25 candidate: %s", hit.get("chunk_id"))
                continue
            doc_id = hit["chunk_id"]
            rrf_score = bm25_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in doc_map:
                doc_map[doc_id] = hit

        # Apply Table & Model Keyword Boost when query targets pricing, specs, or models
        query_lower = query_text.lower()
        pricing_spec_keywords = [
            "giá",
            "gia",
            "bao nhiêu",
            "bao nhieu",
            "triệu",
            "trieu",
            "vnd",
            "vnđ",
            "evo200",
            "feliz",
            "klara",
            "theon",
            "vento",
            "impa",
            "ludo",
            "pin",
            "thuê pin",
            "mua pin",
            "cọc pin",
            "thông số",
            "thong so",
            "bảng giá",
            "bang gia",
        ]
        is_table_query = any(k in query_lower for k in pricing_spec_keywords)

        if is_table_query:
            for doc_id, hit in doc_map.items():
                content = hit.get("content", "")
                has_markdown_table = "|" in content and "---" in content
                # Boost chunks containing tables or exact query keyword matches
                boost = 1.0
                if has_markdown_table:
                    boost += 0.25
                if any(m in content.lower() for m in ["evo200", "feliz", "klara", "theon", "vento"]):
                    boost += 0.15
                if boost > 1.0:
                    rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) * boost

        # Sort combined documents by fused RRF score
        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)

        final_results = []
        for doc_id in sorted_doc_ids[:top_k]:
            item = doc_map[doc_id].copy()
            item["rrf_score"] = rrf_scores[doc_id]
            final_results.append(item)

        return final_results
