"""
run_benchmark.py
================
Chay benchmark RAG pipeline va in bang so sanh ket qua.

Su dung:
    python scripts/run_benchmark.py
    python scripts/run_benchmark.py --save-report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.evaluator import RAGEvaluator


def parse_args():
    parser = argparse.ArgumentParser(description="Chay benchmark RAG pipeline.")
    parser.add_argument("--top-k", type=int, default=5, help="Top K de retrieve (mac dinh: 5)")
    parser.add_argument("--save-report", action="store_true", help="Luu ket qua vao eval/reports/")
    parser.add_argument(
        "--dataset",
        type=str,
        default="./eval/dataset.json",
        help="Duong dan file dataset (mac dinh: ./eval/dataset.json)",
    )
    return parser.parse_args()


def print_report(metrics: dict) -> None:
    print("\n" + "=" * 65)
    print("  KET QUA BENCHMARK RAG")
    print("=" * 65)
    print(f"  Embedding model : {metrics.get('embedding_model', 'unknown')}")
    dim = metrics.get("embedding_dim")
    if dim:
        print(f"  Vector dims     : {dim}")
    cfg = metrics.get("chunk_config", {})
    if cfg:
        print(
            f"  Chunk config    : {cfg.get('min_tokens')}-{cfg.get('max_tokens')} tokens, overlap={cfg.get('overlap_tokens')}"
        )
    print("-" * 65)
    print(f"  Total queries   : {metrics.get('total_queries', 0)}")
    print(f"  Top-K           : {metrics.get('top_k', 5)}")
    print("-" * 65)

    hr = metrics.get("hit_rate_at_k", 0)
    mrr = metrics.get("mrr", 0)
    rc = metrics.get("role_compliance_rate", 0)
    ta = metrics.get("table_retrieval_accuracy", 0)
    sa = metrics.get("section_match_accuracy", 0)

    print(f"  Hit Rate@K      : {hr:.4f}  ({hr * 100:.1f}%)")
    print(f"  MRR             : {mrr:.4f}  ({mrr * 100:.1f}%)")
    print(f"  Role Compliance : {rc:.4f}  ({rc * 100:.1f}%)")
    print(f"  Table Accuracy  : {ta:.4f}  ({ta * 100:.1f}%)")
    print(f"  Section Match   : {sa:.4f}  ({sa * 100:.1f}%)")
    print("=" * 65 + "\n")


def main():
    args = parse_args()

    if not Path(args.dataset).exists():
        print(f"[WARN] Khong tim thay dataset: {args.dataset}")
        print("       Tao file eval/dataset.json truoc de chay benchmark.")
        print("       Xem eval/dataset.json.example de biet dinh dang.\n")
        sys.exit(0)

    print(f"\nDang chay benchmark voi dataset: {args.dataset}")
    t0 = time.time()

    evaluator = RAGEvaluator(dataset_path=args.dataset)
    metrics = evaluator.evaluate(top_k=args.top_k)

    elapsed = time.time() - t0
    print(f"Hoan thanh trong {elapsed:.1f}s\n")

    print_report(metrics)

    if args.save_report:
        report_dir = Path("eval/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        report_path = report_dir / f"benchmark_{ts}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            # Bỏ query_details để file gọn hơn khi in
            summary = {k: v for k, v in metrics.items() if k != "query_details"}
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"Da luu report: {report_path}\n")


if __name__ == "__main__":
    main()
