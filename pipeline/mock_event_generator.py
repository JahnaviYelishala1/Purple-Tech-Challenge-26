from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EVENT_SEQUENCE = [
    "ENTRY",
    "ZONE_ENTER",
    "ZONE_DWELL",
    "BILLING_QUEUE_JOIN",
    "EXIT",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and send mock store events.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="FastAPI base URL")
    parser.add_argument(
        "--stores",
        default="store-001,store-002",
        help="Comma-separated store IDs to generate events for",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=10,
        help="Number of visitor journeys to generate per run",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Events per ingestion request",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay between batches, useful for live demos",
    )
    return parser.parse_args()


def post_json(base_url: str, path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=data,
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def build_journey(store_id: str, visitor_id: str, start: datetime) -> list[dict]:
    aisle = random.choice(["aisle-a", "aisle-b", "aisle-c"])
    dwell_ms = random.randint(20_000, 180_000)
    queue_depth = random.randint(1, 8)

    timestamps = [
        start,
        start + timedelta(seconds=random.randint(15, 90)),
        start + timedelta(seconds=random.randint(100, 220)),
        start + timedelta(seconds=random.randint(230, 320)),
        start + timedelta(seconds=random.randint(330, 520)),
    ]

    zones = ["entrance", aisle, aisle, "billing", "exit"]

    events: list[dict] = []
    for idx, event_type in enumerate(EVENT_SEQUENCE, start=1):
        event = {
            "event_id": str(uuid4()),
            "store_id": store_id,
            "camera_id": f"cam-{random.randint(1, 4):02d}",
            "visitor_id": visitor_id,
            "event_type": event_type,
            "timestamp": timestamps[idx - 1].isoformat().replace("+00:00", "Z"),
            "zone_id": zones[idx - 1],
            "dwell_ms": dwell_ms if event_type == "ZONE_DWELL" else 0,
            "is_staff": False,
            "confidence": round(random.uniform(0.9, 0.99), 3),
            "metadata": {
                "queue_depth": queue_depth if event_type == "BILLING_QUEUE_JOIN" else None,
                "sku_zone": zones[idx - 1],
                "session_seq": idx,
            },
        }
        events.append(event)

    return events


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> int:
    args = parse_args()
    stores = [store.strip() for store in args.stores.split(",") if store.strip()]
    if not stores:
        print("No stores configured. Use --stores store-001,store-002")
        return 1

    if args.volume < 1 or args.batch_size < 1:
        print("--volume and --batch-size must be positive integers")
        return 1

    all_events: list[dict] = []
    now = datetime.now(timezone.utc)

    for i in range(args.volume):
        store_id = random.choice(stores)
        visitor_id = f"visitor-{uuid4().hex[:10]}"
        journey_start = now - timedelta(minutes=random.randint(0, 60), seconds=random.randint(0, 59))
        all_events.extend(build_journey(store_id=store_id, visitor_id=visitor_id, start=journey_start))

    total_inserted = 0
    total_duplicates = 0

    print(f"Generated {len(all_events)} events across {len(stores)} stores")

    for batch_index, event_batch in enumerate(chunked(all_events, args.batch_size), start=1):
        try:
            response = post_json(args.base_url, "/events/ingest", {"events": event_batch})
            total_inserted += int(response.get("inserted", 0))
            total_duplicates += int(response.get("duplicates", 0))
            print(
                f"Batch {batch_index}: received={response.get('total_received', 0)} "
                f"inserted={response.get('inserted', 0)} duplicates={response.get('duplicates', 0)}"
            )
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            print(f"Batch {batch_index} failed with HTTP {error.code}: {body}")
            return 1
        except URLError as error:
            print(f"Batch {batch_index} failed: could not reach API ({error.reason})")
            return 1

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print(
        f"Completed ingestion. total_events={len(all_events)} inserted={total_inserted} duplicates={total_duplicates}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
