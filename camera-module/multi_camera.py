"""
Runs the detector + tracker pipeline on several camera sources at
once (webcam + RTSP feeds + video files, any mix), each in its own
thread with its own window - closer to how a real CCTV control room
scans many feeds in parallel.

Note: within a SINGLE feed, detector.py/tracker.py already handle any
number of people and bags at once (they loop over every detection in
the frame) - this file is for running multiple separate CAMERAS at
once, not for detecting more objects per camera.

Usage:
    1. Edit CAMERA_SOURCES in config.py with your feeds, e.g.:
       CAMERA_SOURCES = [0, "rtsp://.../stream1", "videos/plat2.mp4"]
    2. python multi_camera.py
    3. Press 'q' in any window to stop that feed; Ctrl+C stops all.
"""

import threading
import cv2

from detector import Detector
from tracker import ObjectTracker
from alert_sender import send_alert
import config
import main as single_cam  # reuse draw_person / draw_object


def run_camera(source, cam_index):

    window_name = f"RailSentinel AI - Camera {cam_index}"

    # Each camera gets its OWN detector + tracker instance.
    # Sharing one Detector object across threads is unsafe with
    # some YOLO/torch backends, and sharing one tracker would mix
    # up bag IDs between unrelated cameras.
    detector = Detector()
    tracker = ObjectTracker()

    cap = single_cam.open_camera(source)

    if cap is None:
        print(f"[cam {cam_index}] Could not open source: {source}")
        return

    already_alerted = set()

    print(f"[cam {cam_index}] started on source: {source}")

    while True:

        ok, frame = cap.read()

        if not ok:
            print(f"[cam {cam_index}] stream ended.")
            break

        detections = detector.detect(frame)
        tracked_objects = tracker.update(detections)

        for det in detections:
            if det["class_name"] == "person":
                single_cam.draw_person(frame, det)

        for obj in tracked_objects:

            single_cam.draw_object(frame, obj)

            if (
                obj["threat_level"] == "HIGH"
                and not obj.get("predicted")
                and obj["object_id"] not in already_alerted
            ):
                # Tag which physical camera raised it so the
                # backend/dashboard can show the right device_id.
                obj_with_source = {
                    **obj,
                    "device_id": f"{config.DEVICE_ID}-{cam_index}",
                }
                send_alert(frame, obj_with_source)
                already_alerted.add(obj["object_id"])
                print(
                    f"[cam {cam_index}] ALERT "
                    f"{obj['class_name']} -> HIGH"
                )

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyWindow(window_name)


def main():

    sources = config.CAMERA_SOURCES

    if not sources:
        print("CAMERA_SOURCES is empty - add feeds in config.py")
        return

    threads = []

    for i, source in enumerate(sources):

        t = threading.Thread(
            target=run_camera,
            args=(source, i),
            daemon=True,
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()