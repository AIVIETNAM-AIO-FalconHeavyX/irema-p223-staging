"""Validate processed chunks without writing to PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.embedding.embedder import EmbeddingService  # noqa: E402
from src.migration.chunk_importer import dry_run_import, embed_and_upsert_records  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks-dir", type=Path, default=Path("data/processed/chunks"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--embedding-version", default="1")
    parser.add_argument("--pipeline-version", default="1")
    parser.add_argument("--chunk-version", default="1")
    parser.add_argument("--write", action="store_true", help="Embed and write validated records to PostgreSQL")
    parser.add_argument("--database-url", help="Required with --write")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    result = dry_run_import(
        args.chunks_dir,
        embedding_model=args.embedding_model,
        embedding_version=args.embedding_version,
        pipeline_version=args.pipeline_version,
        chunk_version=args.chunk_version,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report_payload = result.to_dict()

    if args.write:
        if not args.database_url:
            parser.error("--database-url is required with --write")
        if result.summary["invalid"]:
            print("Refusing to write because the dry run found invalid chunks.", file=sys.stderr)
            return 1
        engine = create_engine(args.database_url)
        session_factory = sessionmaker(bind=engine)
        embedder = EmbeddingService(model_name=args.embedding_model)
        report_payload["database_write"] = embed_and_upsert_records(
            result.records,
            embedder=embedder,
            session_factory=session_factory,
            batch_size=args.batch_size,
        )

    args.report.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result.summary, ensure_ascii=False, sort_keys=True))
    if "database_write" in report_payload:
        print(json.dumps(report_payload["database_write"], ensure_ascii=False, sort_keys=True))
    print(f"Sanitized dry-run report written to {args.report}")
    return 1 if result.summary["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
