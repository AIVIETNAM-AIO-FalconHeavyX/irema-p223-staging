import json
import logging
import re
import sys
from pathlib import Path

import yaml

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cloud.s3_service import s3_service
from src.config import get_settings
from src.db import SessionLocal
from src.db.models import OnboardingStep
from src.embedding.embedder import EmbeddingService
from src.preprocess.cleaner import TextCleaner
from src.preprocess.structure_aware_chunker import StructureAwareChunker
from src.preprocess.structure_normalizer import StructureNormalizer
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


def split_frontmatter(content: str) -> tuple[dict, str]:
    """
    Tách YAML frontmatter khỏi Markdown content.

    Input:
        ---
        document_id: xxx
        title: xxx
        role: Sale
        source_path: xxx
        ---

        # Content

    Output:
        metadata, body
    """

    if content.startswith("---"):
        parts = content.split("---", 2)

        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()

                if not isinstance(metadata, dict):
                    metadata = {}

                return metadata, body

            except yaml.YAMLError as e:
                logger.warning(f"Không thể parse YAML frontmatter: {e}")

    return {}, content.strip()


def process_markdown(
    file_path: Path,
) -> tuple[Path, list[dict]] | None:
    """
    Đọc Markdown từ data/processed/markdown/.

    Returns:
        (file_path, chunks)
    """

    try:
        content = file_path.read_text(encoding="utf-8")

        # ---------------------------------------------------------
        # 1. Parse frontmatter
        # ---------------------------------------------------------
        frontmatter, body_text = split_frontmatter(content)

        doc_id = frontmatter.get(
            "document_id",
            TextCleaner.normalize_filename(file_path.stem).upper(),
        )

        title = frontmatter.get(
            "title",
            file_path.stem.replace("_", " ").title(),
        )

        role = frontmatter.get(
            "role",
            "general",
        )

        source = frontmatter.get(
            "source_path",
            frontmatter.get(
                "source_file",
                file_path.name,
            ),
        )

        # ---------------------------------------------------------
        # 2. Markdown body
        # ---------------------------------------------------------
        cleaned_body = body_text

        # ---------------------------------------------------------
        # 3. Structure normalization
        # ---------------------------------------------------------
        normalized_body = StructureNormalizer.normalize_headings(cleaned_body)

        sections = StructureNormalizer.parse_structure(normalized_body)

        # ---------------------------------------------------------
        # 4. Structure-aware Chunking
        # ---------------------------------------------------------
        clean_stem = TextCleaner.normalize_filename(file_path.stem)

        unique_doc_prefix = f"{doc_id}_{clean_stem}"

        chunks = StructureAwareChunker.chunk_sections(
            sections=sections,
            document_id=unique_doc_prefix,
            title=title,
            role=role,
            source=source,
        )

        chunks_dict = [chunk.to_dict() for chunk in chunks]

        logger.info(f"Chunked: {file_path.name} -> {len(chunks_dict)} chunks")

        return file_path, chunks_dict

    except Exception as e:
        logger.error(
            f"Lỗi xử lý cleaned Markdown {file_path}: {e}",
            exc_info=True,
        )
        return None


