"""
Standalone diagnostic script - runs ONLY YOLO detection on a single
image or a live webcam frame. No tracker, no threat logic, no
backend calls. Use this to answer one question in isolation: what is
YOLO actually seeing and how confident is it, before any of the
camera-module's other logic touches it.

Usage:
    python diagnose.py path/to/photo.jpg
    python diagnose.py --webcam
    python diagnose.py path/to/photo.jpg --imgsz 1280 --conf 0.1
    python diagnose.py path/to/photo.jpg --model yolov8s.pt
    python diagnose.py path/to/photo.jpg --save-boxes out.jpg

Prints every raw detection YOLO returns for ALL 80 COCO classes (not
just person/backpack/handbag/suitcase) so you can see if something
odd is winning the argument - e.g. "suitcase" or "chair" instead of
either "person" or "backpack".
"""

import argparse
import sys

import cv2
from ultralytics import YOLO


def run_on_frame(model, frame, imgsz, conf):

    results = model(
        frame,
        verbose=False,
        conf=conf,
        imgsz=imgsz,
    )[0]

    rows = []

    for box in results.boxes:

        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        rows.append((cls_name, confidence, (x1, y1, x2, y2)))

    rows.sort(key=lambda r: r[1], reverse=True)

    return rows


def print_table(rows):

    print(f"{'CLASS':<15}{'CONFIDENCE':<12}BBOX")
    print("-" * 55)

    if not rows:
        print("(no detections above the confidence threshold)")
        return

    for cls_name, confidence, bbox in rows:
        print(f"{cls_name:<15}{confidence:<12.2f}{bbox}")


def draw_and_save(frame, rows, out_path):

    for cls_name, confidence, (x1, y1, x2, y2) in rows:

        color = (0, 255, 0) if cls_name != "person" else (255, 180, 0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            frame,
            f"{cls_name} {confidence:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    cv2.imwrite(out_path, frame)
    print(f"\nSaved annotated image to: {out_path}")


def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", help="Path to a single image to test")
    parser.add_argument("--webcam", action="store_true", help="Grab one frame from the webcam")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--conf", type=float, default=0.10)
    parser.add_argument("--save-boxes", metavar="OUT.jpg", default=None)

    args = parser.parse_args()

    if not args.image and not args.webcam:
        parser.error("Provide an image path, or use --webcam")

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    if args.webcam:
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            print("Could not read a frame from the webcam.")
            sys.exit(1)
    else:
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Could not read image: {args.image}")
            sys.exit(1)

    h, w = frame.shape[:2]
    print(f"Input frame size: {w}x{h}")
    print(f"Running inference at imgsz={args.imgsz}, conf={args.conf}\n")

    rows = run_on_frame(model, frame, args.imgsz, args.conf)
    print_table(rows)

    if args.save_boxes:
        draw_and_save(frame, rows, args.save_boxes)


if __name__ == "__main__":
    main()