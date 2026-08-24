"""Diagnostic engine for analyzing retrieval accuracy and root causes."""

from __future__ import annotations

from typing import Any


class RetrievalDiagnostics:
    """
    Analyzes retrieval results against Ground Truth expectations and determines
    root causes and actionable recommendations.
    """

    @staticmethod
    def is_match(expected_docs: list[str], chunk_id: str, title: str, content: str) -> bool:
        """Check if any expected document identifier matches the retrieved chunk."""
        if not expected_docs:
            return True
        c_id_lower = chunk_id.lower()
        title_lower = title.lower()
        content_lower = content.lower()

        for exp in expected_docs:
            exp_clean = exp.lower().strip()
            if not exp_clean:
                continue
            if (
                exp_clean in c_id_lower
                or exp_clean in title_lower
                or exp_clean.replace("_", " ") in title_lower
                or exp_clean.replace("-", " ") in title_lower
                or exp_clean in content_lower
            ):
                return True
        return False

    @classmethod
    def diagnose_case(
        cls,
        expected_docs: list[str],
        retrieval_results: list[dict[str, Any]],
        candidates_pre_rerank: list[dict[str, Any]] | None,
        selected_context: list[str],
        final_answer: str = "",
        expected_keywords: list[str] | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Diagnose a single test case execution and return structured diagnosis.
        """
        hit_rank = None
        hit_item = None

        for rank, item in enumerate(retrieval_results, start=1):
            chunk_id = item.get("document_id", item.get("chunk_id", ""))
            title = item.get("title", item.get("doc_name", ""))
            content = item.get("content", item.get("raw_content", ""))

            if cls.is_match(expected_docs, chunk_id, title, content):
                hit_rank = rank
                hit_item = item
                break

        # Context presence check
        context_has_expected = False
        if hit_item:
            c_text = hit_item.get("content", "")[:200]
            context_has_expected = any(c_text in ctx for ctx in selected_context) or bool(selected_context)
        elif selected_context:
            context_has_expected = any(
                cls.is_match(expected_docs, "", "", ctx) for ctx in selected_context
            )

        # Keyword presence in answer
        keywords_matched = []
        if expected_keywords and final_answer:
            keywords_matched = [
                kw for kw in expected_keywords if kw.lower() in final_answer.lower()
            ]

        # Determine Status
        if hit_rank == 1:
            status = "HIT_TOP_1"
            severity = "SUCCESS"
        elif hit_rank is not None and hit_rank <= top_k:
            status = "HIT_TOP_K"
            severity = "WARNING"
        else:
            status = "MISSED"
            severity = "ERROR"

        # Determine Root Cause & Recommendations
        root_cause = None
        recommendation = ""

        if status == "HIT_TOP_1":
            if final_answer and expected_keywords and len(keywords_matched) == 0:
                root_cause = "LLM_IGNORED_CONTEXT"
                recommendation = (
                    "Tài liệu truy xuất ở vị trí Top 1 nhưng LLM không trích xuất được từ khóa mong đợi. "
                    "Khắc phục: Tinh chỉnh System Prompt, tăng trọng số cho Context hoặc kiểm tra nhiệt độ (temperature)."
                )
            else:
                recommendation = "Truy xuất chính xác tuyệt đối ở vị trí Top 1 và ngữ cảnh được tích hợp hoàn chỉnh."

        elif status == "HIT_TOP_K":
            root_cause = "SUBOPTIMAL_RANKING"
            recommendation = (
                f"Tài liệu mong đợi nằm ở vị trí thứ {hit_rank} (trong Top {top_k}), chưa đạt Top 1. "
                "Khắc phục: Xem lại trọng số Cross-Encoder Reranker hoặc điều chỉnh tham số RRF vector_weight / bm25_weight."
            )

        else:  # MISSED
            # Kiểm tra xem có xuất hiện trong candidates trước khi rerank không
            in_candidates = False
            candidate_rank = None
            if candidates_pre_rerank:
                for c_rank, c in enumerate(candidates_pre_rerank, start=1):
                    c_id = c.get("chunk_id", "")
                    c_title = c.get("metadata", {}).get("document", "") or c.get("title", "")
                    c_content = c.get("content", "")
                    if cls.is_match(expected_docs, c_id, c_title, c_content):
                        in_candidates = True
                        candidate_rank = c_rank
                        break

            if in_candidates:
                root_cause = "RERANKER_DROPPED_DOCUMENT"
                recommendation = (
                    f"Tài liệu có trong danh sách tìm kiếm ban đầu (hạng {candidate_rank}) nhưng bị Cross-Encoder Reranker loại bỏ hoặc xếp sau Top {top_k}. "
                    "Khắc phục: Hạ min_score_threshold của Reranker, tăng candidate top_k hoặc kiểm tra mô hình Cross-Encoder."
                )
            else:
                root_cause = "RETRIEVAL_OR_INDEXING_FAILURE"
                recommendation = (
                    "Tài liệu hoàn toàn không xuất hiện trong cả Vector Search lẫn BM25 Keyword Search. "
                    "Khắc phục: 1) Kiểm tra xem tài liệu đã được index vào ChromaDB chưa. "
                    "2) Kiểm tra phân quyền RBAC (role filter có vô tình chặn tài liệu không). "
                    "3) Tinh chỉnh Embedding Model hoặc bổ sung từ đồng nghĩa vào câu query."
                )

        return {
            "status": status,
            "severity": severity,
            "hit_rank": hit_rank,
            "is_hit": hit_rank is not None,
            "context_included": context_has_expected,
            "root_cause": root_cause,
            "recommendation": recommendation,
            "expected_docs": expected_docs,
            "expected_keywords": expected_keywords or [],
            "keywords_matched": keywords_matched,
        }
