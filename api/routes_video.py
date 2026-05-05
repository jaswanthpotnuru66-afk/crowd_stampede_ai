import cv2
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.data.pseudo_label_generator import PseudoLabelGenerator
from api.analyzer import (
    analyze_frame_sequence,
    build_risk_probs,
    majority_risk,
    build_events,
)

router = APIRouter()


@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video")

    tmp_path = Path(f"tmp_{file.filename}")
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        result = _process_video(tmp_path, file.filename)
        return JSONResponse(result)
    finally:
        tmp_path.unlink(missing_ok=True)


def _process_video(video_path: Path, filename: str) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    fps        = cap.get(cv2.CAP_PROP_FPS) or 30
    total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = round(total / fps, 1)

    gen             = PseudoLabelGenerator()
    density_history = []
    count_history   = []
    risk_votes      = []
    metrics_log     = []
    frame_idx       = 0
    start_time      = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % 5 == 0:
            result = analyze_frame_sequence([frame], gen, density_history)
            if result:
                count_history.append(result["count"])
                risk_votes.append(result["risk_class"])
                metrics_log.append(result)

        frame_idx += 1

    cap.release()

    elapsed_ms  = round((time.time() - start_time) * 1000)
    final_risk  = majority_risk(risk_votes)
    total_votes = max(len(risk_votes), 1)

    avg = lambda key: round(sum(m[key] for m in metrics_log) / max(len(metrics_log), 1), 4)

    high_pct = round(risk_votes.count("HIGH") / total_votes * 100)

    return {
        "risk_class":            final_risk,
        "risk_probs":            build_risk_probs(final_risk),
        "count":                 max(count_history) if count_history else 0,
        "count_source":          metrics_log[-1].get("count_source", "heuristic") if metrics_log else "heuristic",
        "count_history":         count_history,
        "crowd_coverage":        avg("crowd_coverage"),
        "dense_area_ratio":      avg("dense_area_ratio"),
        "avg_speed":             avg("avg_speed"),
        "velocity_variance":     avg("velocity_variance"),
        "turbulence":            avg("turbulence"),
        "flow_direction":        metrics_log[-1]["flow_direction"] if metrics_log else "—",
        "density_growth":        f"+{round(avg('crowd_coverage') * 20)}%/5s",
        "high_risk_frame_pct":   high_pct,
        "latency_ms":            elapsed_ms,
        "frames_analyzed":       len(count_history),
        "zone_risks":            metrics_log[-1].get("zone_risks", ["low"] * 6) if metrics_log else ["low"] * 6,
        "events":                build_events(risk_votes, fps),
        "video_info": {
            "filename":   filename,
            "width":      width,
            "height":     height,
            "fps":        round(fps),
            "duration_s": duration_s,
            "total_frames": total,
        },
    }
