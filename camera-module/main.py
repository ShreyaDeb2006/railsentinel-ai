import cv2
import numpy as np

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


def draw_person(frame, det):

    x1, y1, x2, y2 = det["bbox"]

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 180, 0),
        2
    )

    cv2.putText(
        frame,
        "person",
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 180, 0),
        2
    )


def draw_object(frame, det):

    x1, y1, x2, y2 = det["bbox"]

    color = COLORS[
        det["threat_level"]
    ]

    thickness = 1 if det.get("predicted") else 2

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        thickness
    )

    label = (
        f"{det['class_name']} "
        f"[{det['threat_level']}] "
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
    Tries a few different OpenCV backends before giving up.
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


def resize_to_screen(
    frame,
    screen_width,
    screen_height
):
    """
    Fits the camera frame to the entire screen
    while preserving its original aspect ratio.
    """

    frame_height, frame_width = frame.shape[:2]

    scale = min(
        screen_width / frame_width,
        screen_height / frame_height
    )

    new_width = int(frame_width * scale)
    new_height = int(frame_height * scale)

    resized = cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    output = np.zeros(
        (screen_height, screen_width, 3),
        dtype=frame.dtype
    )

    x = (screen_width - new_width) // 2
    y = (screen_height - new_height) // 2

    output[y:y + new_height, x:x + new_width] = resized

    return output


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

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    screen_width = 1920
    screen_height = 1080

    print("Running RailSentinel AI.")
    print("Press 'q' to quit.")

    already_alerted = set()
    printed_frame_shape = False

    while True:

        ok, frame = cap.read()

        if not ok:
            print("End of stream.")
            break

        if not printed_frame_shape:
            h, w = frame.shape[:2]
            print(f"Actual first captured frame shape: {w}x{h}")
            printed_frame_shape = True

        detections = detector.detect(frame)
        tracked_objects = tracker.update(detections)

        for det in detections:
            if det["class_name"] == "person":
                draw_person(frame, det)

        for obj in tracked_objects:

            draw_object(frame, obj)

            if (
                obj["threat_level"] == "HIGH"
                and not obj.get("predicted")
                and obj["object_id"] not in already_alerted
            ):
                send_alert(frame, obj)
                already_alerted.add(obj["object_id"])
                secs = obj["unattended_seconds"]
                print(f"[ALERT] {obj['class_name']} unattended {secs}s -> HIGH")

        display_frame = resize_to_screen(frame, screen_width, screen_height)
        cv2.imshow(WINDOW_NAME, display_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()