def run_ingestion_pipeline(
    file_target: str | Path | None = None,
    role_filter: str | None = None,
    reset: bool = False,
    upload_minio: bool = True,
):
    """
    RAG Ingestion Pipeline.

    INPUT:
        data/processed/markdown/

    Pipeline:

        markdown
                ↓
        Parse Frontmatter
                ↓
        Structure Normalization
                ↓
        Structure-aware Chunking
                ↓
        chunks/*.json
                ↓
        Embedding
                ↓
        ChromaDB
                +
        BM25
                +
        MinIO
                +
        PostgreSQL / SQLite
    """

    settings = get_settings()

    # ============================================================
    # 1. INPUT = MARKDOWN
    # ============================================================

    md_dir = Path(settings.processed_data_dir) / "markdown"

    if not md_dir.exists():
        logger.error(f"Thư mục markdown không tồn tại: {md_dir}")
        return

    logger.info("=================================================================")
    logger.info("🚀 BẮT ĐẦU RAG INGESTION PIPELINE" + (f" (Incremental File: {file_target})" if file_target else ""))
    logger.info("📥 INPUT: markdown/")
    logger.info("=================================================================")

    # ============================================================
    # 2. Ensure MinIO bucket
    # ============================================================

    if upload_minio:
        logger.info("☁️ Kiểm tra MinIO bucket...")
        s3_service.ensure_bucket_exists()

    # ============================================================
    # 3. Process MARKDOWN → CHUNKS
    # ============================================================

    chunks_dir = Path(settings.processed_data_dir) / "chunks"

    chunks_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Locate markdown files to process
    target_files: list[Path] = []
    if file_target:
        candidate = Path(file_target)
        if candidate.is_file():
            target_files = [candidate]
        else:
            search_name = candidate.name
            if not search_name.endswith(".md"):
                search_name = candidate.stem + ".md"
            found = list(md_dir.rglob(search_name))
            if not found:
                norm_stem = TextCleaner.normalize_filename(candidate.stem)
                found = [f for f in md_dir.rglob("*.md") if TextCleaner.normalize_filename(f.stem) == norm_stem]
            if not found:
                logger.error(f"❌ Không tìm thấy file markdown tương ứng với '{file_target}' trong {md_dir}")
                return
            target_files = found
            logger.info(f"🎯 Tìm thấy {len(target_files)} file markdown tương ứng: {[f.name for f in target_files]}")
    else:
        target_files = list(md_dir.rglob("*.md"))

    logger.info(f"📂 Đọc Markdown từ: {md_dir} ({len(target_files)} files)")

    all_chunks: list[dict] = []

    processed_files = 0
    failed_files = 0

    # ============================================================
    # Scan & Chunk targeted markdown files
    # ============================================================

    for md_file in target_files:
        result = process_markdown(md_file)

        if not result:
            failed_files += 1
            continue

        file_path, chunks = result

        # --------------------------------------------------------
        # Role filtering
        # --------------------------------------------------------

        if role_filter:
            chunks = [
                chunk for chunk in chunks if (chunk.get("metadata", {}).get("role", "").lower() == role_filter.lower())
            ]

        # --------------------------------------------------------
        # Save chunks JSON
        # --------------------------------------------------------

        try:
            relative_path = md_file.relative_to(md_dir)

            output_chunk_path = chunks_dir / relative_path.with_suffix(".json")

            output_chunk_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_chunk_path.write_text(
                json.dumps(
                    chunks,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        except Exception as e:
            logger.error(f"Không thể ghi chunks cho {md_file}: {e}")
            failed_files += 1
            continue

        all_chunks.extend(chunks)
        processed_files += 1

    logger.info(f"✅ Đã xử lý {processed_files} Markdown files.")

    logger.info(f"⚠️ File lỗi: {failed_files}")

    logger.info(f"🧩 Tổng số chunks mới/cập nhật: {len(all_chunks)}")

    # ============================================================
    # 4. Upload MARKDOWN lên MinIO
    # ============================================================

    uploaded_minio_count = 0
    file_to_s3_url: dict[str, str] = {}

    if upload_minio:
        logger.info("☁️ Upload Markdown lên MinIO...")

        for md_file in target_files:
            try:
                rel_path = md_file.relative_to(md_dir)

                role_folder = rel_path.parent.name if rel_path.parent.name else "general"

                # Chuẩn hóa role cho S3
                role_key = settings.role_mapping.get(
                    role_folder,
                    role_folder.lower(),
                )

                object_key = s3_service.upload_processed_md(
                    local_path=str(md_file),
                    role=role_key,
                    filename=md_file.name,
                )

                s3_url = s3_service.get_public_url(object_key)

                file_to_s3_url[md_file.stem.lower()] = s3_url

                uploaded_minio_count += 1

            except Exception as e:
                logger.warning(f"Không thể upload {md_file.name} lên MinIO: {e}")

        logger.info(f"✅ Đã upload {uploaded_minio_count} cleaned Markdown files.")

    # ============================================================
    # 5. UPDATE POSTGRESQL / SQLITE
    # ============================================================

    logger.info("🐘 Đồng bộ processed_md_url vào Database...")

    db = SessionLocal()

    updated_steps = 0

    try:
        steps = db.query(OnboardingStep).all()

        for step in steps:
            step_title_clean = (
                re.sub(
                    r"[^\w\s-]",
                    "",
                    step.title or "",
                )
                .strip()
                .replace(
                    " ",
                    "_",
                )
                .lower()
            )

            matched_url = None

            # ----------------------------------------------------
            # Match theo Step title
            # ----------------------------------------------------

            for stem_key, url in file_to_s3_url.items():
                if stem_key in step_title_clean or step_title_clean in stem_key:
                    matched_url = url
                    break

            # ----------------------------------------------------
            # Match theo resources
            # ----------------------------------------------------

            if not matched_url and step.resources:
                for res in step.resources:
                    res_name = res.get("name", "").lower()

                    for stem_key, url in file_to_s3_url.items():
                        if stem_key in res_name or res_name in stem_key:
                            matched_url = url
                            break

                    if matched_url:
                        break

            # ----------------------------------------------------
            # Update DB
            # ----------------------------------------------------

            if matched_url and step.processed_md_url != matched_url:
                step.processed_md_url = matched_url

                db.add(step)

                updated_steps += 1

                logger.info(f"🔗 Step [{step.id}] {step.title} -> {matched_url}")

        db.commit()

        logger.info(f"✅ Đã cập nhật {updated_steps} onboarding steps.")

    except Exception as e:
        logger.error(
            f"Lỗi cập nhật Database: {e}",
            exc_info=True,
        )

        db.rollback()

    finally:
        db.close()

    # ============================================================
    # 6. EMBEDDING + CHROMADB + BM25
    # ============================================================

    if not all_chunks:
        logger.warning("Không có chunks để index.")

        return

    logger.info("🧠 Bắt đầu Embedding + ChromaDB...")

    # ------------------------------------------------------------
    # Embedding model
    # ------------------------------------------------------------

    embedding_model = getattr(
        settings,
        "embedding_model",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    logger.info(f"🔤 Embedding model: {embedding_model}")

    embedder = EmbeddingService(model_name=embedding_model)

    # ------------------------------------------------------------
    # ChromaDB
    # ------------------------------------------------------------

    vector_store = ChromaVectorStore(embedder=embedder)

    if reset and not file_target:
        logger.info("🔄 Reset ChromaDB collection...")

        vector_store.reset()

    elif file_target:
        # Xóa các chunk cũ của file này trước khi add mới
        seen_sources = set()
        seen_doc_ids = set()
        for chunk in all_chunks:
            meta = chunk.get("metadata", {})
            src = meta.get("source")
            doc_id = meta.get("document_id")
            if src and src not in seen_sources:
                vector_store.delete_by_source(src)
                seen_sources.add(src)
            if doc_id and doc_id not in seen_doc_ids:
                vector_store.delete_by_document_id(doc_id)
                seen_doc_ids.add(doc_id)

    indexed_vector = vector_store.add_chunks(all_chunks)

    # ============================================================
    # 7. BM25
    # ============================================================

    logger.info("📚 Xây dựng BM25 index...")

    bm25 = BM25Retriever()

    if file_target:
        all_corpus_chunks = []
        for chunk_file in chunks_dir.rglob("*.json"):
            try:
                data = json.loads(chunk_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    all_corpus_chunks.extend(data)
            except Exception as e:
                logger.warning(f"Không thể đọc chunk {chunk_file}: {e}")
        indexed_bm25 = bm25.build_index(all_corpus_chunks)
    else:
        indexed_bm25 = bm25.build_index(all_chunks)

    # ============================================================
    # 8. SUMMARY
    # ============================================================

    logger.info(
        "\n"
        "=================================================================\n"
        "🎉 HOÀN TẤT RAG INGESTION PIPELINE!\n"
        "-----------------------------------------------------------------\n"
        f"📥 Input cleaned Markdown:       {processed_files}\n"
        f"🧩 Total chunks processed:       {len(all_chunks)}\n"
        f"☁️ MinIO uploaded:              {uploaded_minio_count}\n"
        f"🐘 Database updated:             {updated_steps}\n"
        f"🧠 ChromaDB indexed:            {indexed_vector}\n"
        f"📚 BM25 indexed:                {indexed_bm25}\n"
        f"🔤 Embedding model:             {embedding_model}\n"
        "=================================================================\n"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "RAG Ingestion Pipeline (Cleaned Markdown -> Chunking -> Embedding -> ChromaDB/BM25 -> MinIO/PostgreSQL)"
        )
    )

    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help=("Chỉ index một file cụ thể (tên file hoặc đường dẫn markdown/raw)"),
    )

    parser.add_argument(
        "--role",
        type=str,
        default=None,
        help=("Chỉ index role cụ thể (ví dụ: Sale, KeToan, KTV)"),
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help=("Xóa ChromaDB collection cũ trước khi index"),
    )

    parser.add_argument(
        "--no-minio",
        action="store_true",
        help=("Không upload cleaned Markdown lên MinIO"),
    )

    args = parser.parse_args()

    run_ingestion_pipeline(
        file_target=args.file,
        role_filter=args.role,
        reset=args.reset,
        upload_minio=not args.no_minio,
    )
