#!/usr/bin/env python
"""
Retrieval Debugger CLI Runner.

Usage:
    python retrieval_debugger/run_debug.py
    python retrieval_debugger/run_debug.py --retrieval-only
    python retrieval_debugger/run_debug.py --canary-only
    python retrieval_debugger/run_debug.py --query "Làm thế nào để đăng nhập DMS?" --role accounting
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_debugger.canary_tester import DEFAULT_SECRET_TOKEN, CanaryTester  # noqa: E402
from retrieval_debugger.diagnostics import RetrievalDiagnostics  # noqa: E402
from retrieval_debugger.logger import DebugSessionLogger  # noqa: E402
from retrieval_debugger.reporter import DebugReporter  # noqa: E402
from src.vectordb.hybrid_search import HybridRetriever  # noqa: E402
from src.vectordb.reranker import RerankerService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetrievalDebugger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VinFast AI Onboarding — RAG Retrieval Testing & Debugging Tool"
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default=str(PROJECT_ROOT / "retrieval_debugger" / "ground_truth.json"),
        help="Path to Ground Truth dataset JSON",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top K documents to evaluate (default: 5)",
    )
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Test retrieval and context selection only (skip LLM generation, no API cost)",
    )
    parser.add_argument(
        "--canary-only",
        action="store_true",
        help="Run only the Unique Canary Test",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Ad-hoc single test query string",
    )
    parser.add_argument(
        "--role",
        type=str,
        default="general",
        help="User role for ad-hoc query (sales, accounting, technician, general, owner)",
    )
    parser.add_argument(
        "--secret",
        type=str,
        default=DEFAULT_SECRET_TOKEN,
        help="Secret token to use in the Canary Document",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "retrieval_debugger" / "reports"),
        help="Directory to save generated reports",
    )
    return parser.parse_args()


def run_debugger() -> int:
    args = parse_args()

    print("\n" + "=" * 90)
    print(" 🚀 KHỞI ĐỘNG CÔNG CỤ DEBUG & KIỂM THỬ TRUY XUẤT VĂN BẢN (RETRIEVAL DEBUGGER) ")
    print("=" * 90)
    print(f" Cấu hình: Top K={args.top_k} | Chế độ LLM={'TẮT (Retrieval-Only)' if args.retrieval_only else 'BẬT (End-to-End)'}")
    print(f" Thư mục báo cáo: {args.output_dir}\n")

    session_logger = DebugSessionLogger(session_name="RAG_Retrieval_Debug")
    hybrid_retriever = HybridRetriever()
    reranker = RerankerService()
    canary_tester = CanaryTester(hybrid_retriever=hybrid_retriever, reranker=reranker)

    # ------------------------------------------------------------------
    # 1. Unique Test (Canary Document)
    # ------------------------------------------------------------------
    print("📌 [1/2] Đang thực thi Unique Test (Canary Document)...")
    canary_log = session_logger.create_case_log(
        query_id="CANARY_01",
        input_query="Mã bí mật của dự án là gì?",
        user_role="general",
        expected_document_id=["doc_canary_unique_test", "Canary_Unique_Test_Document"],
        expected_keywords=[args.secret],
    )
    canary_res = canary_tester.run_canary_test(
        case_log=canary_log,
        secret_token=args.secret,
        llm_generate=not args.retrieval_only,
        top_k=args.top_k,
    )
    canary_verdict = canary_res.get("canary_details", {}).get("overall_verdict", "UNKNOWN")
    print(f"   -> Kết quả Canary Test: {canary_verdict} (Rank: {canary_res.get('hit_rank')})\n")

    if args.canary_only:
        reporter = DebugReporter(session_logger=session_logger, output_dir=args.output_dir)
        reporter.print_console_summary()
        reporter.generate_markdown_report()
        return 0

    # ------------------------------------------------------------------
    # 2. Ad-hoc single query (if provided)
    # ------------------------------------------------------------------
    if args.query:
        print(f"📌 [2/2] Đang thực thi kiểm thử câu hỏi tùy chỉnh: '{args.query}' (Role: {args.role})...")
        case_log = session_logger.create_case_log(
            query_id="CUSTOM_01",
            input_query=args.query,
            user_role=args.role,
            expected_document_id=[],
            expected_keywords=[],
        )
        candidates = hybrid_retriever.search(
            query_text=args.query,
            top_k=args.top_k * 3,
            role=args.role,
        )
        reranked = reranker.rerank(
            query_text=args.query,
            candidates=candidates,
            top_k=args.top_k,
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
        case_log.selected_context = [c.get("content", "") for c in reranked]

        final_answer = ""
        if not args.retrieval_only:
            try:
                from src.services.llm import get_llm

                llm = get_llm()
                prompt_ctx = "\n\n".join(case_log.selected_context)
                system_prompt = f"Bạn là Trợ lý AI VinFast. Hãy trả lời câu hỏi dựa vào Context:\n{prompt_ctx}"
                case_log.final_prompt = system_prompt
                res = llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": args.query},
                ])
                final_answer = getattr(res, "content", str(res))
            except Exception as e:
                final_answer = f"[LLM Error]: {e}"
        case_log.final_answer = final_answer

        case_log.diagnosis = RetrievalDiagnostics.diagnose_case(
            expected_docs=[],
            retrieval_results=case_log.retrieval_results,
            candidates_pre_rerank=candidates,
            selected_context=case_log.selected_context,
            final_answer=final_answer,
            top_k=args.top_k,
        )

    # ------------------------------------------------------------------
    # 3. Ground Truth Dataset evaluation
    # ------------------------------------------------------------------
    else:
        gt_path = Path(args.ground_truth)
        if not gt_path.exists():
            print(f"❌ Không tìm thấy file Ground Truth tại: {gt_path}")
            return 1

        with open(gt_path, encoding="utf-8") as f:
            dataset = json.load(f)

        print(f"📌 [2/2] Đang thực thi kiểm thử trên {len(dataset)} câu hỏi Ground Truth...")

        for idx, item in enumerate(dataset, start=1):
            q_id = item.get("query_id", f"Q{idx:03d}")
            query_text = item["query"]
            user_role = item.get("role", "general")
            exp_docs = item.get("expected_document_id", [])
            exp_keywords = item.get("expected_keywords", [])

            print(f"   [{idx}/{len(dataset)}] Đang xử lý: {q_id} - '{query_text[:40]}...' (Role: {user_role})")

            case_log = session_logger.create_case_log(
                query_id=q_id,
                input_query=query_text,
                user_role=user_role,
                expected_document_id=exp_docs,
                expected_keywords=exp_keywords,
            )

            # 1. Search candidates
            candidates = hybrid_retriever.search(
                query_text=query_text,
                top_k=args.top_k * 3,
                role=user_role,
            )

            # 2. Rerank
            reranked = reranker.rerank(
                query_text=query_text,
                candidates=candidates,
                top_k=args.top_k,
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
            case_log.selected_context = [
                f"[{c.get('metadata', {}).get('document', '')}] {c.get('content', '')}"
                for c in reranked
            ]

            # 3. Optional LLM
            final_answer = ""
            if not args.retrieval_only:
                try:
                    from src.services.llm import get_llm

                    llm = get_llm()
                    prompt_ctx = "\n\n".join(case_log.selected_context)
                    system_prompt = (
                        "Bạn là Trợ lý AI VinFast. Hãy trả lời câu hỏi dựa vào Context bên dưới:\n\n"
                        f"{prompt_ctx}"
                    )
                    case_log.final_prompt = system_prompt
                    res = llm.invoke([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query_text},
                    ])
                    final_answer = getattr(res, "content", str(res))
                except Exception as e:
                    final_answer = f"[LLM Error]: {e}"
            case_log.final_answer = final_answer

            # 4. Diagnose
            case_log.diagnosis = RetrievalDiagnostics.diagnose_case(
                expected_docs=case_log.expected_document_id,
                retrieval_results=case_log.retrieval_results,
                candidates_pre_rerank=candidates,
                selected_context=case_log.selected_context,
                final_answer=final_answer,
                expected_keywords=exp_keywords,
                top_k=args.top_k,
            )

    # ------------------------------------------------------------------
    # 4. Output Reports
    # ------------------------------------------------------------------
    reporter = DebugReporter(session_logger=session_logger, output_dir=args.output_dir)
    reporter.print_console_summary()
    reporter.generate_markdown_report()

    return 0


if __name__ == "__main__":
    sys.exit(run_debugger())
