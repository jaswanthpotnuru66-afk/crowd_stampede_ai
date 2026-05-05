import os


class PersonCounter:
    """
    Optional YOLO-based person counter.

    If ultralytics is unavailable, the caller can fall back to pseudo-counts.
    """

    def __init__(self, model_path: str | None = None, conf: float = 0.35):
        self.conf = conf
        self.enabled = False
        self.error = None
        self.model = None

        try:
            from ultralytics import YOLO

            self.model = YOLO(model_path or os.environ.get("PERSON_COUNTER_MODEL", "yolov8n.pt"))
            self.enabled = True
        except Exception as exc:
            self.error = str(exc)

    def detect_persons(self, frame) -> list[list[float]] | None:
        if not self.enabled or self.model is None:
            return None

        results = self.model.predict(frame, conf=self.conf, verbose=False)
        if not results:
            return []

        boxes = getattr(results[0], "boxes", None)
        if boxes is None or boxes.cls is None:
            return []

        classes = boxes.cls.detach().cpu().numpy().astype(int)
        coords = boxes.xyxy.detach().cpu().numpy().tolist()
        return [coord for coord, cls in zip(coords, classes) if cls == 0]

    def count(self, frame) -> int | None:
        detections = self.detect_persons(frame)
        if detections is None:
            return None
        return len(detections)
