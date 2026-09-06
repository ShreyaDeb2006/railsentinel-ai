# ---- Debug ----
# When True, every stage of the pipeline prints what it's doing:
# raw YOLO output, what got filtered/kept, tracker state, threat
# decisions, and the backend request/response. Turn this on whenever
# you need to see WHY a particular box appeared/disappeared/changed
# label, instead of guessing from the video window alone.
DEBUG = True
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
# The webcam is never told what resolution to capture at, so it can
# silently default to something low (commonly 640x480) depending on
# the driver. That caps how much detail even a high MODEL_IMG_SIZE
# can work with - upscaling a low-res frame doesn't add real detail
# back. This requests a higher capture resolution; if the hardware
# doesn't support it, OpenCV falls back to its native max, which is
# fine and gets logged either way.
REQUESTED_CAMERA_WIDTH = 1280
REQUESTED_CAMERA_HEIGHT = 720
# ---- Model ----
# yolov8n = fastest/least accurate, yolov8s/m = slower but noticeably
# better at telling small/distant bags apart from people.
# If you have a GPU, yolov8s.pt is a good accuracy upgrade with
# almost no speed cost.
MODEL_PATH = "yolov8n.pt"
# Downloads automatically on first run.
CONFIDENCE_THRESHOLD = 0.45
# Higher input resolution = the model sees more detail on small/far
# away objects, which helps with "bag detected as person". Must be a
# multiple of 32. 640 is the YOLO default; 960 is a good accuracy
# upgrade if your hardware can keep up.
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
# MUST match backend/main.py's actual endpoint. FastAPI/uvicorn's
# default port is 8000 (from `uvicorn main:app --reload`), and the
# camera module posts to POST /api/camera-detection - NOT /api/alerts
# (that path is GET-only, for the dashboard to read already-fused
# alerts back out). Posting to the wrong URL fails silently from the
# camera module's point of view (it just logs "backend not reachable"
# and keeps going), which is why this is easy to miss.
BACKEND_API_URL = "http://localhost:8000/api/camera-detection"
DEVICE_ID = "AI-CAM-01"
# The backend's schema (schemas.CameraDetectionIn) REQUIRES a gps
# {lat, lng} object with every detection - it has no "unknown
# location" option. Set this to where this camera is physically
# installed (e.g. the platform/entrance it covers).
CAMERA_LAT = 26.1445
CAMERA_LNG = 91.7362
# A lone camera detection only becomes a dashboard Alert once it's
# either paired with a handheld reading within fusion.TIME_WINDOW_SECONDS
# (30s), or that window expires and the backend's stale-sweep turns it
# into a solo alert. So a camera-only detection can take up to ~30s to
# show up on the dashboard - that's the fusion design, not a bug.
# ---- Output ----
ALERTS_DIR = "alerts"

