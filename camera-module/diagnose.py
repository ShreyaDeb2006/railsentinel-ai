"""
Standalone diagnostic script - shows two things side by side, clearly
labeled, for a single image or webcam frame:

  1. RAW YOLO OUTPUT: every detection across all 80 COCO classes,
     straight from the model, before any of this project's filtering.
  2. PRODUCTION FILTERED OUTPUT: exactly what camera-module's actual
     Detector class (detector.py) keeps after class + confidence
     filtering - the same code main.py uses, run in DEBUG mode so you
     see the accept/reject reasoning too.

No tracker, no threat logic, no backend calls either way - this
isolates "what does YOLO see" from everything downstream of it.

Usage:
    python diagnose.py path/to/photo.jpg
    python diagnose.py --webcam
    python diagnose.py path/to/photo.jpg --imgsz 1280 --conf 0.1
    python diagnose.py path/to/photo.jpg --model yolov8s.pt
    python diagnose.py path/to/photo.jpg --save-boxes out.jpg
"""

import argparse
import sys

import cv2
from ultralytics import YOLO

import config
from detector import Detector


def run_raw(model, frame, imgsz, conf):

    results = model(frame, verbose=False, conf=conf, imgsz=imgsz)[0]

    rows = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        rows.append((cls_name, confidence, (x1, y1, x2, y2)))

    rows.sort(key=lambda r: r[1], reverse=True)

    return rows


def print_table(title, rows):

    print(f"\n{title}")
    print(f"{'CLASS':<15}{'CONFIDENCE':<12}BBOX")
    print("-" * 55)

    if not rows:
        print("(no detections above the confidence threshold)")
        return

    for cls_name, confidence, bbox in rows:
        print(f"{cls_name:<15}{confidence:<12.2f}{bbox}")


def draw_and_save(frame, raw_rows, production_dets, out_path):

    annotated = frame.copy()

    for cls_name, confidence, (x1, y1, x2, y2) in raw_rows:
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (128, 128, 128), 1)
        cv2.putText(
            annotated, f"{cls_name} {confidence:.2f}", (x1, max(15, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1,
        )

    for d in production_dets:
        x1, y1, x2, y2 = d["bbox"]
        color = (0, 255, 0) if d["class_name"] != "person" else (255, 180, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated, f"KEPT: {d['class_name']} {d['confidence']:.2f}",
            (x1, min(annotated.shape[0] - 5, y2 + 20)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
        )

    cv2.imwrite(out_path, annotated)
    print(f"\nSaved annotated image to: {out_path}")
    print("(thin gray = raw YOLO, all classes | thick colored = kept by production Detector)")


def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", help="Path to a single image to test")
    parser.add_argument("--webcam", action="store_true", help="Grab one frame from the webcam")
    parser.add_argument("--model", default=config.MODEL_PATH)
    parser.add_argument("--imgsz", type=int, default=config.MODEL_IMG_SIZE)
    parser.add_argument(
        "--conf", type=float, default=0.10,
        help="Confidence floor for the RAW table only (deliberately low "
             "so you can see everything, including things the production "
             "pipeline would reject). Production filtering always uses "
             "config.py's real thresholds, not this value.",
    )
    parser.add_argument("--save-boxes", metavar="OUT.jpg", default=None)

    args = parser.parse_args()

    if not args.image and not args.webcam:
        parser.error("Provide an image path, or use --webcam")

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

    # ---- 1. RAW: every class, low confidence floor, straight from YOLO ----
    print(f"\nLoading model for raw pass: {args.model}")
    raw_model = YOLO(args.model)
    raw_rows = run_raw(raw_model, frame, args.imgsz, args.conf)
    print_table(
        f"RAW YOLO OUTPUT (all 80 classes, conf >= {args.conf}, imgsz={args.imgsz})",
        raw_rows,
    )

    # ---- 2. PRODUCTION: the actual Detector class, actual config thresholds ----
    print(
        f"\nRunning PRODUCTION Detector (detector.py) with real config.py "
        f"thresholds, DEBUG on so you see accept/reject reasoning:"
    )
    prod_detector = Detector(
        model_path=args.model, img_size=args.imgsz, debug=True
    )
    production_dets = prod_detector.detect(frame)

    print_table("PRODUCTION FILTERED OUTPUT (what main.py actually sees)", [
        (d["class_name"], d["confidence"], d["bbox"]) for d in production_dets
    ])

    if args.save_boxes:
        draw_and_save(frame, raw_rows, production_dets, args.save_boxes)


if __name__ == "__main__":
    main()
