"""Canary Document Tester (Unique Test) for rapid end-to-end RAG verification."""

from __future__ import annotations

import logging
from typing import Any

from retrieval_debugger.diagnostics import RetrievalDiagnostics
from retrieval_debugger.logger import TestCaseLog
from src.vectordb.chroma_store import ChromaVectorStore
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService

logger = logging.getLogger(__name__)

CANARY_DOC_ID = "doc_canary_unique_test"
DEFAULT_SECRET_TOKEN = "XKCD-98765-VINFAST-CANARY"


class CanaryTester:
    """
    Injects a temporary, unique canary document containing a random/secret token,
    runs an isolated test query, verifies retrieval and LLM context inclusion,
    and cleans up immediately.
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever | None = None,
        reranker: RerankerService | None = None,
    ):
        self.retriever = hybrid_retriever or HybridRetriever()
        self.reranker = reranker or RerankerService()
        self.vector_store: ChromaVectorStore = self.retriever.vector_store

    def inject_canary(self, secret_token: str = DEFAULT_SECRET_TOKEN) -> dict[str, Any]:
        """Temporarily inject the canary chunk into ChromaDB collection."""
        canary_content = (
            f"Tài liệu định danh kiểm thử tự động hệ thống RAG VinFast AI Onboarding.\n"
            f"Mã bí mật của dự án là: {secret_token}.\n"
            f"Mục đích: Xác thực tính toàn vẹn của pipeline tìm kiếm ngữ nghĩa và khả năng tổng hợp của mô hình."
        )

        canary_chunk = {
            "chunk_id": CANARY_DOC_ID,
            "content": canary_content,
            "raw_content": canary_content,
            "metadata": {
                "document": "Canary_Unique_Test_Document",
                "document_id": CANARY_DOC_ID,
                "title": "Tài liệu kiểm định Canary Test",
                "role": "general",
                "section": "Mã bí mật",
                "source": "memory://canary",
                "content_type": "document",
            },
        }

        # Add chunk to ChromaDB
        self.vector_store.add_chunks([canary_chunk])
        logger.info("Injected canary chunk '%s' into ChromaDB.", CANARY_DOC_ID)
        return canary_chunk

    def cleanup_canary(self) -> None:
        """Remove the canary chunk from ChromaDB to prevent dataset pollution."""
        try:
            self.vector_store.collection.delete(ids=[CANARY_DOC_ID])
            logger.info("Cleaned up canary chunk '%s' from ChromaDB.", CANARY_DOC_ID)
        except Exception as e:
            logger.warning("Canary cleanup warning: %s", e)

    def run_canary_test(
        self,
        case_log: TestCaseLog,
        secret_token: str = DEFAULT_SECRET_TOKEN,
        llm_generate: bool = True,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Execute the complete Canary Unique Test:
        1. Inject canary chunk
        2. Query ChromaDB + Hybrid search
        3. Rerank candidates
        4. Optional LLM answer generation
        5. Clean up canary chunk
        6. Return diagnostic report
        """
        query_text = "Mã bí mật của dự án là gì?"
        case_log.input_query = query_text
        case_log.processed_query = query_text
        case_log.user_role = "general"
        case_log.expected_document_id = [CANARY_DOC_ID, "Canary_Unique_Test_Document"]
        case_log.expected_keywords = [secret_token, "XKCD-98765"]

        self.inject_canary(secret_token=secret_token)

        try:
            # 1. Hybrid Search
            candidates = self.retriever.search(
                query_text=query_text,
                top_k=top_k * 3,
                role="general",
            )

            # 2. Rerank
            reranked = self.reranker.rerank(
                query_text=query_text,
                candidates=candidates,
                top_k=top_k,
            )

            case_log.retrieval_results = [
                {
                    "document_id": c.get("chunk_id", ""),
                    "score": float(c.get("rerank_score", c.get("rrf_score", 0.0))),
                    "rank": i,
                    "title": c.get("metadata", {}).get("title", c.get("metadata", {}).get("document", "N/A")),
                    "section": c.get("metadata", {}).get("section", ""),
                    "content": c.get("content", ""),
                }
                for i, c in enumerate(reranked, start=1)
            ]

            selected_context = [
                f"[{c.get('metadata', {}).get('document', 'Canary')}] {c.get('content', '')}"
                for c in reranked
            ]
            case_log.selected_context = selected_context

            # 3. Optional LLM Generation
            final_answer = ""
            if llm_generate:
                try:
                    from src.services.llm import get_llm

                    llm = get_llm()
                    prompt_context = "\n\n".join(selected_context)
                    system_prompt = (
                        "Bạn là Trợ lý AI VinFast. Hãy trả lời câu hỏi dựa CHÍNH XÁC vào ngữ cảnh bên dưới.\n\n"
                        f"Context:\n{prompt_context}"
                    )
                    case_log.final_prompt = system_prompt
                    res = llm.invoke(
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query_text},
                        ]
                    )
                    final_answer = getattr(res, "content", str(res))
                except Exception as e:
                    final_answer = f"[LLM Call Error / Skipped]: {e}"

            case_log.final_answer = final_answer

            # 4. Diagnose
            diagnosis = RetrievalDiagnostics.diagnose_case(
                expected_docs=case_log.expected_document_id,
                retrieval_results=case_log.retrieval_results,
                candidates_pre_rerank=candidates,
                selected_context=case_log.selected_context,
                final_answer=final_answer,
                expected_keywords=case_log.expected_keywords,
                top_k=top_k,
            )

            # Special Canary Assessment
            token_in_answer = secret_token.lower() in final_answer.lower() if final_answer else None
            canary_status = {
                "canary_retrieved": diagnosis["is_hit"],
                "canary_rank": diagnosis["hit_rank"],
                "token_in_context": any(secret_token.lower() in ctx.lower() for ctx in selected_context),
                "token_in_llm_answer": token_in_answer,
                "overall_verdict": "PASSED" if diagnosis["is_hit"] and (token_in_answer is not False) else "FAILED",
            }
            diagnosis["canary_details"] = canary_status
            case_log.diagnosis = diagnosis

            return diagnosis

        finally:
            self.cleanup_canary()
