from ultralytics import YOLO
import config


class Detector:
    """
    YOLO detector for people and unattended-bag objects.
    """

    def __init__(
        self,
        model_path=config.MODEL_PATH,
        thresholds=config.CONFIDENCE_THRESHOLDS,
        imgsz=config.INFERENCE_SIZE,
    ):
        self.model = YOLO(model_path)
        self.thresholds = thresholds
        self.imgsz = imgsz

        self.wanted_classes = set(thresholds.keys())

        # Use the lowest threshold for YOLO's initial filter
        # so bag detections are not removed too early.
        self._yolo_conf = min(thresholds.values())

    def detect(self, frame):
        results = self.model(
            frame,
            verbose=False,
            imgsz=self.imgsz,
            conf=self._yolo_conf,
        )[0]

        detections = []

        for box in results.boxes:

            cls_id = int(box.cls[0])

            cls_name = self.model.names[cls_id]

            if cls_name not in self.wanted_classes:
                continue

            conf = float(box.conf[0])

            # Apply the correct confidence threshold
            # for this specific object class.
            if conf < self.thresholds[cls_name]:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            detections.append({
                "class_name": cls_name,
                "confidence": conf,
                "bbox": (x1, y1, x2, y2),
                "centroid": (
                    (x1 + x2) // 2,
                    (y1 + y2) // 2
                ),
            })

        return detections