# ---- Camera ----
CAMERA_SOURCE = 0
# 0 = laptop webcam.
# You can also use a video file path or RTSP URL.

# ---- Model ----
MODEL_PATH = "yolov8n.pt"
# YOLOv8n downloads automatically on first run.

CONFIDENCE_THRESHOLD = 0.45


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