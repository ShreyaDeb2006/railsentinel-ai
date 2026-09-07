from ultralytics import YOLO
import config


class Detector:
    """
    YOLO detector for people and bag-type objects (backpack/handbag/
    suitcase). Responsible ONLY for: run the model, filter to classes
    we care about, filter by confidence. It does NOT try to resolve
    person/bag relationships - that's tracker.py's job, using
    temporal + spatial evidence across frames, not a single frame's
    raw boxes.

    CORRECTION from an earlier version: this file used to drop a
    "person" box whenever it overlapped a bag box above an IoU
    threshold, on the theory that heavy overlap meant the model was
    double-labeling one physical object. Real-world testing proved
    that wrong - a person GENUINELY carrying a bag produces exactly
    the same kind of overlap, and that rule deleted real person
    detections during completely normal carrying (a false negative on
    the person, which is dangerous for the "is this bag attended"
    logic). Overlap is legitimate association evidence, not grounds
    for deleting a detection - that reasoning now lives in
    tracker.py's association step, and BOTH boxes are always kept
    here.
    """

    def __init__(
        self,
        model_path=config.MODEL_PATH,
        confidence=config.CONFIDENCE_THRESHOLD,
        img_size=config.MODEL_IMG_SIZE,
        device=config.DEVICE,
        debug=None,
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.img_size = img_size
        self.device = device
        self.debug = config.DEBUG if debug is None else debug

        self.wanted_classes = {config.PERSON_CLASS} | config.BAG_CLASSES

        self.per_class_confidence = dict(config.PER_CLASS_CONFIDENCE)

        # The raw model call needs its own conf= floor to be AT MOST
        # the lowest of any per-class override - otherwise Ultralytics
        # itself throws away boxes below the general threshold before
        # our per-class logic ever sees them, silently making a lower
        # per-class override meaningless. (This was a real bug: a
        # per-class "person" floor of 0.40 did nothing when the
        # general threshold passed to the model was 0.45, because
        # anything between 0.40-0.45 never came back from the model
        # call at all.)
        self._model_call_conf = min(
            [self.confidence] + list(self.per_class_confidence.values())
        )

    def _raw_predict(self, frame):

        results = self.model(
            frame,
            verbose=False,
            conf=self._model_call_conf,
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

    def _class_and_confidence_filter(self, raw):

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

    def detect(self, frame):

        raw = self._raw_predict(frame)

        filtered = self._class_and_confidence_filter(raw)

        detections = []

        for d in filtered:

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
            summary = ", ".join(
                f"{d['class_name']}({d['confidence']:.2f})"
                for d in detections
            )
            print(f"[FILTER] final detections: {summary or 'none'}")

        return detections
