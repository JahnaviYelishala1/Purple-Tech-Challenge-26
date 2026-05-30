from __future__ import annotations

from typing import Any

import requests


INGEST_URL = "http://localhost:8000/events/ingest"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 5


def _payload(event: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {"events": [event]}


def publish_event(event: dict[str, Any]) -> bool:
    """Publish a single event to the backend ingestion API.

    Returns True when the backend accepts the request (HTTP 200), otherwise False.
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                INGEST_URL,
                json=_payload(event),
                timeout=TIMEOUT_SECONDS,
            )

            if response.status_code == 200:
                print(f"publish_event success: response_code={response.status_code} attempt={attempt}")
                return True

            print(
                "publish_event failure: "
                f"response_code={response.status_code} attempt={attempt} body={response.text}"
            )
        except requests.RequestException as exc:
            print(f"publish_event failure: response_code=N/A attempt={attempt} error={exc}")

    return False
