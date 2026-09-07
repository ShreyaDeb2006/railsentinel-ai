"""
Runs the detector + tracker pipeline on several camera sources at
once (webcam + RTSP feeds + video files, any mix), each in its own
thread with its own window - closer to how a real CCTV control room
scans many feeds in parallel.

This now delegates the actual per-frame loop to main.run() instead of
reimplementing it, so multi-camera mode automatically gets whatever
main.py has (person drawing, alert cooldown, exception handling,
fullscreen toggle) without needing to be kept in sync by hand.

Usage:
    1. Edit CAMERA_SOURCES in config.py with your feeds, e.g.:
       CAMERA_SOURCES = [0, "rtsp://.../stream1", "videos/plat2.mp4"]
    2. python multi_camera.py
    3. Press 'q' in a window to stop that feed, 'f' to toggle
       fullscreen for it. Ctrl+C in the terminal stops all of them.
"""

import threading

from detector import Detector
from tracker import ObjectTracker
import config
import main as single_cam


def run_camera(source, cam_index):

    window_name = f"RailSentinel AI - Camera {cam_index}"

    # Each camera gets its OWN detector + tracker instance. Sharing
    # one Detector across threads is unsafe with some YOLO/torch
    # backends, and sharing one tracker would mix up person/bag IDs
    # between physically unrelated cameras.
    detector = Detector()
    tracker = ObjectTracker()

    cap = single_cam.open_camera(source)

    if cap is None:
        print(f"[cam {cam_index}] Could not open source: {source}")
        return

    device_id = f"{config.DEVICE_ID}-{cam_index}"

    print(f"[cam {cam_index}] started on source: {source}")

    single_cam.run(cap, detector, tracker, window_name, device_id=device_id)


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

    try:
        for t in threads:
            # join with a timeout so KeyboardInterrupt is actually
            # noticed promptly instead of blocking forever on join()
            while t.is_alive():
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        print("\nInterrupted (Ctrl+C) - individual camera windows will "
              "close as their threads finish their current frame.")


if __name__ == "__main__":
    main()
