import cv2
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from api.analyzer import build_risk_probs, majority_risk, build_events

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
    from api.model_loader import get_model

    cap        = cv2.VideoCapture(str(video_path))
    fps        = cap.get(cv2.CAP_PROP_FPS) or 30
    total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = round(total / fps, 1)

    model         = get_model()
    risk_votes    = []
    count_history = []
    frame_buffer  = []
    frame_idx     = 0
    start_time    = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % 10 == 0:
            frame_buffer.append(frame)
            if len(frame_buffer) > 8:
                frame_buffer.pop(0)

            if len(frame_buffer) == 8 and model is not None:
                result = model.predict(frame_buffer)
                risk_votes.append(result["risk_class"])
                count_history.append(result["count"])

        frame_idx += 1

    cap.release()

    elapsed_ms = round((time.time() - start_time) * 1000)
    final_risk = majority_risk(risk_votes)
    high_pct   = round(risk_votes.count("HIGH") / max(len(risk_votes), 1) * 100)

    return {
        "risk_class":          final_risk,
        "risk_probs":          build_risk_probs(final_risk),
        "count":               max(count_history) if count_history else 0,
        "count_source":        "model",
        "count_history":       count_history,
        "crowd_coverage":      0.0,
        "dense_area_ratio":    0.0,
        "avg_speed":           0.0,
        "velocity_variance":   0.0,
        "turbulence":          0.0,
        "flow_direction":      "Uniform",
        "density_growth":      "+0%/5s",
        "high_risk_frame_pct": high_pct,
        "latency_ms":          elapsed_ms,
        "frames_analyzed":     len(risk_votes),
        "zone_risks":          ["low"] * 6,
        "events":              build_events(risk_votes, fps),
        "video_info": {
            "filename":     filename,
            "width":        width,
            "height":       height,
            "fps":          round(fps),
            "duration_s":   duration_s,
            "total_frames": total,
        },
    }