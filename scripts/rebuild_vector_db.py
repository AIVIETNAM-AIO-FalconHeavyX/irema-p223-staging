"""
rebuild_vector_db.py — Rebuild toàn bộ ChromaDB + BM25 với embedding model mới.

Các bước:
1. Xóa data/chroma/ (ChromaDB cũ)
2. Xóa data/bm25_index.pkl (BM25 cũ)
3. Đọc chunk JSON từ data/processed/chunks/
4. Embed lại bằng BAAI/bge-m3
5. Index vào ChromaDB + BM25 mới
6. In báo cáo

Sử dụng:
    python scripts/rebuild_vector_db.py
    python scripts/rebuild_vector_db.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_settings
from src.embedding.embedder import EmbeddingService
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rebuild_vector_db")


def parse_args():
    parser = argparse.ArgumentParser(description="Rebuild ChromaDB + BM25 với model mới.")
    parser.add_argument("--embedding-model", "-m", default="BAAI/bge-m3")
    parser.add_argument("--chunks-dir", "-c", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Chỉ đếm, không xóa/embed")
    parser.add_argument("--keep-chroma", action="store_true", help="Chỉ rebuild BM25")
    return parser.parse_args()


def load_chunks(chunks_dir: Path) -> list[dict]:
    all_chunks = []
    json_files = list(chunks_dir.rglob("*.json"))
    logger.info(f"Tìm thấy {len(json_files)} file JSON trong {chunks_dir}")
    for jp in json_files:
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            if isinstance(data, list):
                all_chunks.extend(data)
            elif isinstance(data, dict) and "chunk_id" in data:
                all_chunks.append(data)
        except Exception as e:
            logger.error(f"Lỗi đọc {jp.name}: {e}")
    return all_chunks


def delete_old_data(settings, keep_chroma: bool) -> None:
    bm25_path = Path(getattr(settings, "bm25_index_path", "./data/bm25_index.pkl"))
    if bm25_path.exists():
        bm25_path.unlink()
        logger.info(f"Đã xóa BM25: {bm25_path}")

    if not keep_chroma:
        chroma_dir = Path(settings.chroma_persist_dir)
        if chroma_dir.exists():
            # Dùng ChromaDB API thay vì shutil.rmtree để tránh WinError 32
            # khi backend uvicorn đang giữ file lock trên Windows
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(chroma_dir))
                collection_name = getattr(settings, "chroma_collection_name", "rag_chunks")
                try:
                    client.delete_collection(collection_name)
                    logger.info(f"Đã xóa ChromaDB collection '{collection_name}'")
                except Exception:
                    logger.info("Collection chưa tồn tại, bỏ qua bước xóa.")
            except Exception as e:
                logger.warning(f"ChromaDB API delete failed, fallback to rmtree: {e}")
                shutil.rmtree(chroma_dir)
            logger.info(f"ChromaDB tại '{chroma_dir}' đã được reset.")


def main():
    args = parse_args()
    settings = get_settings()
    chunks_dir = Path(args.chunks_dir or (Path(settings.processed_data_dir) / "chunks"))

    print("\n" + "=" * 60)
    print("  REBUILD VECTOR DB")
    print("=" * 60)
    print(f"  Model    : {args.embedding_model}")
    print(f"  Chunks   : {chunks_dir}")
    print(f"  Dry run  : {args.dry_run}")
    print("=" * 60 + "\n")

    if not chunks_dir.exists():
        logger.error(f"Không tìm thấy: {chunks_dir}")
        logger.error("Chạy 'python -m scripts.run_markdown_pipeline' trước.")
        sys.exit(1)

    t0 = time.time()
    all_chunks = load_chunks(chunks_dir)
    if not all_chunks:
        logger.warning("Không có chunk nào.")
        sys.exit(0)

    logger.info(f"Tổng số chunks: {len(all_chunks)}")

    if args.dry_run:
        print(f"\n[DRY RUN] Sẽ embed {len(all_chunks)} chunks với {args.embedding_model}")
        return

    print("\n Xóa dữ liệu cũ...")
    delete_old_data(settings, keep_chroma=args.keep_chroma)

    print(f"\n Tải embedding model: {args.embedding_model}")
    print("   (Lần đầu ~2.3GB, 5-10 phút...)\n")
    embedder = EmbeddingService(model_name=args.embedding_model)

    print(f"\n Indexing {len(all_chunks)} chunks vào ChromaDB...")
    vector_store = ChromaVectorStore(embedder=embedder)
    indexed_chroma = vector_store.add_chunks(all_chunks)

    print("\n Building BM25 index...")
    bm25 = BM25Retriever()
    indexed_bm25 = bm25.build_index(all_chunks)

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("  REBUILD HOÀN THÀNH")
    print("=" * 60)
    print(f"  ChromaDB : {indexed_chroma} chunks")
    print(f"  BM25     : {indexed_bm25} chunks")
    print(f"  Model    : {embedder.model_name} ({embedder.embedding_dim} dims)")
    print(f"  Thời gian: {elapsed:.1f}s ({elapsed / 60:.1f} phút)")
    print("=" * 60)
    print("\nChạy 'python scripts/run_benchmark.py' để đo chất lượng.\n")


if __name__ == "__main__":
    main()
