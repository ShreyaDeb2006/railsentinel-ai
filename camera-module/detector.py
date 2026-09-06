from ultralytics import YOLO
import config


class Detector:
    """
    YOLO detector for people and unattended-bag objects.
    """

    def __init__(
        self,
        model_path=config.MODEL_PATH,
        confidence=config.CONFIDENCE_THRESHOLD,
        img_size=config.MODEL_IMG_SIZE,
        device=config.DEVICE,
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.img_size = img_size
        self.device = device

        self.wanted_classes = {
            "person",
            "backpack",
            "handbag",
            "suitcase"
        }

        # Bags are much easier to confuse with a person than a person
        # is to confuse with a bag (a slouched/partial person looks a
        # bit like a blob, same as a bag). Asking for a slightly
        # higher confidence specifically on "person" cuts down on
        # bags getting mislabeled as low-confidence people, without
        # making the model miss real bags.
        self.per_class_confidence = {
            "person": max(confidence, 0.55),
        }

    def detect(self, frame):
        results = self.model(
            frame,
            verbose=False,
            conf=self.confidence,
            imgsz=self.img_size,
            device=self.device,
        )[0]

        detections = []

        for box in results.boxes:

            cls_id = int(box.cls[0])

            cls_name = self.model.names[cls_id]

            if cls_name not in self.wanted_classes:
                continue

            conf = float(box.conf[0])

            min_conf = self.per_class_confidence.get(
                cls_name, self.confidence
            )

            if conf < min_conf:
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