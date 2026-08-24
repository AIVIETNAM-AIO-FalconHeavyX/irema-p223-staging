import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pickle

import chromadb


def check_fast():
    print("=== 1. CHATBOT VECTOR DATABASE (ChromaDB) ===", flush=True)
    chroma_dir = Path("./data/chroma")
    print(f"Path: {chroma_dir.resolve()}", flush=True)
    if chroma_dir.exists():
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = client.list_collections()
        print("Trạng thái: ĐÃ KẾT NỐI", flush=True)
        print(f"Số lượng Collections: {len(collections)}", flush=True)
        total_chunks = 0
        for col in collections:
            count = col.count()
            total_chunks += count
            print(f"  + Collection '{col.name}': {count} chunks dữ liệu vector", flush=True)
            if count > 0:
                sample = col.peek(limit=2)
                print(f"    * Sample Chunk IDs: {sample['ids']}", flush=True)
                for i, meta in enumerate(sample["metadatas"]):
                    print(
                        f"      - Chunk {sample['ids'][i]}: role={meta.get('role')}, source={meta.get('source_file')}",
                        flush=True,
                    )
    else:
        print("Trạng thái: THƯ MỤC CHROMA CHƯA TỒN TẠI", flush=True)

    print("\n=== 2. CHATBOT KEYWORD SEARCH (BM25 Index) ===", flush=True)
    bm25_file = Path("./data/bm25_index.pkl")
    if bm25_file.exists():
        with open(bm25_file, "rb") as f:
            data = pickle.load(f)
            chunks = data.get("chunks", []) if isinstance(data, dict) else data
            print("Trạng thái: ĐÃ KẾT NỐI", flush=True)
            print(f"Dung lượng index file: {bm25_file.stat().st_size / 1024:.1f} KB", flush=True)
            print(f"Tổng số văn bản/chunks trong BM25: {len(chunks)}", flush=True)
            if chunks:
                first = chunks[0]
                print(
                    f"    * Mẫu Document 1: id={first.get('chunk_id')}, source={first.get('metadata', {}).get('source_file')}",
                    flush=True,
                )
    else:
        print("Trạng thái: FILE BM25 CHƯA TỒN TẠI", flush=True)

    print("\n=== 3. KHO TÀI LIỆU RAW & PROCESSED ===", flush=True)
    raw_dir = Path("./data/raw")
    proc_dir = Path("./data/processed")
    if raw_dir.exists():
        raw_files = list(raw_dir.rglob("*.*"))
        print(f"Tài liệu gốc (data/raw): {len(raw_files)} files", flush=True)
    if proc_dir.exists():
        proc_files = list(proc_dir.rglob("*.md"))
        print(f"Tài liệu đã tiền xử lý sạch PII (data/processed): {len(proc_files)} file Markdown", flush=True)
        for folder in proc_dir.iterdir():
            if folder.is_dir():
                md_count = len(list(folder.glob("*.md")))
                print(f"  + Thư mục {folder.name}: {md_count} files", flush=True)

    print("\n=== 4. CẤU HÌNH API LLM ===", flush=True)
    from src.config import get_settings

    s = get_settings()
    has_openai = bool(s.openai_api_key and s.openai_api_key.strip())
    has_gemini = bool(s.google_api_key and s.google_api_key.strip())
    print(f"OpenAI API Key: {'Đã cấu hình' if has_openai else 'Chưa cấu hình'}", flush=True)
    print(f"Google Gemini API Key: {'Đã cấu hình' if has_gemini else 'Chưa cấu hình'}", flush=True)
    print(f"Mô hình sử dụng: {s.model_name} (OpenAI) / {s.gemini_model_name} (Gemini)", flush=True)


if __name__ == "__main__":
    check_fast()
