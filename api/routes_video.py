import cv2
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.analyzer import build_events, build_risk_probs, estimate_zones, majority_risk
from src.data.pseudo_label_generator import PseudoLabelGenerator

router = APIRouter()

RISK_LABELS = ["LOW", "MODERATE", "HIGH"]


@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video")

    safe_name = Path(file.filename or "upload.mp4").name
    tmp_path = Path(f"tmp_{safe_name}")

    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        result = _process_video(tmp_path, safe_name)
        return JSONResponse(result)
    finally:
        tmp_path.unlink(missing_ok=True)


def _process_video(video_path: Path, filename: str) -> dict:
    from api.model_loader import get_model

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Could not open uploaded video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = round(total / fps, 1) if fps else 0

    try:
        model = get_model()
    except Exception as exc:
        print(f"WARNING: Model unavailable, using motion-only analysis: {exc}")
        model = None

    generator = PseudoLabelGenerator(risk_cfg={"count_mode": "heuristic"})
    metric_history = []
    risk_votes = []
    count_history = []
    frame_buffer = []
    frame_idx = 0
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % 10 == 0:
            density, heuristic_count = generator.get_density_map(frame)
            flow = generator.get_optical_flow(frame)
            metrics = generator.get_risk_metrics(density, flow)
            heuristic_risk = _classify_upload_risk(metrics, metric_history)



            metric_history.append(metrics)
            risk_votes.append(heuristic_risk)

            model_count = None
            frame_buffer.append(frame)
            if len(frame_buffer) > 8:
                frame_buffer.pop(0)

            if len(frame_buffer) == 8 and model is not None:
                try:
                    model_result = model.predict(frame_buffer)
                    model_count = int(round(model_result.get("count", 0)))
                except Exception as exc:
                    print(f"WARNING: Model prediction failed on frame {frame_idx}: {exc}")

            count_history.append(max(int(heuristic_count), int(model_count or 0)))

        frame_idx += 1

    cap.release()

    elapsed_ms = round((time.time() - start_time) * 1000)
    final_risk = majority_risk(risk_votes)
    high_pct = round(risk_votes.count("HIGH") / max(len(risk_votes), 1) * 100)

    coverage_values = _metric_values(metric_history, "crowd_coverage")
    dense_values = _metric_values(metric_history, "dense_area_ratio")
    speed_values = _metric_values(metric_history, "avg_speed")
    variance_values = _metric_values(metric_history, "velocity_variance")
    turbulence_values = _metric_values(metric_history, "turbulence")
    last_metrics = metric_history[-1] if metric_history else {}
    coverage_count_history = [int(round(value * 1000)) for value in coverage_values]
    count_history = _normalize_count_history(count_history, coverage_count_history)
    summary_count = max(count_history) if count_history else 0

    return {
        "risk_class": final_risk,
        "risk_probs": _risk_probs_from_votes(risk_votes, final_risk),
        "count": summary_count,
        "count_source": "model+motion" if model is not None else "motion",
        "count_history": count_history,
        "crowd_coverage": round(max(coverage_values, default=0.0), 4),
        "dense_area_ratio": round(max(dense_values, default=0.0), 4),
        "avg_speed": round(_mean(speed_values), 4),
        "velocity_variance": round(_mean(variance_values), 4),
        "turbulence": round(max(turbulence_values, default=0.0), 4),
        "flow_direction": _dominant_flow_direction(metric_history),
        "density_growth": _density_growth_label(coverage_values),
        "high_risk_frame_pct": high_pct,
        "latency_ms": elapsed_ms,
        "frames_analyzed": len(risk_votes),
        "zone_risks": estimate_zones(last_metrics, final_risk),
        "events": build_events(risk_votes, fps),
        "video_info": {
            "filename": filename,
            "width": width,
            "height": height,
            "fps": round(fps),
            "duration_s": duration_s,
            "total_frames": total,
        },
    }
def _normalize_count_history(raw_history: list[int | float], fallback_history: list[int]) -> list[int]:
    values = [max(0, int(round(float(value)))) for value in raw_history if value is not None]
    if values and max(values) > 1:
        return values

    fallback_values = [max(0, int(value)) for value in fallback_history]
    if fallback_values and max(fallback_values) > 0:
        return fallback_values

    return values

def _classify_upload_risk(metrics: dict, history: list[dict]) -> str:
    coverage = float(metrics.get("crowd_coverage", 0.0))
    dense_area = float(metrics.get("dense_area_ratio", 0.0))
    avg_speed = float(metrics.get("avg_speed", 0.0))
    turbulence = float(metrics.get("turbulence", 0.0))

    valid_history = [m for m in history if float(m.get("crowd_coverage", 0.0)) > 0.001]
    recent_coverage = _mean(_metric_values(valid_history[-5:], "crowd_coverage")) if valid_history else coverage
    density_growth = coverage - recent_coverage

    score = 0.0
    if coverage >= 0.120:
        score += 2.0
    elif coverage >= 0.100:
        score += 1.0
    elif coverage >= 0.080:
        score += 0.4

    if dense_area >= 0.93:
        score += 1.0
    elif dense_area >= 0.88:
        score += 0.5

    if coverage >= 0.080 and avg_speed < 4.5:
        score += 1.0
    elif coverage >= 0.080 and avg_speed < 7.0:
        score += 0.4

    if coverage >= 0.080 and turbulence > 0.65:
        score += 0.5

    if density_growth > 0.004:
        score += 0.5

    if score >= 2.5:
        return "HIGH"
    if score >= 1.25:
        return "MODERATE"
    return "LOW"

def _metric_values(metrics: list[dict], key: str) -> list[float]:
    return [float(m[key]) for m in metrics if key in m and m[key] is not None]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _risk_probs_from_votes(votes: list[str], fallback_risk: str) -> list[float]:
    if not votes:
        return build_risk_probs(fallback_risk)

    total = len(votes) + len(RISK_LABELS)
    return [round((votes.count(label) + 1) / total, 4) for label in RISK_LABELS]


def _dominant_flow_direction(metrics: list[dict]) -> str:
    labels = [m.get("flow_direction") for m in metrics if m.get("flow_direction")]
    if not labels:
        return "Uniform"
    return max(set(labels), key=labels.count)


def _density_growth_label(coverage_values: list[float]) -> str:
    if len(coverage_values) < 2:
        return "0.0%/video"

    delta_pct = (coverage_values[-1] - coverage_values[0]) * 100
    return f"{delta_pct:+.1f}%/video"
