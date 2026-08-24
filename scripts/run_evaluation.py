import argparse
import json
import logging
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.evaluator import RAGEvaluator
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_evaluation")


def main():
    parser = argparse.ArgumentParser(description="Run Evaluation Suite & Model Benchmark Comparison for RAG Pipeline.")
    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        default="eval/dataset.json",
        help="Path to evaluation test dataset JSON.",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Top-K context documents to evaluate (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="eval/results",
        help="Output directory for evaluation reports (default: eval/results).",
    )

    args = parser.parse_args()

    # Load Stores
    logger.info("Initializing Hybrid Retriever & Cross-Encoder Reranker...")
    vector_store = ChromaVectorStore()
    bm25 = BM25Retriever()
    bm25.load_index()

    hybrid_retriever = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25)
    reranker = RerankerService()

    evaluator = RAGEvaluator(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
        dataset_path=args.dataset,
    )

    logger.info(f"Running evaluation benchmark on dataset: {args.dataset} (Top-K = {args.top_k})")
    metrics = evaluator.evaluate(top_k=args.top_k)

    print("\n" + "=" * 65)
    print("           RAG RETRIEVAL & RERANKING EVALUATION BENCHMARK")
    print("=" * 65)
    print(f" Total Evaluation Queries : {metrics.get('total_queries', 0)}")
    print(f" Top-K Context Window    : {metrics.get('top_k', 5)}")
    print(f" Hit Rate @ K (Recall)   : {metrics.get('hit_rate_at_k', 0.0) * 100:.2f}%")
    print(f" Mean Reciprocal Rank    : {metrics.get('mrr', 0.0):.4f}")
    print(f" Role Access Compliance  : {metrics.get('role_compliance_rate', 0.0) * 100:.2f}%")
    print(f" Table Retrieval Accuracy: {metrics.get('table_retrieval_accuracy', 0.0) * 100:.2f}%")
    print(f" Section Match Accuracy  : {metrics.get('section_match_accuracy', 0.0) * 100:.2f}%")
    print("=" * 65 + "\n")

    # Save output report JSON
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "eval_report.json"
    report_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Saved evaluation report to: {report_path}")


if __name__ == "__main__":
    main()
