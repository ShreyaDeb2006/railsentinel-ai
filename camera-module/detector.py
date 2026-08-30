from ultralytics import YOLO
import config


class Detector:
    """
    YOLO detector for people and unattended-bag objects.
    """

    def __init__(
        self,
        model_path=config.MODEL_PATH,
        confidence=config.CONFIDENCE_THRESHOLD
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence

        self.wanted_classes = {
            "person",
            "backpack",
            "handbag",
            "suitcase"
        }

    def detect(self, frame):
        results = self.model(
            frame,
            verbose=False,
            conf=self.confidence
        )[0]

        detections = []

        for box in results.boxes:

            cls_id = int(box.cls[0])

            cls_name = self.model.names[cls_id]

            if cls_name not in self.wanted_classes:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            conf = float(box.conf[0])

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