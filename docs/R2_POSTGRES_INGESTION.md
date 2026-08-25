# Controlled R2 ingestion on Railway

The web service never scans or processes the R2 bucket during startup. It exposes
VinFast-admin-only controls:

- `POST /api/v1/s3-manager/sync` with `{ "dry_run": true }` for reconciliation
- `POST /api/v1/s3-manager/sync` with `{ "dry_run": false }` to queue processing
- `GET /api/v1/s3-manager/sync/status` for progress
- `GET /api/v1/s3-manager/documents?status=failed` for failures
- `POST /api/v1/s3-manager/retry-failed` to create a retry run

Create a second Railway service from the same repository. Give it the same
`DATABASE_URL`, R2, embedding, and LLM environment variables as the web service,
and set its start command to:

```text
python scripts/r2_ingestion_worker.py
```

Recommended web-service variables:

```text
RETRIEVAL_BACKEND=postgres
LIVE_INGESTION_ENABLED=false
LEGACY_STARTUP_INGESTION=false
```

The first sync is a dry run. Review the skipped/unsupported count, then start a
normal sync. Jobs are persisted in PostgreSQL, continue after individual
document failures, and can be retried without creating duplicate registry rows
or active chunks.
