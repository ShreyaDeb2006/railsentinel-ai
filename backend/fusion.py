"""
fusion.py
---------
This is the "brain" logic: it looks at recent camera detections and
handheld readings, matches ones that happened close together in time
and location, and decides a threat level.

Kept deliberately simple (rule-based thresholds) so it's easy to explain
to judges and easy to tune during testing. This can be replaced with a
proper ML model later without changing anything else in the backend.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models

# --- Tunable thresholds (adjust these while testing) ---
TIME_WINDOW_SECONDS = 30      # how close in time two readings must be to "match"
DISTANCE_THRESHOLD = 0.01     # ~1km in lat/lng degrees, rough approximation for demo

HIGH_CAMERA_CONF = 0.7
HIGH_HANDHELD_VAL = 0.6
UNCERTAIN_CAMERA_CONF = 0.4
UNCERTAIN_HANDHELD_VAL = 0.3


def _close_enough(a_lat, a_lng, b_lat, b_lng):
    return abs(a_lat - b_lat) < DISTANCE_THRESHOLD and abs(a_lng - b_lng) < DISTANCE_THRESHOLD


def classify(camera_confidence: float, handheld_value: float) -> str:
    """Turns two numbers into a Low / Uncertain / High threat label."""
    if camera_confidence is None or handheld_value is None:
        # Only one sensor reported — treat cautiously
        score = camera_confidence or handheld_value or 0
        if score >= HIGH_CAMERA_CONF:
            return "UNCERTAIN"
        return "LOW"

    if camera_confidence >= HIGH_CAMERA_CONF and handheld_value >= HIGH_HANDHELD_VAL:
        return "HIGH"
    if camera_confidence >= UNCERTAIN_CAMERA_CONF or handheld_value >= UNCERTAIN_HANDHELD_VAL:
        return "UNCERTAIN"
    return "LOW"


def _make_alert(db, camera=None, handheld=None):
    camera_conf = camera.confidence if camera else None
    handheld_val = handheld.reading_value if handheld else None
    lat = camera.lat if camera else handheld.lat
    lng = camera.lng if camera else handheld.lng
    device_ids = [d.device_id for d in (camera, handheld) if d]

    alert = models.Alert(
        threat_level=classify(camera_conf, handheld_val),
        camera_confidence=camera_conf,
        handheld_reading=handheld_val,
        object_type=camera.object_type if camera else None,
        lat=lat,
        lng=lng,
        device_ids=",".join(device_ids),
        status="pending_verification",
    )
    db.add(alert)
    if camera:
        camera.matched = True
    if handheld:
        handheld.matched = True
    db.commit()
    db.refresh(alert)
    return alert


def try_fuse(db: Session):
    """
    Called right after a new camera detection or handheld reading is
    saved. Looks ONLY for an immediate pair (a camera detection and a
    handheld reading, both still unmatched, close in time and location).

    If no pair exists yet, this does nothing and returns None — the lone
    reading is left unmatched so it still has a chance to be paired when
    the other sensor's data arrives moments later. Use sweep_stale() to
    eventually turn old unmatched leftovers into solo alerts.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=TIME_WINDOW_SECONDS)

    unmatched_camera = (
        db.query(models.CameraDetection)
        .filter(models.CameraDetection.matched == False)  # noqa: E712
        .filter(models.CameraDetection.timestamp >= cutoff)
        .order_by(models.CameraDetection.timestamp.desc())
        .first()
    )
    unmatched_handheld = (
        db.query(models.HandheldReading)
        .filter(models.HandheldReading.matched == False)  # noqa: E712
        .filter(models.HandheldReading.timestamp >= cutoff)
        .order_by(models.HandheldReading.timestamp.desc())
        .first()
    )

    if unmatched_camera and unmatched_handheld and _close_enough(
        unmatched_camera.lat, unmatched_camera.lng,
        unmatched_handheld.lat, unmatched_handheld.lng
    ):
        return _make_alert(db, camera=unmatched_camera, handheld=unmatched_handheld)

    return None


def sweep_stale(db: Session):
    """
    Run periodically (e.g. every few seconds) in the background.
    Any camera detection or handheld reading that is now OLDER than the
    matching time window and still unmatched never found its pair —
    turn it into its own solo alert instead of losing it silently.

    Returns a list of any new Alerts created.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=TIME_WINDOW_SECONDS)
    new_alerts = []

    stale_cameras = (
        db.query(models.CameraDetection)
        .filter(models.CameraDetection.matched == False)  # noqa: E712
        .filter(models.CameraDetection.timestamp < cutoff)
        .all()
    )
    for cam in stale_cameras:
        new_alerts.append(_make_alert(db, camera=cam))

    stale_handhelds = (
        db.query(models.HandheldReading)
        .filter(models.HandheldReading.matched == False)  # noqa: E712
        .filter(models.HandheldReading.timestamp < cutoff)
        .all()
    )
    for hh in stale_handhelds:
        new_alerts.append(_make_alert(db, handheld=hh))

    return new_alerts