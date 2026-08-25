"""Railway worker entrypoint for controlled R2 ingestion."""

from __future__ import annotations

import os
import time

from src.db import SessionLocal
from src.ingestion.durable import durable_ingestion


def main() -> None:
    poll_seconds = max(2, int(os.getenv("INGESTION_WORKER_POLL_SECONDS", "5")))
    while True:
        db = SessionLocal()
        try:
            durable_ingestion.process_one_batch(db, limit=1)
        finally:
            db.close()
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
