"""
eval/ragas_baseline.py
Chạy RAGAS evaluation để đo baseline chất lượng RAG pipeline.

Metrics đo:
- context_precision: Tỷ lệ chunk retrieved thực sự hữu ích
- faithfulness:      LLM có hallucinate ngoài context không?
- answer_relevancy:  Câu trả lời có đúng với câu hỏi không?

Cách chạy:
    python eval/ragas_baseline.py
    python eval/ragas_baseline.py --sample 10   # chỉ test 10 câu
    python eval/ragas_baseline.py --output-json eval/results/ragas_baseline.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("APP_ENV", "development")

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from src.agents.nodes.rag_node import build_rag_context
from src.config import get_settings
from src.vectordb.hybrid_search import HybridSearcher

settings = get_settings()

# ─── Config ────────────────────────────────────────────────────────────────────
GROUND_TRUTH_PATH = Path("retrieval_debugger/ground_truth.json")
RESULTS_DIR = Path("eval/results")
TOP_K = 5  # số chunks retrieve


def load_ground_truth(sample: int | None = None) -> list[dict]:
    data = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    # Bỏ qua out_of_scope cases (không có expected answer)
    data = [d for d in data if d.get("query_type") != "out_of_scope"]
    if sample:
        data = data[:sample]
    return data


def retrieve_contexts(query: str, role: str, top_k: int = TOP_K) -> list[str]:
    """Retrieve top-K chunks từ HybridSearcher."""
    try:
        searcher = HybridSearcher()
        results = searcher.search(query=query, role=role, top_k=top_k)
        return [r.get("content", r.get("raw_content", "")) for r in results]
    except Exception as e:
        print(f"  [WARN] Retrieval failed for '{query[:50]}': {e}")
        return []


def generate_answer(query: str, contexts: list[str]) -> str:
    """Gọi LLM để sinh câu trả lời từ contexts (dùng OpenAI qua LangChain)."""
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            openai_api_key=settings.openai_api_key,
        )
        context_text = "\n\n---\n\n".join(contexts[:3])
        prompt = (
            f"Dựa vào tài liệu sau, trả lời câu hỏi ngắn gọn bằng tiếng Việt:\n\n"
            f"TÀI LIỆU:\n{context_text}\n\n"
            f"CÂU HỎI: {query}\n\n"
            f"TRẢ LỜI:"
        )
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"  [WARN] LLM failed: {e}")
        return "Không thể tạo câu trả lời."


def main():
    parser = argparse.ArgumentParser(description="Run RAGAS baseline evaluation")
    parser.add_argument("--sample", "-n", type=int, default=None,
                        help="Số câu hỏi để test (mặc định: toàn bộ)")
    parser.add_argument("--output-json", type=str,
                        default=None, help="Path lưu kết quả JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("  RAGAS BASELINE EVALUATION")
    print("=" * 60)

    ground_truth_items = load_ground_truth(sample=args.sample)
    print(f"  Evaluating {len(ground_truth_items)} questions...")

    # ─── Build RAGAS dataset ──────────────────────────────────────────
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []

    for i, item in enumerate(ground_truth_items, 1):
        query = item["query"]
        role = item.get("role", "general")
        gt_answer = item.get("expected_answer", "")

        print(f"  [{i:02d}/{len(ground_truth_items)}] {query[:60]}...")

        # 1. Retrieve
        ctxs = retrieve_contexts(query, role)
        if not ctxs:
            ctxs = ["Không tìm thấy tài liệu liên quan."]

        # 2. Generate answer
        answer = generate_answer(query, ctxs)

        questions.append(query)
        answers.append(answer)
        contexts_list.append(ctxs)
        ground_truths.append(gt_answer)

    # ─── Run RAGAS ────────────────────────────────────────────────────
    print("\n  Running RAGAS metrics...")
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })

    result = evaluate(
        dataset=dataset,
        metrics=[context_precision, faithfulness, answer_relevancy],
        raise_exceptions=False,
    )

    # ─── Report ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RAGAS BASELINE RESULTS")
    print("=" * 60)
    print(f"  Context Precision : {result['context_precision']:.4f}")
    print(f"  Faithfulness      : {result['faithfulness']:.4f}")
    print(f"  Answer Relevancy  : {result['answer_relevancy']:.4f}")
    print("=" * 60)

    # ─── Targets ──────────────────────────────────────────────────────
    targets = {
        "context_precision": 0.70,
        "faithfulness": 0.85,
        "answer_relevancy": 0.80,
    }
    print("\n  Target vs Actual:")
    for metric, target in targets.items():
        actual = result[metric]
        status = "PASS" if actual >= target else "FAIL"
        diff = actual - target
        print(f"  {metric:25s}: {actual:.4f} (target={target:.2f}, {status:4s}, diff={diff:+.4f})")

    # ─── Save JSON ────────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.output_json) if args.output_json else RESULTS_DIR / f"ragas_{ts}.json"

    output = {
        "timestamp": ts,
        "n_questions": len(questions),
        "metrics": {
            "context_precision": float(result["context_precision"]),
            "faithfulness": float(result["faithfulness"]),
            "answer_relevancy": float(result["answer_relevancy"]),
        },
        "targets": targets,
        "pass": all(result[m] >= t for m, t in targets.items()),
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Results saved -> {out_path}")

    return 0 if output["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
