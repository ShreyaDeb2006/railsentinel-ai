# ---- Camera ----
# Single source (used by main.py). For multiple CCTV-style feeds
# running at once, list them here and use multi_camera.py instead.
CAMERA_SOURCE = 0
# 0 = laptop webcam.
# You can also use a video file path or RTSP URL.

CAMERA_SOURCES = [
    0,
    # "rtsp://user:pass@192.168.1.10/stream1",
    # "rtsp://user:pass@192.168.1.11/stream1",
    # "videos/platform2.mp4",
]

# ---- Model ----
# yolov8n = fastest/least accurate, yolov8s/m = slower but noticeably
# better at telling small/distant bags apart from people.
# If you have a GPU, yolov8s.pt is a good accuracy upgrade with
# almost no speed cost.
MODEL_PATH = "yolov8n.pt"
# Downloads automatically on first run.

CONFIDENCE_THRESHOLD = 0.45

# Higher input resolution = the model sees more detail on small/far
# away objects, which is the #1 fix for "bag detected as person".
# Must be a multiple of 32. 640 is the YOLO default; 960 is a good
# accuracy upgrade if your hardware can keep up.
MODEL_IMG_SIZE = 960

# "cpu", "cuda" (Nvidia GPU) or "mps" (Apple Silicon).
DEVICE = "cpu"


# ---- Threat logic ----
PERSON_PROXIMITY_PX = 180

UNCERTAIN_AFTER_SEC = 3

HIGH_ALERT_AFTER_SEC = 10

MATCH_DISTANCE_PX = 80

# How many seconds a tracked bag is allowed to be MISSED by the
# detector (occluded, motion blur, a flickering low-confidence
# frame, etc.) while still being drawn at its last known position.
# This is what stops the box from disappearing/reappearing when the
# bag hasn't actually moved.
TRACK_GRACE_SEC = 1.5

# How many seconds with literally no detection at all before we
# forget the track completely and free up its ID.
TRACK_FORGET_SEC = 5


# ---- Backend integration ----
BACKEND_API_URL = "http://localhost:5000/api/alerts"

DEVICE_ID = "AI-CAM-01"


# ---- Output ----
ALERTS_DIR = "alerts"