import time

import cv2

from detector import Detector
from tracker import ObjectTracker
from alert_sender import send_alert
import config


WINDOW_NAME = "RailSentinel AI - Camera Module"


COLORS = {
    "LOW": (0, 200, 0),
    "UNCERTAIN": (0, 200, 255),
    "HIGH": (0, 0, 255),
}

PERSON_COLOR = (255, 180, 0)
PERSON_COLOR_UNCONFIRMED = (180, 130, 0)


def draw_person(frame, det):

    x1, y1, x2, y2 = det["bbox"]

    confirmed = det.get("confirmed", True)
    color = PERSON_COLOR if confirmed else PERSON_COLOR_UNCONFIRMED
    thickness = 1 if det.get("predicted") else 2

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    label = "person" if confirmed else "person?"

    cv2.putText(
        frame,
        label,
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2
    )


def draw_object(frame, det):

    x1, y1, x2, y2 = det["bbox"]

    color = COLORS[det["threat_level"]]

    # "predicted" = this frame's YOLO pass missed/low-confidence'd the
    # bag, so we're drawing its last known position from the
    # tracker's grace period instead of a fresh detection.
    thickness = 1 if det.get("predicted") else 2

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    attended_tag = " (attended)" if det.get("attended") else ""

    label = (
        f"{det['class_name']} "
        f"[{det['threat_level']}]{attended_tag} "
        f"{det['unattended_seconds']}s"
    )

    cv2.putText(
        frame,
        label,
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2
    )


def open_camera(source):
    """
    Tries a few different OpenCV backends before giving up. A plain
    cv2.VideoCapture(source) can fail to open a perfectly working
    webcam on some Windows/Linux setups depending on which backend
    OpenCV picks by default.
    """

    backends_to_try = [
        (None, "default"),
        (getattr(cv2, "CAP_DSHOW", None), "CAP_DSHOW (Windows)"),
        (getattr(cv2, "CAP_MSMF", None), "CAP_MSMF (Windows)"),
        (getattr(cv2, "CAP_V4L2", None), "CAP_V4L2 (Linux)"),
    ]

    for backend, label in backends_to_try:

        if backend is None and label != "default":
            continue

        cap = (
            cv2.VideoCapture(source)
            if backend is None
            else cv2.VideoCapture(source, backend)
        )

        if cap.isOpened():
            print(f"Camera opened using backend: {label}")
            return cap

        cap.release()
        print(f"Backend failed: {label}")

    return None


def run(cap, detector, tracker, window_name, device_id=None):
    """
    Shared frame loop, used by both single-camera main() and (via
    multi_camera.py) each camera's own thread. No hardcoded screen
    size - the window is created resizable at the camera's own
    resolution; press 'f' to toggle OS-level fullscreen (which scales
    to whatever monitor the window is actually on), 'q' to quit.
    """

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    fullscreen = False

    alerted_ids = set()  # currently-HIGH ids we've already sent an alert for

    printed_frame_shape = False

    frame_count = 0
    fps_timer = time.time()

    try:

        while True:

            ok, frame = cap.read()

            if not ok:
                print(f"[{window_name}] End of stream / camera read failed.")
                break

            if not printed_frame_shape:
                h, w = frame.shape[:2]
                print(f"[{window_name}] Actual first captured frame: {w}x{h}")
                printed_frame_shape = True

            try:

                detections = detector.detect(frame)
                tracked_bags = tracker.update(detections)
                tracked_persons = tracker.get_visible_persons()

                for p in tracked_persons:
                    draw_person(frame, p)

                for obj in tracked_bags:

                    draw_object(frame, obj)

                    is_high = obj["threat_level"] == "HIGH"

                    if is_high and not obj.get("predicted"):

                        if obj["object_id"] not in alerted_ids:

                            payload = dict(obj)
                            if device_id:
                                payload["device_id"] = device_id

                            send_alert(frame, payload)
                            alerted_ids.add(obj["object_id"])

                            print(
                                f"[{window_name}] [ALERT] {obj['class_name']} "
                                f"unattended {obj['unattended_seconds']}s -> HIGH"
                            )

                    elif not is_high and obj["object_id"] in alerted_ids:
                        # Bag became attended/uncertain again - allow a
                        # FUTURE separate unattended episode on this
                        # same track to alert again, instead of being
                        # silenced forever after the first alert.
                        alerted_ids.discard(obj["object_id"])

            except Exception as exc:  # noqa: BLE001 - see comment below
                # A single bad frame (corrupt read, transient YOLO
                # hiccup, etc.) should never take down the whole
                # camera loop. Log it and keep going - the alternative
                # is a live security camera silently dying.
                print(f"[{window_name}] Frame processing error (skipping frame): {exc}")

            if config.DEBUG:
                frame_count += 1
                if time.time() - fps_timer >= 5:
                    fps = frame_count / (time.time() - fps_timer)
                    print(f"[{window_name}] ~{fps:.1f} FPS")
                    frame_count = 0
                    fps_timer = time.time()

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("f"):
                fullscreen = not fullscreen
                cv2.setWindowProperty(
                    window_name,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL,
                )

    finally:

        cap.release()
        cv2.destroyWindow(window_name)


def main():

    print("Starting RailSentinel AI...")

    detector = Detector()
    tracker = ObjectTracker()

    cap = open_camera(config.CAMERA_SOURCE)

    if cap is None:
        print(
            "Could not open camera/video source "
            f"({config.CAMERA_SOURCE!r}) with any backend."
        )
        print("- Check CAMERA_SOURCE in config.py is the right index/path/URL.")
        print("- Check no other application is already holding the camera.")
        print("- Check the OS actually granted this program camera permission.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUESTED_CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUESTED_CAMERA_HEIGHT)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(
        f"Camera capture resolution: {actual_w}x{actual_h} "
        f"(requested {config.REQUESTED_CAMERA_WIDTH}x{config.REQUESTED_CAMERA_HEIGHT})"
    )
    print(f"YOLO inference resolution (imgsz): {config.MODEL_IMG_SIZE}")
    print("Running RailSentinel AI. Press 'q' to quit, 'f' to toggle fullscreen.")

    try:
        run(cap, detector, tracker, WINDOW_NAME)
    except KeyboardInterrupt:
        print("\nInterrupted (Ctrl+C) - shutting down cleanly.")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
