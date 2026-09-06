import os
import json
import time
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
    Saves a snapshot, logs the alert locally,
    and tries to send it to the backend.
    """

    timestamp = time.strftime(
        "%Y%m%d-%H%M%S"
    )

    snapshot_name = (
        f"alert_{detection['object_id']}_"
        f"{timestamp}.jpg"
    )

    snapshot_path = os.path.join(
        config.ALERTS_DIR,
        snapshot_name
    )

    cv2.imwrite(
        snapshot_path,
        frame
    )

    alert = {

        "device_id": config.DEVICE_ID,

        "timestamp": timestamp,

        "object_class":
            detection["class_name"],

        "threat_level":
            detection["threat_level"],

        "unattended_seconds":
            detection["unattended_seconds"],

        "confidence":
            round(
                detection["confidence"],
                2
            ),

        "snapshot":
            snapshot_path,
    }

    # Always save locally first.

    _append_local_log(alert)

    # Try the backend.

    try:

        requests.post(
            config.BACKEND_API_URL,
            json=alert,
            timeout=2
        )

    except requests.exceptions.RequestException:

        print(
            "[camera-module] "
            "Backend not reachable, "
            f"alert saved locally: "
            f"{snapshot_name}"
        )

    return alert