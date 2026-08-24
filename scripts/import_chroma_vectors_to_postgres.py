"""Populate PostgreSQL document_chunks from the verified local Chroma vectors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chromadb  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.migration.chunk_importer import (  # noqa: E402
    EmbeddedRecord,
    dry_run_import,
    upsert_embedded_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--chunks-dir", type=Path, default=Path("data/processed/chunks"))
    parser.add_argument("--chroma-dir", type=Path, default=Path("data/chroma"))
    parser.add_argument("--collection", default="rag_chunks")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    dry_run = dry_run_import(args.chunks_dir)
    records = {record.id: record for record in dry_run.records}
    collection = chromadb.PersistentClient(path=str(args.chroma_dir)).get_collection(args.collection)
    stored = collection.get(include=["embeddings"])

    duplicate_ids = {issue.chunk_id for issue in dry_run.issues if issue.code in {"duplicate_id", "duplicate_hash"}}
    missing_records = sorted(set(stored["ids"]) - set(records) - duplicate_ids)
    missing_vectors = sorted(set(records) - set(stored["ids"]))
    if missing_records or missing_vectors:
        raise RuntimeError(
            f"Chroma/chunk mismatch: missing_records={len(missing_records)}, missing_vectors={len(missing_vectors)}"
        )

    embedded = [
        EmbeddedRecord(record=records[chunk_id], embedding=[float(value) for value in vector])
        for chunk_id, vector in zip(stored["ids"], stored["embeddings"], strict=True)
        if chunk_id in records
    ]
    engine = create_engine(args.database_url)
    factory = sessionmaker(bind=engine)
    totals = {"inserted": 0, "updated": 0, "unchanged": 0, "batches": 0}
    for start in range(0, len(embedded), args.batch_size):
        session = factory()
        try:
            counts = upsert_embedded_batch(session, embedded[start : start + args.batch_size])
        finally:
            session.close()
        for key in ("inserted", "updated", "unchanged"):
            totals[key] += counts[key]
        totals["batches"] += 1

    payload = {
        "validated_chunks": len(records),
        "chroma_vectors": len(stored["ids"]),
        "skipped_duplicate_vectors": len(duplicate_ids),
        "database_write": totals,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
