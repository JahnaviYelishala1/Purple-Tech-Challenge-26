# Store Intelligence — Architecture

This document describes the high-level architecture, component responsibilities, and deployment topology for the Store Intelligence submission.

## High-level diagram

The canonical architecture diagram is included in the repository:

- `docs/store-intelligence-architecture.svg` (viewable on GitHub)
- `docs/store-intelligence-architecture.drawio` (editable source)

## Components & Responsibilities

- API (FastAPI) — `app/`:
  - `app/api/` contains route definitions grouped by concern (events, transactions, stores, metrics, funnel, heatmap, anomalies).
  - `app/services/` implements business logic: session lifecycle, metrics, funnel and anomaly computations.
  - `app/models/` and `app/schemas/` define the ORM and Pydantic contracts.

- Dashboard (Streamlit) — `dashboard/`:
  - `dashboard/app.py` renders the UI and calls the API endpoints exposed by the FastAPI service.
  - Auto-refresh and demo helpers provide a live view for judges.

- CV / Pipeline — `pipeline/`:
  - YOLOv8-based detection scripts, tracking helpers, and mock event generators live here.
  - The pipeline produces normalized business events and posts them to the API ingestion endpoints.

- Persistence — `data/` (SQLite by default in challenge package) or Postgres when configured by `DATABASE_URL`.

## Backend architecture

- Single modular FastAPI process that exposes ingestion and analytics routes.
- Startup lifecycle creates schema and optionally seeds demo data (`DEMO_SEED_ON_STARTUP`).
- Structured logging and request middleware provide trace IDs for each request.

## CV architecture

- Detection: YOLOv8 model (small variant) runs per-frame detections to locate customers.
- Tracking: a lightweight tracker (frame-to-frame ID reconciliation) produces stable tracking IDs.
- Event publisher: tracker + detection logic emit normalized business events (`ENTRY`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, etc.) to the API.

## Analytics architecture

- Services compute store-level aggregates by reading canonical event and session state.
- Funnel and heatmap services are deterministic functions over persisted events and sessions.

## Deployment architecture

- Recommended deployment contains two web services:
  1. `store-intelligence-api` — FastAPI backend
 2. `store-intelligence-dashboard` — Streamlit frontend
- Optional: managed Postgres instance for production-grade persistence. `DATABASE_URL` should point to a Postgres URI in that case.

## Database relationships

- Major entities:
  - `Event` — raw normalized business events (store_id, camera_id, event_type, timestamp, payload)
  - `VisitorSession` — session lifecycle (start_ts, end_ts, converted, visitor_id)
  - `Transaction` — POS transactions associated with a session
  - `Store` — store metadata
- Indexes: queries are optimized for `store_id`, `event_type`, and `timestamp`.

## Component-to-code mapping

- API routes: `app/api/*`
- Services: `app/services/*`
- Models: `app/models/*`
- Database / session: `app/db/*`
- Dashboard UI: `dashboard/*`
- CV / pipeline utilities: `pipeline/*`

## Notes

- The modular monolith makes it straightforward to extract services later; mapping is intentionally explicit to help judges evaluate responsibility boundaries.
