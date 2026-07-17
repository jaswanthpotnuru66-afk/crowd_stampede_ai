# pyrefly: ignore [missing-import]
import cv2
from pathlib import Path
from src.data.pseudo_label_generator import PseudoLabelGenerator
from api.routes_video import _classify_upload_risk

video_path = Path("data/hajjv2/videos/10.mp4")
cap = cv2.VideoCapture(str(video_path))
generator = PseudoLabelGenerator(risk_cfg={"count_mode": "heuristic"})
metric_history = []
frame_idx = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % 10 == 0:
        density, count = generator.get_density_map(frame)
        flow = generator.get_optical_flow(frame)
        metrics = generator.get_risk_metrics(density, flow)
        risk = _classify_upload_risk(metrics, metric_history)
        metric_history.append(metrics)
        print(f"Frame {frame_idx}: Coverage={metrics['crowd_coverage']:.3f}, Speed={metrics['avg_speed']:.3f}, Dense={metrics.get('dense_area_ratio', 0):.3f}, Turb={metrics.get('turbulence', 0):.3f}, Risk={risk}")
    frame_idx += 1
    if frame_idx > 100:
        break
cap.release()
