# Pipeline

This folder is reserved for future computer vision and data processing pipelines.

## Available Utility

### `mock_event_generator.py`

Generates synthetic visitor journeys and sends them to `POST /events/ingest`.

Event sequence per generated journey:

- `ENTRY`
- `ZONE_ENTER`
- `ZONE_DWELL`
- `BILLING_QUEUE_JOIN`
- `EXIT`

Example:

```powershell
python pipeline/mock_event_generator.py --base-url http://127.0.0.1:8001 --stores store-001,store-002 --volume 50 --batch-size 100
```

Planned uses:
- image ingestion and preprocessing
- model inference and feature extraction
- batch jobs for retail analytics workflows
- integration points for future CV services