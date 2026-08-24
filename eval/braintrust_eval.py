"""Braintrust Evaluation Framework for RAG Pipeline & Agent Responses.

Runs experiments via Braintrust Eval() and logs metrics, traces, and scores
directly to the Braintrust dashboard.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import braintrust
from autoevals import Levenshtein

from src.agents.graph import agent
from src.config import get_settings
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("braintrust_eval")


def recall_at_k_scorer(output: dict[str, Any], expected: list[str]) -> float:
    """Check if any expected document ID is in retrieved citations/documents."""
    retrieved_docs = output.get("retrieved_docs", [])
    citations = output.get("citations", [])

    all_retrieved = []
    for d in retrieved_docs:
        all_retrieved.append(str(d.get("document_id", "")))
        all_retrieved.append(str(d.get("chunk_id", "")))
        all_retrieved.append(str(d.get("source", "")))
        all_retrieved.append(str(d.get("content", "")))
    for c in citations:
        all_retrieved.append(str(c))

    combined = " ".join(all_retrieved).lower()
    for exp in expected:
        if exp.lower() in combined:
            return 1.0
    return 0.0


def mrr_scorer(output: dict[str, Any], expected: list[str]) -> float:
    """Mean Reciprocal Rank scorer."""
    retrieved_docs = output.get("retrieved_docs", [])
    for rank, doc in enumerate(retrieved_docs, start=1):
        doc_id = str(doc.get("document_id", "")).lower()
        chunk_id = str(doc.get("chunk_id", "")).lower()
        source = str(doc.get("source", "")).lower()
        for exp in expected:
            if exp.lower() in doc_id or exp.lower() in chunk_id or exp.lower() in source:
                return 1.0 / rank
    return 0.0


def role_compliance_scorer(output: dict[str, Any], unauthorized_roles: list[str] | None) -> float:
    """Ensure no unauthorized role documents are leaked."""
    if not unauthorized_roles:
        return 1.0
    retrieved_docs = output.get("retrieved_docs", [])
    for doc in retrieved_docs:
        doc_role = doc.get("role", "")
        if doc_role in unauthorized_roles:
            return 0.0
    return 1.0


def run_braintrust_evaluation(
    dataset_path: str = "eval/dataset.json",
    experiment_name: str | None = None,
    limit: int | None = None,
) -> Any:
    """Run evaluation and push results to Braintrust."""
    settings = get_settings()
    api_key = settings.braintrust_api_key or os.environ.get("BRAINTRUST_API_KEY")
    project = settings.braintrust_project_name or os.environ.get("BRAINTRUST_PROJECT_NAME", "p223-agent")

    if not api_key:
        raise ValueError("BRAINTRUST_API_KEY is not configured in .env or settings!")

    # Set environment variables for Braintrust
    os.environ["BRAINTRUST_API_KEY"] = api_key

    # Load dataset
    p = Path(dataset_path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    if limit:
        data = data[:limit]

    logger.info(f"Loaded {len(data)} test cases from {dataset_path}")

    # Initialize RAG components
    logger.info("Initializing Vector Stores and Hybrid Retriever...")
    vector_store = ChromaVectorStore()
    bm25 = BM25Retriever()
    bm25.load_index()
    hybrid_retriever = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25)
    reranker = RerankerService()

    async def task(input_data: dict[str, Any]) -> dict[str, Any]:
        """Task function executed for each evaluation sample (async)."""
        query = input_data["query"]
        role = input_data.get("role", "general")

        # 1. Retrieval Pass
        retrieved = hybrid_retriever.search(query_text=query, top_k=10, role=role)
        reranked = reranker.rerank(query_text=query, candidates=retrieved, top_k=5)

        # 2. Agent Graph Execution
        try:
            agent_result = await agent.ainvoke(
                {
                    "raw_query": query,
                    "query": query,
                    "user_role": role,
                    "session_id": f"eval_{input_data.get('query_id', '000')}",
                }
            )
            answer = agent_result.get("response", agent_result.get("final_response", ""))
            citations = agent_result.get("citations", [])
            intent = agent_result.get("intent", "UNKNOWN")
        except Exception as e:
            logger.warning(f"Graph execution failed for query '{query}': {e}")
            answer = ""
            citations = []
            intent = "ERROR"

        return {
            "answer": answer,
            "citations": citations,
            "intent": intent,
            "retrieved_docs": [
                {
                    "chunk_id": doc.get("chunk_id", ""),
                    "document_id": doc.get("metadata", {}).get("document_id", doc.get("document_id", "")),
                    "source": doc.get("metadata", {}).get("source_path", doc.get("source", "")),
                    "role": doc.get("metadata", {}).get("role", "") if isinstance(doc.get("metadata"), dict) else "",
                    "content": doc.get("content", "")[:200],
                    "score": doc.get("rerank_score", doc.get("rrf_score", 0.0)),
                }
                for doc in reranked
            ],
        }

    # Format dataset for Braintrust Eval
    eval_data = [
        {
            "input": {
                "query": item["query"],
                "role": item.get("role", "general"),
                "query_id": item.get("query_id", ""),
            },
            "expected": item.get("expected_answer", ""),
            "metadata": {
                "query_id": item.get("query_id", ""),
                "expected_document_id": item.get("expected_document_id", []),
                "expected_section": item.get("expected_section", ""),
                "unauthorized_roles": item.get("unauthorized_roles", []),
                "query_type": item.get("query_type", "text"),
            },
        }
        for item in data
    ]

    # Define Scorers
    def eval_recall(output, metadata):
        return {
            "name": "Recall@5",
            "score": recall_at_k_scorer(output, metadata.get("expected_document_id", [])),
        }

    def eval_mrr(output, metadata):
        return {
            "name": "MRR",
            "score": mrr_scorer(output, metadata.get("expected_document_id", [])),
        }

    def eval_role_isolation(output, metadata):
        return {
            "name": "RoleIsolation",
            "score": role_compliance_scorer(output, metadata.get("unauthorized_roles")),
        }

    def eval_levenshtein(output, expected):
        if not expected or not output.get("answer"):
            return {"name": "Levenshtein", "score": 0.5}
        try:
            return Levenshtein(output=output["answer"], expected=expected)
        except Exception:
            return {"name": "Levenshtein", "score": 0.5}

    logger.info(f"Starting Braintrust Eval in project '{project}'...")
    summary = braintrust.Eval(
        project,
        data=eval_data,
        task=task,
        scores=[eval_recall, eval_mrr, eval_role_isolation, eval_levenshtein],
        experiment_name=experiment_name,
    )

    logger.info("Braintrust Evaluation Completed Successfully!")
    return summary


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Run Braintrust RAG Evaluation.")
    parser.add_argument("--dataset", "-d", type=str, default="eval/dataset.json", help="Path to test dataset.")
    parser.add_argument("--experiment-name", "-e", type=str, default=None, help="Custom experiment name.")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limit number of test cases.")
    args = parser.parse_args()

    summary = run_braintrust_evaluation(
        dataset_path=args.dataset,
        experiment_name=args.experiment_name,
        limit=args.limit,
    )
    print("\n--- Evaluation Summary ---")
    try:
        print(summary)
    except Exception:
        print(f"Scores: {getattr(summary, 'scores', 'Completed')}")


if __name__ == "__main__":
    main()
