import os
import json
import time
from datetime import datetime, timezone

import cv2
import requests
import config


os.makedirs(
    config.ALERTS_DIR,
    exist_ok=True
)


LOG_FILE = os.path.join(
    config.ALERTS_DIR,
    "alerts_log.json"
)


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

        json.dump(
            logs,
            f,
            indent=2
        )


def send_alert(frame, detection):
    """
    Saves a snapshot, logs the alert locally, and POSTs it to the
    backend using the EXACT shape backend/schemas.py:CameraDetectionIn
    requires:

        {
          "device_id": str,
          "object_type": str,
          "confidence": float,
          "gps": {"lat": float, "lng": float},
          "timestamp": <ISO-8601 datetime string>
        }

    Sending anything else (extra/renamed fields, a missing "gps", or
    a non-ISO timestamp) makes FastAPI reject it with a 422 before it
    ever reaches the fusion/alert logic - which is why alerts from
    this module might never have been showing up on the dashboard.
    """

    now = datetime.now(timezone.utc)

    # Local filename still uses a filesystem-safe format.
    file_timestamp = now.strftime("%Y%m%d-%H%M%S")

    snapshot_name = (
        f"alert_{detection['object_id']}_"
        f"{file_timestamp}.jpg"
    )

    snapshot_path = os.path.join(
        config.ALERTS_DIR,
        snapshot_name
    )

    cv2.imwrite(
        snapshot_path,
        frame
    )

    # ---- Payload sent to the backend: must match schemas.CameraDetectionIn ----
    backend_payload = {
        "device_id": detection.get(
            "device_id", config.DEVICE_ID
        ),
        "object_type": detection["class_name"],
        "confidence": round(detection["confidence"], 2),
        "gps": {
            "lat": config.CAMERA_LAT,
            "lng": config.CAMERA_LNG,
        },
        # ISO-8601, timezone-aware - this is the format Pydantic's
        # datetime validator actually accepts.
        "timestamp": now.isoformat(),
    }

    # ---- Everything else, kept locally for our own debugging/audit ----
    local_alert = {
        **backend_payload,
        "threat_level": detection["threat_level"],
        "unattended_seconds": detection["unattended_seconds"],
        "snapshot": snapshot_path,
    }

    # Always save locally first, regardless of backend reachability.
    _append_local_log(local_alert)

    try:

        if config.DEBUG:
            print(f"[BACKEND] POST {config.BACKEND_API_URL}")
            print(f"[BACKEND] payload: {backend_payload}")

        resp = requests.post(
            config.BACKEND_API_URL,
            json=backend_payload,
            timeout=2
        )

        if resp.status_code >= 400:
            print(
                "[camera-module] Backend REJECTED the alert "
                f"({resp.status_code}): {resp.text}"
            )
        else:
            if config.DEBUG:
                print(f"[BACKEND] {resp.status_code} {resp.text}")
            print(
                f"[camera-module] Sent to backend OK: "
                f"{resp.json()}"
            )

    except requests.exceptions.RequestException as exc:

        print(
            "[camera-module] "
            "Backend not reachable, "
            f"alert saved locally: "
            f"{snapshot_name} ({exc})"
        )

    return local_alert