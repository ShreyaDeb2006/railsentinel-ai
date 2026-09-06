"""
Runs the detector + tracker pipeline on several camera sources at
once (webcam + RTSP feeds + video files, any mix), each in its own
thread with its own window.

Usage:
    1. Edit CAMERA_SOURCES in config.py with your feeds.
    2. python multi_camera.py
    3. Press 'q' in any window to stop that feed; Ctrl+C stops all.
"""

import threading
import cv2

from detector import Detector
from tracker import ObjectTracker
from alert_sender import send_alert
import config
import main as single_cam


def run_camera(source, cam_index):

    window_name = f"RailSentinel AI - Camera {cam_index}"

    detector = Detector()
    tracker = ObjectTracker()

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
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
                obj_with_source = {
                    **obj,
                    "device_id": f"{config.DEVICE_ID}-{cam_index}",
                }
                send_alert(frame, obj_with_source)
                already_alerted.add(obj["object_id"])
                print(f"[cam {cam_index}] ALERT {obj['class_name']} -> HIGH")

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
        t = threading.Thread(target=run_camera, args=(source, i), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()