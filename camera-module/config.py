# ============================================================
# DEBUG
# ============================================================
# When True, every stage prints what it's doing: raw YOLO output,
# what got filtered, tracker state, person/bag association reasoning,
# threat decisions, and the backend request/response.
DEBUG = False


# ============================================================
# CAMERA
# ============================================================
CAMERA_SOURCE = 0
# 0 = laptop webcam. Can also be a video file path or RTSP URL.

CAMERA_SOURCES = [
    0,
    # "rtsp://user:pass@192.168.1.10/stream1",
    # "videos/platform2.mp4",
]

# The webcam is never told what resolution to capture at otherwise,
# and can silently default to something low (often 640x480). This
# requests a higher capture resolution; if the hardware doesn't
# support it, OpenCV falls back to its native max (logged either way).
REQUESTED_CAMERA_WIDTH = 1280
REQUESTED_CAMERA_HEIGHT = 720


# ============================================================
# MODEL
# ============================================================
MODEL_PATH = "yolov8n.pt"
# Downloads automatically on first run. yolov8n = fastest/least
# accurate; yolov8s is a meaningful accuracy upgrade at a modest
# speed cost if your hardware can keep up.

CONFIDENCE_THRESHOLD = 0.30
# General floor for accepting a raw detection at all.

MODEL_IMG_SIZE = 1120
# Must be a multiple of 32. Higher = more detail on small/far
# objects, at a speed cost. 640 is the YOLO default.

DEVICE = "cpu"
# "cpu", "cuda" (Nvidia GPU), or "mps" (Apple Silicon).


# ============================================================
# CLASSES
# ============================================================
# backpack/handbag/suitcase are treated as ONE "bag" category for
# tracking and threat purposes - the exact subclass YOLO reports is
# unreliable (a single physical bag can flicker between these labels
# frame to frame) and shouldn't drive security decisions. The
# specific subclass is still tracked and reported (stabilized via a
# short rolling majority-vote) for logging/display, but never causes
# tracking discontinuity or affects threat logic.
BAG_CLASSES = {"backpack", "handbag", "suitcase"}

PERSON_CLASS = "person"


# ============================================================
# PER-CLASS CONFIDENCE (single-frame acceptance floor)
# ============================================================
# NOTE: earlier versions of this file used a HIGHER floor for
# "person" (0.55) to fight single-frame noise. Real-world testing
# showed this doesn't fix instability, it just moves the flicker
# boundary (a person hovering at 0.50-0.60 confidence still flickers
# in/out, just at a different cutoff). The actual fix for that is
# temporal confirmation in tracker.py (see PERSON_CONFIRM_SEC below),
# so this floor is back down near the general threshold - it only
# exists to reject obvious single-frame noise, not to provide
# stability on its own.
PER_CLASS_CONFIDENCE = {
    "person": 0.40,
}


# ============================================================
# TRACKING - shared by both person tracks and bag tracks
# ============================================================
MATCH_DISTANCE_PX = 80
# Max centroid distance to match a new detection to an existing track.

TRACK_GRACE_SEC = 1.5
# How long a track is kept "alive" (drawn/considered) at its last
# known position after a frame where it wasn't (re)detected - this is
# what stops a box from flickering off/on when the object hasn't
# actually moved, and what lets person-bag association survive the
# model alternating which label it gives the SAME physical object
# from one frame to the next.

TRACK_FORGET_SEC = 5
# How long with ZERO detections before a track is fully deleted and
# its ID freed up.

BAG_CLASS_HISTORY_LEN = 7
# How many recent per-frame class labels a bag track remembers to
# pick a STABLE displayed subclass (majority vote) instead of
# flickering "backpack"/"suitcase" every frame the raw label changes.


# ============================================================
# PERSON CONFIRMATION
# ============================================================
# A brand new person track must exist for at least this long
# (tolerating grace-period gaps, same as bags) before it's treated as
# "confirmed" - i.e. trusted to fully mark a bag as attended. This is
# what fixes single-frame confidence oscillation around the
# PER_CLASS_CONFIDENCE floor (Failure 4): the track survives the dip
# via TRACK_GRACE_SEC, and a momentary appearance doesn't instantly
# grant/revoke "attended" status either way.
PERSON_CONFIRM_SEC = 1.0

# A person who is nearby but NOT YET confirmed still counts as WEAK
# evidence: it prevents an immediate jump straight to HIGH, but
# doesn't fully reset the unattended timer either. This handles
# "someone just walked up to grab the bag" without a false HIGH in
# the ~1s before their track confirms, while still not letting a
# bare, fleeting, unconfirmed detection indefinitely protect a truly
# abandoned bag.
WEAK_ASSOCIATION_CAP_SEC = 4.0
# How long weak (unconfirmed-person) evidence caps the threat level
# at UNCERTAIN before HIGH can fire again if nothing stronger arrives.


# ============================================================
# PERSON <-> BAG ASSOCIATION ("is this bag attended?")
# ============================================================
PERSON_PROXIMITY_PX = 180
# Centroid distance under which a person standing near a bag counts
# as association ("standing next to their bag").

BAG_HOLD_IOU_THRESHOLD = 0.15
# Box overlap above which a person is treated as holding/carrying the
# bag. Deliberately LOW and used only as ASSOCIATION evidence, never
# to delete/suppress either box - a real person carrying a real bag
# routinely overlaps it heavily, and treating that as "these must be
# the same misdetected object, delete one" was a real bug in an
# earlier version of this file. Overlap is positive evidence the bag
# is attended, nothing more.


# ============================================================
# THREAT ESCALATION (time WITHOUT attendance)
# ============================================================
UNCERTAIN_AFTER_SEC = 5
HIGH_ALERT_AFTER_SEC = 10


# ============================================================
# ALERTING
# ============================================================
ALERT_COOLDOWN_SEC = 60
# Minimum time before re-alerting on a bag at essentially the same
# location, even if tracking briefly lost it and it came back under a
# new track ID. Prevents alert spam from ID churn on a single
# real-world abandoned bag.

ALERT_COOLDOWN_PX = 100
# "Same location" radius (pixels) for the cooldown above.

BACKEND_TIMEOUT_SEC = 2

BACKEND_DOWN_BACKOFF_SEC = 15
# After a failed backend connection, don't retry for this long -
# keeps a down backend from adding a ~2s stall to the frame loop on
# every single alert while it's unreachable.


# ============================================================
# BACKEND INTEGRATION
# ============================================================
# MUST match backend/main.py's actual endpoint: POST /api/camera-
# detection on port 8000 (uvicorn's default). /api/alerts is GET-only
# (for the dashboard to read already-fused alerts back out) and
# posting there fails silently from the camera module's point of view.
BACKEND_API_URL = "http://localhost:8000/api/camera-detection"

DEVICE_ID = "AI-CAM-01"

# backend/schemas.py:CameraDetectionIn REQUIRES a gps {lat, lng}
# object on every detection. Set this to where this camera is
# physically installed.
CAMERA_LAT = 26.1445
CAMERA_LNG = 91.7362

# A lone camera detection only becomes a dashboard Alert once it's
# paired with a handheld reading within fusion.TIME_WINDOW_SECONDS
# (30s), or that window expires and the backend's stale-sweep turns
# it into a solo alert - so it can take up to ~30s to appear on the
# dashboard. That's the fusion design, not a bug.


# ============================================================
# OUTPUT
# ============================================================
ALERTS_DIR = "alerts"
