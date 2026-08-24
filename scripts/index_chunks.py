import argparse
import json
import logging
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_settings
from src.embedding.embedder import EmbeddingService
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("index_chunks")


def main():
    parser = argparse.ArgumentParser(description="Embed & Index Processed Markdown Chunks into ChromaDB & BM25.")
    parser.add_argument(
        "--chunks-dir",
        "-c",
        type=str,
        help="Directory containing chunk JSON files (defaults to data/processed/chunks).",
    )
    parser.add_argument(
        "--embedding-model",
        "-m",
        type=str,
        default="BAAI/bge-m3",
        help="Embedding model name (default: BAAI/bge-m3).",
    )

    args = parser.parse_args()
    settings = get_settings()

    chunks_dir = Path(args.chunks_dir or (Path(settings.processed_data_dir) / "chunks"))
    if not chunks_dir.exists():
        logger.error(f"Chunks directory does not exist: {chunks_dir}")
        sys.exit(1)

    logger.info(f"Scanning for chunk JSON files in: {chunks_dir}")
    all_chunks = []

    for json_path in chunks_dir.rglob("*.json"):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                all_chunks.extend(data)
        except Exception as e:
            logger.error(f"Error loading chunk JSON file {json_path}: {e}")

    logger.info(f"Total chunks collected across all files: {len(all_chunks)}")

    if not all_chunks:
        logger.warning("No chunks found to index.")
        return

    # 1. Embed & Index into ChromaDB
    embedder = EmbeddingService(model_name=args.embedding_model)
    vector_store = ChromaVectorStore(embedder=embedder)
    vector_store.reset()
    indexed_vector_count = vector_store.add_chunks(all_chunks)

    # 2. Build BM25 Index
    bm25 = BM25Retriever()
    indexed_bm25_count = bm25.build_index(all_chunks)

    logger.info(
        f"INDEXING COMPLETE!\n"
        f"- ChromaDB Vector Store: {indexed_vector_count} chunks indexed\n"
        f"- BM25 Index: {indexed_bm25_count} chunks indexed\n"
        f"- Embedding Model: {args.embedding_model}"
    )


if __name__ == "__main__":
    main()
