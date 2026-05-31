# Demo Guide — 3–5 Minute Walkthrough

This short script is tailored for hackathon judges. It shows the core features of the Store Intelligence submission in a concise, reproducible flow.

Preparation
- Ensure the API and dashboard are deployed and reachable. The dashboard must have `API_BASE_URL` configured to point at the API.
- If no live data exists, start the demo generator:

```powershell
python pipeline/mock_event_generator.py --base-url http://127.0.0.1:8000 --stores STORE_BLR_001 --volume 50 --batch-size 100
```

3–5 Minute Script

0:00 — 0:20 — Brief Overview
- One-slide architecture: cameras → YOLOv8 → tracker → event publisher → FastAPI → analytics → Streamlit dashboard.

0:20 — 1:20 — Start Live Data (if required)
- Run the mock event generator (or ensure the CV pipeline is running and posting events). Explain that events are normalized business events.

1:20 — 2:20 — Dashboard Walkthrough
- Open the live dashboard.
- Point out KPIs: Unique Visitors, Active Visitors, Conversion Rate.
- Show funnel: how visitors progress through ENTRY → ZONE_VISIT → BILLING_QUEUE → PURCHASE.

2:20 — 3:20 — Anomaly & Heatmap
- Simulate a queue spike by increasing generator volume or injecting `BILLING_QUEUE_JOIN` events.
- Show the anomaly panel where a `QUEUE_SPIKE` alert appears and suggested action.
- Show heatmap/zone dwell to demonstrate zone-level analytics.

3:20 — 4:00 — Backend Evidence & Logs
- Open the API `/docs` to show OpenAPI definitions.
- Point to structured JSON logs or Render logs showing request trace IDs.

Expected outputs
- KPIs update with generated events.
- Funnel counts move proportionally to traffic volume.
- Anomaly appears when queue threshold is breached.

Troubleshooting
- If dashboard shows "Backend Offline": confirm `API_BASE_URL` (dashboard env vars) and `/health` on the API.
- If no data: ensure mock generator `--base-url` matches the API and `DEMO_SEED_ON_STARTUP` is `true` if using seeded data.

Screenshots
- Use images from `docs/screenshots/` to show the expected visuals if live demo connectivity fails.
