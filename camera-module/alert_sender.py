import os
import json
import math
import time
from datetime import datetime, timezone

import cv2
import requests
import config


os.makedirs(config.ALERTS_DIR, exist_ok=True)

LOG_FILE = os.path.join(config.ALERTS_DIR, "alerts_log.json")

# Module-level state (single camera process = single set of recent
# alerts/backend status; multi_camera.py gives each thread its own
# Detector/ObjectTracker, but alerts across ALL cameras sharing this
# process still go through the same cooldown/backoff, which is fine -
# an alert on one physical camera doesn't need to independently
# re-trigger backend-down backoff logic).
_recent_alert_locations = []  # [(x, y, timestamp), ...]
_backend_down_until = 0.0


def _append_local_log(alert):

    logs = []

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(alert)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def _within_cooldown(centroid, now):
    """
    True if a HIGH alert was already sent very recently at essentially
    this same location - protects against alert spam when tracking
    briefly loses a bag and it comes back under a new track ID (a
    fresh ID would otherwise bypass the tracker's own per-track
    debounce entirely).
    """

    global _recent_alert_locations

    _recent_alert_locations = [
        (x, y, t) for (x, y, t) in _recent_alert_locations
        if now - t < config.ALERT_COOLDOWN_SEC
    ]

    for x, y, _ in _recent_alert_locations:
        if math.hypot(centroid[0] - x, centroid[1] - y) < config.ALERT_COOLDOWN_PX:
            return True

    return False


def send_alert(frame, detection):
    """
    Saves a snapshot, logs the alert locally, and POSTs it to the
    backend matching backend/schemas.py:CameraDetectionIn exactly:

        {
          "device_id": str,
          "object_type": str,
          "confidence": float,
          "gps": {"lat": float, "lng": float},
          "timestamp": <ISO-8601 datetime string>
        }

    Returns None (and sends nothing) if this location is still within
    its alert cooldown - the caller doesn't need to track that itself.
    """

    global _backend_down_until

    now = time.time()

    centroid = detection.get("centroid")

    if centroid and _within_cooldown(centroid, now):
        if config.DEBUG:
            print(
                f"[ALERT] Skipped - within {config.ALERT_COOLDOWN_SEC}s "
                f"cooldown for this location"
            )
        return None

    now_dt = datetime.now(timezone.utc)
    file_timestamp = now_dt.strftime("%Y%m%d-%H%M%S")

    snapshot_name = f"alert_{detection['object_id']}_{file_timestamp}.jpg"
    snapshot_path = os.path.join(config.ALERTS_DIR, snapshot_name)

    cv2.imwrite(snapshot_path, frame)

    backend_payload = {
        "device_id": detection.get("device_id", config.DEVICE_ID),
        "object_type": detection["class_name"],
        "confidence": round(detection["confidence"], 2),
        "gps": {
            "lat": config.CAMERA_LAT,
            "lng": config.CAMERA_LNG,
        },
        "timestamp": now_dt.isoformat(),
    }

    local_alert = {
        **backend_payload,
        "threat_level": detection["threat_level"],
        "unattended_seconds": detection["unattended_seconds"],
        "snapshot": snapshot_path,
    }

    _append_local_log(local_alert)

    if centroid:
        _recent_alert_locations.append((centroid[0], centroid[1], now))

    if now < _backend_down_until:
        remaining = round(_backend_down_until - now, 1)
        print(
            f"[camera-module] Backend recently unreachable, skipping "
            f"retry for {remaining}s more. Alert saved locally: {snapshot_name}"
        )
        return local_alert

    try:

        if config.DEBUG:
            print(f"[BACKEND] POST {config.BACKEND_API_URL}")
            print(f"[BACKEND] payload: {backend_payload}")

        resp = requests.post(
            config.BACKEND_API_URL,
            json=backend_payload,
            timeout=config.BACKEND_TIMEOUT_SEC,
        )

        if resp.status_code >= 400:
            print(
                f"[camera-module] Backend REJECTED the alert "
                f"({resp.status_code}): {resp.text}"
            )
        else:
            if config.DEBUG:
                print(f"[BACKEND] {resp.status_code} {resp.text}")
            print(f"[camera-module] Sent to backend OK: {resp.json()}")

    except requests.exceptions.RequestException as exc:

        _backend_down_until = now + config.BACKEND_DOWN_BACKOFF_SEC

        print(
            f"[camera-module] Backend not reachable, alert saved "
            f"locally: {snapshot_name} ({exc}). Backing off retries "
            f"for {config.BACKEND_DOWN_BACKOFF_SEC}s."
        )

    return local_alert
