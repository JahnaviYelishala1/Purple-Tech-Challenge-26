from __future__ import annotations


def resolve_event_confidence(
    *,
    detection_confidence: float | None = None,
    tracker_confidence: float | None = None,
    fallback_confidence: float = 0.5,
) -> float:
    """Return the strongest available confidence score for an emitted event."""

    for confidence in (detection_confidence, tracker_confidence, fallback_confidence):
        if confidence is None:
            continue
        return max(0.0, min(1.0, float(confidence)))

    return 0.5