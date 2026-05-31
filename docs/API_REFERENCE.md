# API Reference

This file documents the main API endpoints exposed by the Store Intelligence backend. Example request/response shapes are included to help graders and integrators.

Base path: `/`

## GET /health
- Method: GET
- Purpose: Service readiness check
- Request: none
- Response (200):

```json
{ "status": "healthy" }
```

## POST /events/ingest
- Method: POST
- Purpose: Ingest normalized business events (entry, exit, zone events, queue events)
- Request body (example):

```json
{
  "store_id": "STORE_BLR_001",
  "camera_id": "cam3",
  "event_type": "ENTRY",
  "timestamp": "2026-05-31T09:00:00Z",
  "payload": { "tracking_id": "t-123" }
}
```

- Response (201): Created or 200 with acknowledgement. Error responses: 400 for invalid payload, 500 for server errors.

## POST /transactions/ingest
- Method: POST
- Purpose: Ingest POS transactions and mark sessions converted
- Request body (example):

```json
{
  "store_id": "STORE_BLR_001",
  "timestamp": "2026-05-31T09:05:00Z",
  "transaction_id": "txn-123",
  "amount": 125.50
}
```

- Response: 201/200. Errors: 400 invalid fields, 404 session not found, 500 server error.

## GET /stores/{store_id}/metrics
- Method: GET
- Purpose: Return store-level metrics (unique visitors, active visitors, conversion rate)
- Response (200 example):

```json
{
  "unique_visitors": 120,
  "active_visitors": 4,
  "conversion_rate": 0.075,
  "average_session_duration_seconds": 312
}
```

## GET /stores/{store_id}/funnel
- Method: GET
- Purpose: Return funnel stages and counts
- Response (200 example):

```json
{
  "stages": [
    { "stage": "ENTRY", "count": 120 },
    { "stage": "ZONE_VISIT", "count": 90 },
    { "stage": "BILLING_QUEUE", "count": 18 },
    { "stage": "PURCHASE", "count": 9 }
  ]
}
```

## GET /stores/{store_id}/heatmap
- Method: GET
- Purpose: Return aggregated zone-level dwell/visits data
- Response (200 example):

```json
{
  "zones": [ { "zone_id": "z1", "visits": 40, "avg_dwell_seconds": 55 }, { "zone_id": "z2", "visits": 25, "avg_dwell_seconds": 22 } ]
}
```

## GET /stores/{store_id}/anomalies
- Method: GET
- Purpose: Return active operational alerts for the store
- Response (200 example):

```json
{
  "anomalies": [ { "anomaly_type": "QUEUE_SPIKE", "severity": "CRITICAL", "description": "Queue length spiked", "suggested_action": "Open another checkout" } ]
}
```

## GET /stores/{store_id}/pipeline-status
- Method: GET
- Purpose: Return CCTV pipeline connectivity and camera statuses
- Response: camera-level last heartbeat, last processed frame timestamp, and detector status.

## Errors
- 400 Bad Request — invalid JSON or missing required fields.
- 404 Not Found — resource not found (store, session).
- 500 Internal Server Error — unexpected server error; check logs.

Notes:
- OpenAPI/Swagger is available at `/docs` when the server runs; this file provides quick examples for judges who prefer human-readable docs.
