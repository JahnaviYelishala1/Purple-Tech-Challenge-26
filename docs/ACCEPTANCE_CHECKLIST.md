# Acceptance Gate Checklist

Date: 2026-05-30

## Environment Check

- Docker compose command attempted: `docker compose up --build -d`
- Result: failed on this machine because Docker engine pipe was unavailable (`//./pipe/dockerDesktopLinuxEngine` not found).
- Fallback used for endpoint validation: local uvicorn runtime on `http://127.0.0.1:8001`.

## Required Endpoint Verification

All required endpoints were executed against a live API process with realistic ingestion payloads.

- [x] `GET /` -> 200 OK
- [x] `GET /health` -> 200 OK
- [x] `POST /events/ingest` -> 200 OK
- [x] `POST /transactions/ingest` -> 200 OK
- [x] `GET /stores/{id}/metrics` -> 200 OK
- [x] `GET /stores/{id}/funnel` -> 200 OK
- [x] `GET /stores/{id}/heatmap` -> 200 OK
- [x] `GET /stores/{id}/anomalies` -> 200 OK

## Evidence Snapshot

- Store tested: `store-001`
- Event types ingested in check run: `ENTRY`, `ZONE_ENTER`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, `EXIT`
- Metrics response sample: `{"unique_visitors":1,"active_visitors":0,"converted_visitors":1,"conversion_rate":100.0,"avg_session_duration_seconds":300.0}`
- Funnel response sample includes all stages with counts
- Heatmap response sample includes zone metrics and confidence
- Anomalies response sample returned valid schema (`anomalies` list)

## Notes

- A startup schema initialization step was added in the FastAPI lifespan so new SQLite files are initialized automatically before serving requests.
- For local runs, set `DATABASE_URL` explicitly if your shell has a global Postgres `DATABASE_URL` override.
