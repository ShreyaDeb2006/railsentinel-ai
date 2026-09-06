from ultralytics import YOLO
import config


BAG_CLASSES = {"backpack", "handbag", "suitcase"}


def _iou(box_a, box_b):
    """Standard intersection-over-union between two (x1,y1,x2,y2) boxes."""

    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])

    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)
    inter_area = inter_w * inter_h

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

    union = area_a + area_b - inter_area

    return inter_area / union if union > 0 else 0.0


class Detector:
    """
    YOLO detector for people and unattended-bag objects.
    """

    # How much a "person" box has to overlap a bag box before we
    # treat them as the SAME physical object being double-labeled
    # (rather than two genuinely separate things standing near each
    # other). 0.4 was chosen because a real standing person and a
    # real nearby bag essentially never share 40%+ of each other's
    # box area - only a misclassification of the same object does.
    PERSON_BAG_OVERLAP_IOU = 0.4

    def __init__(
        self,
        model_path=config.MODEL_PATH,
        confidence=config.CONFIDENCE_THRESHOLD,
        img_size=config.MODEL_IMG_SIZE,
        device=config.DEVICE,
        debug=getattr(config, "DEBUG", False),
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.img_size = img_size
        self.device = device
        self.debug = debug

        self.wanted_classes = {
            "person",
            "backpack",
            "handbag",
            "suitcase"
        }

        # Bags are much easier to confuse with a person than a person
        # is to confuse with a bag. A slightly higher confidence floor
        # specifically on "person" cuts down on low-confidence noise,
        # without touching real bags. This is a SEPARATE fix from the
        # overlap-resolution below - this one helps with weak/noisy
        # person guesses in general; the overlap check below handles
        # the specific "person box drawn on top of a bag" symptom.
        self.per_class_confidence = {
            "person": max(confidence, 0.55),
        }

    def _raw_predict(self, frame):

        results = self.model(
            frame,
            verbose=False,
            conf=self.confidence,
            imgsz=self.img_size,
            device=self.device,
        )[0]

        raw = []

        for box in results.boxes:

            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            raw.append({
                "class_name": cls_name,
                "confidence": conf,
                "bbox": (x1, y1, x2, y2),
            })

        if self.debug:
            print("[YOLO] raw detections this frame:")
            for r in raw:
                print(
                    f"   {r['class_name']:<10} "
                    f"{r['confidence']:.2f}  bbox={r['bbox']}"
                )
            if not raw:
                print("   (nothing above conf threshold)")

        return raw

    def _class_filter(self, raw):

        kept = []

        for r in raw:

            if r["class_name"] not in self.wanted_classes:
                continue

            min_conf = self.per_class_confidence.get(
                r["class_name"], self.confidence
            )

            if r["confidence"] < min_conf:
                if self.debug:
                    print(
                        f"[FILTER] dropped {r['class_name']} "
                        f"(conf {r['confidence']:.2f} < "
                        f"required {min_conf:.2f})"
                    )
                continue

            kept.append(r)

        return kept

    def _resolve_person_bag_overlap(self, dets):
        """
        THE core fix: when a "person" box and a bag box overlap
        heavily, they almost certainly represent YOLO hedging on the
        SAME physical object, not two separate things. Keep the bag
        label and drop the overlapping person box - genuinely
        separate, non-overlapping people are completely untouched by
        this, so "person nearby" logic for real people still works.
        """

        persons = [d for d in dets if d["class_name"] == "person"]
        bags = [d for d in dets if d["class_name"] in BAG_CLASSES]
        others = [
            d for d in dets
            if d["class_name"] not in BAG_CLASSES
            and d["class_name"] != "person"
        ]

        drop_indices = set()

        for p_idx, p in enumerate(persons):
            for b in bags:

                overlap = _iou(p["bbox"], b["bbox"])

                if overlap >= self.PERSON_BAG_OVERLAP_IOU:

                    drop_indices.add(p_idx)

                    if self.debug:
                        print(
                            f"[FILTER] dropped overlapping person box "
                            f"(IoU={overlap:.2f} with {b['class_name']} "
                            f"conf {b['confidence']:.2f}) - treating as "
                            f"the same object, keeping the bag label"
                        )

        kept_persons = [
            p for i, p in enumerate(persons) if i not in drop_indices
        ]

        return kept_persons + bags + others

    def detect(self, frame):

        raw = self._raw_predict(frame)

        filtered = self._class_filter(raw)

        resolved = self._resolve_person_bag_overlap(filtered)

        detections = []

        for d in resolved:

            x1, y1, x2, y2 = d["bbox"]

            detections.append({
                "class_name": d["class_name"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "centroid": (
                    (x1 + x2) // 2,
                    (y1 + y2) // 2
                ),
            })

        if self.debug:
            print(
                "[FILTER] final detections: "
                + ", ".join(
                    f"{d['class_name']}({d['confidence']:.2f})"
                    for d in detections
                ) or "[FILTER] final detections: none"
            )

        return detections