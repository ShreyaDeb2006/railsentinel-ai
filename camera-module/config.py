# ---- Camera ----
CAMERA_SOURCE = 0
# 0 = laptop webcam.
# You can also use a video file path or RTSP URL.

CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720


# ---- Model ----
MODEL_PATH = "yolov8s.pt"
# YOLOv8s downloads automatically on first run.

INFERENCE_SIZE = 960

CONFIDENCE_THRESHOLDS = {
    "person": 0.45,
    "backpack": 0.25,
    "handbag": 0.25,
    "suitcase": 0.25,
}


# ---- Threat logic ----
PERSON_PROXIMITY_PX = 180

UNCERTAIN_AFTER_SEC = 3

HIGH_ALERT_AFTER_SEC = 10

MATCH_DISTANCE_PX = 80


# ---- Backend integration ----
BACKEND_API_URL = "http://localhost:5000/api/alerts"

DEVICE_ID = "AI-CAM-01"


# ---- Output ----
ALERTS_DIR = "alerts"