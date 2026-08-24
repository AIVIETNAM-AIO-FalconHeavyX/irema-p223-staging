import json
import logging
from pathlib import Path
from typing import Any

from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    Evaluation framework for RAG Retrieval & Reranking pipeline.
    Calculates:
    - Hit Rate@K (Recall@K)
    - Mean Reciprocal Rank (MRR)
    - Role Isolation Compliance Rate
    - Table Query Accuracy
    - Section Match Accuracy
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever | None = None,
        reranker: RerankerService | None = None,
        dataset_path: str | Path | None = None,
    ):
        self.retriever = hybrid_retriever or HybridRetriever()
        self.reranker = reranker or RerankerService()
        self.dataset_path = Path(dataset_path or "./eval/dataset.json")

    def load_dataset(self) -> list[dict[str, Any]]:

        if not self.dataset_path.exists():
            logger.warning(f"Dataset path not found: {self.dataset_path}")
            return []
        with open(self.dataset_path, encoding="utf-8") as f:
            return json.load(f)

    def evaluate(
        self,
        top_k: int = 5,
        test_cases: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        dataset = test_cases or self.load_dataset()
        if not dataset:
            return {"error": "Empty dataset"}

        total_queries = len(dataset)
        hits_at_k = 0
        mrr_sum = 0.0
        role_compliance_passes = 0
        table_queries_total = 0
        table_queries_hits = 0
        section_matches = 0

        query_details = []

        for item in dataset:
            query = item["query"]
            user_role = item.get("role", "general")
            exp_doc = item.get("expected_document_id", "")
            exp_sec = item.get("expected_section", "")
            q_type = item.get("query_type", "text")
            unauthorized = item.get("unauthorized_roles", [])

            # 1. Retrieve candidates via Hybrid Search
            candidates = self.retriever.search(
                query_text=query,
                top_k=top_k * 3,
                role=user_role,
            )

            # 2. Rerank top candidates
            reranked = self.reranker.rerank(
                query_text=query,
                candidates=candidates,
                top_k=top_k,
            )

            # 3. Calculate metrics
            hit_rank = 0
            is_hit = False
            role_compliant = True
            sec_matched = False

            for rank, c in enumerate(reranked, start=1):
                c_doc_id = c.get("chunk_id", "").split("_chunk_")[0]
                c_role = c.get("metadata", {}).get("role", "general")
                c_sec = c.get("metadata", {}).get("section", "") or ""

                # Check role compliance
                if unauthorized and c_role in unauthorized:
                    role_compliant = False

                # Check hit matching
                exp_docs = exp_doc if isinstance(exp_doc, list) else ([exp_doc] if exp_doc else [])
                is_doc_match = any(
                    (
                        d.lower() in c_doc_id.lower()
                        or d.lower() in c.get("metadata", {}).get("document_id", "").lower()
                        or d.lower() in c.get("content", "").lower()
                    )
                    for d in exp_docs
                )
                if is_doc_match and not is_hit:
                    is_hit = True
                    hit_rank = rank

                if exp_sec and exp_sec.lower() in c_sec.lower():
                    sec_matched = True

            if is_hit:
                hits_at_k += 1
                mrr_sum += 1.0 / hit_rank

            if role_compliant:
                role_compliance_passes += 1

            if sec_matched:
                section_matches += 1

            if q_type == "table":
                table_queries_total += 1
                if is_hit:
                    table_queries_hits += 1

            query_details.append(
                {
                    "query_id": item.get("query_id"),
                    "query": query,
                    "user_role": user_role,
                    "is_hit": is_hit,
                    "hit_rank": hit_rank,
                    "role_compliant": role_compliant,
                    "retrieved_count": len(reranked),
                }
            )

        hit_rate = (hits_at_k / total_queries) if total_queries > 0 else 0.0
        mrr = (mrr_sum / total_queries) if total_queries > 0 else 0.0
        role_accuracy = (role_compliance_passes / total_queries) if total_queries > 0 else 0.0
        table_accuracy = (table_queries_hits / table_queries_total) if table_queries_total > 0 else 1.0
        section_accuracy = (section_matches / total_queries) if total_queries > 0 else 0.0

        # Lấy metadata embedding model nếu có
        embedding_model = "unknown"
        embedding_dim = None
        try:
            if hasattr(self.retriever, "vector_store") and hasattr(self.retriever.vector_store, "embedder"):
                embedding_model = self.retriever.vector_store.embedder.model_name
                embedding_dim = self.retriever.vector_store.embedder.embedding_dim
        except Exception:
            pass

        metrics = {
            # Thông tin config (để so sánh trước/sau)
            "embedding_model": embedding_model,
            "embedding_dim": embedding_dim,
            "chunk_config": {
                "min_tokens": 400,
                "max_tokens": 800,
                "overlap_tokens": 80,
            },
            # Metrics
            "total_queries": total_queries,
            "top_k": top_k,
            "hit_rate_at_k": round(hit_rate, 4),
            "mrr": round(mrr, 4),
            "role_compliance_rate": round(role_accuracy, 4),
            "table_retrieval_accuracy": round(table_accuracy, 4),
            "section_match_accuracy": round(section_accuracy, 4),
            "query_details": query_details,
        }

        return metrics
