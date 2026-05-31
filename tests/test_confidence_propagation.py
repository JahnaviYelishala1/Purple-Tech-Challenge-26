from pipeline.billing_detector import make_billing_event
from pipeline.entry_detector import make_entry_event
from pipeline.exit_detector import make_exit_event


def test_detector_event_factories_use_detection_confidence() -> None:
    """Detector event factories should carry the detection confidence through to the payload."""

    entry_event = make_entry_event(
        track_id=1,
        camera_id="CAM3",
        store_id="STORE_BLR_001",
        detection_confidence=0.83,
    )
    exit_event = make_exit_event(
        track_id=2,
        camera_id="CAM4",
        store_id="STORE_BLR_001",
        detection_confidence=0.74,
    )
    billing_event = make_billing_event(
        track_id=3,
        camera_id="CAM5",
        store_id="STORE_BLR_001",
        detection_confidence=0.69,
    )

    assert entry_event["confidence"] == 0.83
    assert exit_event["confidence"] == 0.74
    assert billing_event["confidence"] == 0.69


def test_tracker_confidence_is_used_when_detection_is_missing() -> None:
    """Tracker confidence should be used when a detection score is not available."""

    entry_event = make_entry_event(
        track_id=4,
        camera_id="CAM3",
        store_id="STORE_BLR_001",
        detection_confidence=None,
        tracker_confidence=0.71,
    )

    assert entry_event["confidence"] == 0.71


def test_fallback_confidence_is_used_as_last_resort() -> None:
    """A fallback confidence should be available for synthetic or partially populated events."""

    exit_event = make_exit_event(
        track_id=5,
        camera_id="CAM4",
        store_id="STORE_BLR_001",
        detection_confidence=None,
        tracker_confidence=None,
        fallback_confidence=0.42,
    )

    assert exit_event["confidence"] == 0.42