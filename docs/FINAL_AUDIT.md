# Final Project Audit

Date: 2026-05-30

## Submission Checklist

- [ ] Docker works
- [x] README complete
- [x] DESIGN.md > 250 words
- [x] CHOICES.md > 250 words
- [x] 20+ tests pass
- [x] Coverage > 70%
- [x] Dashboard works
- [x] APIs documented
- [x] Logging enabled

## Evidence

### Docker works

- Command attempted: `docker compose up --build -d`
- Current result on this machine: failed because Docker engine is unavailable (`//./pipe/dockerDesktopLinuxEngine` not found).
- Status: blocked by local Docker runtime, not by repository code.

### README complete

- API overview, architecture, setup, Docker instructions, testing, and API docs are present.
- Added sections for Streamlit dashboard and demo data generator.

### Documentation length

- `docs/DESIGN.md`: 1152 words
- `docs/CHOICES.md`: 1258 words

### Tests and Coverage

- Test command: `pytest -q`
- Result: `20 passed`
- Coverage command: `coverage run -m pytest -q && coverage report`
- Total coverage: `86%`

### Dashboard works

- Dashboard file: `dashboard/streamlit_app.py`
- Validation: Streamlit server starts successfully on `http://localhost:8501`.
- Features implemented:
  - Store selector dropdown
  - Unique Visitors
  - Conversion Rate
  - Active Visitors
  - Funnel Metrics
  - Heatmap Metrics
  - Active Anomalies
  - Auto-refresh every 10 seconds

### APIs documented

- Endpoint documentation included in README.
- FastAPI OpenAPI/Swagger available at `/docs` while server is running.

### Logging enabled

- Structured JSON logging configured in `app/core/logging.py`.
- Request logging middleware enabled in `app/main.py` via `add_request_logging_middleware(app)`.

## Additional Acceptance Gate

- Full endpoint verification checklist is recorded in `docs/ACCEPTANCE_CHECKLIST.md`.
- All required challenge endpoints returned HTTP 200 in live checks.
