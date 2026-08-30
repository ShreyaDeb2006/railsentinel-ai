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

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        2
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


def resize_to_screen(
    frame,
    screen_width,
    screen_height
):
    """
    Fits the camera frame to the entire screen
    while preserving its original aspect ratio.

    Empty areas are filled with black instead
    of stretching the image.
    """

    frame_height, frame_width = frame.shape[:2]

    scale = min(
        screen_width / frame_width,
        screen_height / frame_height
    )

    new_width = int(
        frame_width * scale
    )

    new_height = int(
        frame_height * scale
    )

    resized = cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    output = np.zeros(
        (
            screen_height,
            screen_width,
            3
        ),
        dtype=frame.dtype
    )

    x = (
        screen_width - new_width
    ) // 2

    y = (
        screen_height - new_height
    ) // 2

    output[
        y:y + new_height,
        x:x + new_width
    ] = resized

    return output


def main():

    print("Starting RailSentinel AI...")

    # -----------------------------
    # Create detector and tracker
    # -----------------------------

    detector = Detector()

    tracker = ObjectTracker()

    # -----------------------------
    # Open camera
    # -----------------------------

    cap = cv2.VideoCapture(
        config.CAMERA_SOURCE
    )

    if not cap.isOpened():

        print(
            "Could not open camera/video source."
        )

        print(
            "Check CAMERA_SOURCE in config.py"
        )

        return

    # -----------------------------
    # Create full-screen window
    # -----------------------------

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL
    )

    cv2.setWindowProperty(
        WINDOW_NAME,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    # -----------------------------
    # Get screen size
    # -----------------------------

    screen_width = 1920
    screen_height = 1080

    print(
        "Running RailSentinel AI."
    )

    print(
        "Press 'q' to quit."
    )

    # -----------------------------
    # Track alerts already sent
    # -----------------------------

    already_alerted = set()

    # -----------------------------
    # Main camera loop
    # -----------------------------

    while True:

        ok, frame = cap.read()

        if not ok:

            print(
                "End of stream."
            )

            break

        # -------------------------
        # YOLO detection
        # -------------------------

        detections = detector.detect(
            frame
        )

        # -------------------------
        # Threat tracking
        # -------------------------

        tracked_objects = tracker.update(
            detections
        )

        # -------------------------
        # Draw people
        # -------------------------

        for det in detections:

            if det["class_name"] == "person":

                draw_person(
                    frame,
                    det
                )

        # -------------------------
        # Draw bags and alerts
        # -------------------------

        for obj in tracked_objects:

            draw_object(
                frame,
                obj
            )

            # ---------------------
            # HIGH alert
            # ---------------------

            if (
                obj["threat_level"] == "HIGH"
                and
                obj["object_id"]
                not in already_alerted
            ):

                send_alert(
                    frame,
                    obj
                )

                already_alerted.add(
                    obj["object_id"]
                )

                secs = (
                    obj["unattended_seconds"]
                )

                print(
                    f"[ALERT] "
                    f"{obj['class_name']} "
                    f"unattended "
                    f"{secs}s -> HIGH"
                )

        # -------------------------
        # Resize without stretching
        # -------------------------

        display_frame = resize_to_screen(
            frame,
            screen_width,
            screen_height
        )

        # -------------------------
        # Show frame
        # -------------------------

        cv2.imshow(
            WINDOW_NAME,
            display_frame
        )

        # -------------------------
        # Quit with Q
        # -------------------------

        if (
            cv2.waitKey(1) & 0xFF
            == ord("q")
        ):

            break

    # -----------------------------
    # Clean up
    # -----------------------------

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()