# Deployment Guide

This document explains how to run the project locally, in Docker, and on Render (used for the demo). It also lists required environment variables and common troubleshooting steps.

## Environment variables

- `DATABASE_URL` — SQLAlchemy-compatible DSN. Example (Postgres): `postgresql://user:pass@host:5432/dbname`.
- `API_BASE_URL` — Base URL the dashboard uses to call the API (required when dashboard is deployed separately).
- `DEMO_SEED_ON_STARTUP` — `true`/`false` to seed demo data on API startup.
- `LOG_LEVEL` — logging level (INFO/DEBUG).

## Local deployment (Python)

1. Create and activate a virtual environment:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the API (development):

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Start the dashboard (in a separate terminal):

```powershell
set API_BASE_URL=http://127.0.0.1:8000
streamlit run dashboard/app.py
```

5. Health checks:

```powershell
curl http://127.0.0.1:8000/health
```

## Docker (compose)

1. Build and run (docker-compose must be installed):

```powershell
docker compose up --build
```

2. The compose file exposes the API on port 8000. Dashboard can be run locally or added as a service in `docker-compose.yml` if desired.

Notes: the repository defaults to SQLite for quick demo runs. For production, set `DATABASE_URL` to a Postgres instance and update any Docker secrets accordingly.

## Render deployment

This project includes `render.yaml` to simplify blueprint deploys. Render will create two services: API and dashboard.

Steps:

1. In Render, create a new Web Service using the GitHub repo (or create a Blueprint deploy and apply it). Render will create `store-intelligence-api` and `store-intelligence-dashboard`.
2. For the API service, set these environment variables in Render:
   - `DATABASE_URL` (use Render Postgres for persistence)
   - `DEMO_SEED_ON_STARTUP` (optional)
3. For the Dashboard service, set:
   - `API_BASE_URL` = URL of the deployed API (example: `https://store-intelligence-api-izty.onrender.com`)
4. Trigger a redeploy of the Dashboard service to pick up the env var.

Common Render troubleshooting:

- Dashboard shows "Backend Offline": confirm `API_BASE_URL` is set on the *dashboard* service and points to the API URL. Environment variable names are case-sensitive.
- Backend fails on startup with DB errors: confirm `DATABASE_URL` and Postgres credentials are correct and the database is reachable from Render.
- Logs: open the Render service logs and search for `ERROR`, `Traceback`, or the diagnostic startup line `Dashboard starting with API_BASE_URL=`.

## Troubleshooting checklist

- Is the API returning `200` on `/health`?
- Is `API_BASE_URL` correctly configured on the dashboard service?
- Are database migrations/schema created? On first API startup the schema is created automatically for SQLite. For Postgres, confirm a successful migration step.
- Connectivity: confirm that the backend host allows connections from the dashboard host (CORS is not required for server-to-server REST calls but network reachability matters).
