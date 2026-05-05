import base64

import cv2
import numpy as np

from src.data.pseudo_label_generator import PseudoLabelGenerator
from src.utils.person_counter import PersonCounter

_PERSON_COUNTER = None


def get_person_counter() -> PersonCounter:
    global _PERSON_COUNTER
    if _PERSON_COUNTER is None:
        _PERSON_COUNTER = PersonCounter()
    return _PERSON_COUNTER


def analyze_frame_sequence(frames: list, gen: PseudoLabelGenerator, density_history: list) -> dict:
    """
    Risk classification driven by two reliable signals:
      1. YOLO person count  — how many people are in the frame
      2. Optical flow speed — are they moving freely or compressed

    Density-map accumulator is still used for the motion metrics display
    and as a fallback when YOLO is unavailable.
    """
    if not frames:
        return {}

    frame = frames[-1]

    # ── Motion / optical flow metrics (always computed) ──────────────────────
    density, _ = gen.get_density_map(frame)
    flow        = gen.get_optical_flow(frame)
    metrics     = gen.get_risk_metrics(density, flow)

    density_history.append(metrics)
    if len(density_history) > 30:
        density_history.pop(0)

    avg_speed        = metrics["avg_speed"]          # optical flow px/frame-gap
    crowd_coverage   = metrics["crowd_coverage"]     # accumulated motion 0→1
    dense_area_ratio = metrics["dense_area_ratio"]

    # ── YOLO person detection ─────────────────────────────────────────────────
    counter        = get_person_counter()
    boxes          = counter.detect_persons(frame)   # list of [x1,y1,x2,y2] or None
    detected_count = len(boxes) if boxes is not None else None

    # YOLO box coverage: fraction of frame occupied by detected bounding boxes
    if boxes:
        fh, fw = frame.shape[:2]
        box_area = sum((x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in boxes)
        box_coverage = float(box_area) / max(fh * fw, 1)
    else:
        box_coverage = 0.0

    pseudo_count = int(crowd_coverage * 1000)
    count = detected_count if detected_count is not None else pseudo_count

    # ── Heuristic Critical Override (Hajj / Extreme Density Scenarios) ───────
    # Pull dynamic thresholds from the generator (synced with default.yaml)
    SAFE_LIMIT_HIGH  = gen.label_high           # approx 0.12
    SAFE_LIMIT_AREA  = gen.density_high_override # approx 0.15
    STAGNATION_SPEED = 0.40                     # very extreme stagnation (shuffling is ~0.60+)

    is_heavy = (crowd_coverage > SAFE_LIMIT_HIGH  or dense_area_ratio > SAFE_LIMIT_AREA)
    is_slow  = (avg_speed < STAGNATION_SPEED)   # Truly stuck / compressed
    is_chaos = (metrics["turbulence"] > 0.35 or metrics["hotspot_share"] > 0.35)

    is_heuristic_high = is_heavy and (is_slow or is_chaos)

    if is_heuristic_high:
        risk_int, risk_str = 2, "HIGH"
        print(f"[DBG] HAJJ OVERRIDE TRIGGERED: cov={crowd_coverage:.4f} spd={avg_speed:.2f} turb={metrics['turbulence']:.2f}", flush=True)

    elif detected_count is not None:
        # ── Primary risk classification: YOLO count + speed ──────────────────────
        #
        # YOLO counts at 448×448 (people overlap heavily in dense crowds):
        #   < 15  →  sparse / low crowd
        #  15–39  →  moderate crowd
        #   40+   →  heavy crowd
        # ─────────────────────────────────────────────────────────────────────────

        # NEW: Ensure we don't default to LOW if coverage is high but YOLO missed them
        is_coverage_high = crowd_coverage >= gen.label_high
        
        is_heavy = detected_count >= 80 or box_coverage >= 0.25
        is_slow  = avg_speed < 1.0          # way below walking speed
        is_very_dense = detected_count >= 120 or box_coverage >= 0.35

        if is_very_dense or (is_coverage_high and is_slow):
            risk_int, risk_str = 2, "HIGH"
        elif is_heavy and is_slow:
            risk_int, risk_str = 2, "HIGH"
        elif is_heavy or is_coverage_high:
            risk_int, risk_str = 1, "MODERATE"   # dense but still flowing
        elif detected_count >= 15:
            risk_int, risk_str = 1, "MODERATE"
        else:
            risk_int, risk_str = 0, "LOW"

    else:
        # ── Fallback: motion accumulator path (no YOLO) ───────────────────────
        is_heavy = crowd_coverage >= gen.label_low or dense_area_ratio >= (SAFE_LIMIT_AREA * 0.5)
        is_slow  = avg_speed < 1.0

        if crowd_coverage >= (SAFE_LIMIT_HIGH * 1.0) or dense_area_ratio >= (SAFE_LIMIT_AREA * 1.5):
            risk_int, risk_str = 2, "HIGH"
        elif is_heavy and is_slow:
            risk_int, risk_str = 2, "HIGH"
        elif is_heavy:
            risk_int, risk_str = 1, "MODERATE"
        elif crowd_coverage >= 0.06 or dense_area_ratio >= 0.25:
            risk_int, risk_str = 1, "MODERATE"
        else:
            risk_int, risk_str = 0, "LOW"

    print(f"[DBG] cnt={detected_count} box_cov={box_coverage:.3f} cov={crowd_coverage:.4f} "
          f"spd={avg_speed:.2f} → {risk_str}", flush=True)

    dmap_b64   = encode_density_map(density)
    zone_risks = estimate_zones(metrics, risk_str)

    return {
        "risk_class":      risk_str,
        "risk_int":        risk_int,
        "crowd_coverage":  round(crowd_coverage, 4),
        "dense_area_ratio": round(dense_area_ratio, 4),
        "avg_speed":       round(avg_speed, 4),
        "velocity_variance": round(metrics["velocity_variance"], 4),
        "turbulence":      round(metrics["turbulence"], 4),
        "count":           count,
        "pseudo_count":    pseudo_count,
        "count_source":    "detector" if detected_count is not None else "heuristic",
        "density_map_b64": dmap_b64,
        "flow_direction":  metrics.get("flow_direction", _flow_label(metrics["turbulence"])),
        "hotspot_index":   metrics["hotspot_index"],
        "hotspot_share":   round(metrics["hotspot_share"], 4),
        "zone_risks":      zone_risks,
    }


def encode_density_map(density: np.ndarray) -> str:
    dmap_vis = (density * 255).astype(np.uint8)
    colored = cv2.applyColorMap(dmap_vis, cv2.COLORMAP_JET)
    _, buf = cv2.imencode(".jpg", colored, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf).decode()


def build_risk_probs(risk_str: str) -> list:
    return {
        "HIGH": [0.05, 0.18, 0.77],
        "MODERATE": [0.20, 0.62, 0.18],
        "LOW": [0.75, 0.20, 0.05],
    }.get(risk_str, [0.75, 0.20, 0.05])


def majority_risk(votes: list) -> str:
    if not votes:
        return "LOW"

    total = len(votes)
    if votes.count("HIGH") / total > 0.3:
        return "HIGH"
    if votes.count("MODERATE") / total > 0.4:
        return "MODERATE"
    return "LOW"


def estimate_zones(metrics: dict | None, risk: str = "LOW") -> list:
    if not metrics:
        return ["low"] * 6

    zone_shares = metrics.get("zone_shares") or []
    if not zone_shares:
        return ["low"] * 6

    hotspot_index = int(metrics.get("hotspot_index", 0))
    hotspot_share = float(metrics.get("hotspot_share", 0.0))
    zones = []

    for idx, share in enumerate(zone_shares):
        share = float(share)
        if idx == hotspot_index and risk == "HIGH" and share >= 0.30:
            zones.append("high")
        elif share >= max(0.20, hotspot_share * 0.7):
            zones.append("moderate" if risk != "LOW" else "low")
        else:
            zones.append("low")

    return zones


def build_events(risk_votes: list, fps: float) -> list:
    events = []
    prev = None
    for i, risk in enumerate(risk_votes):
        if risk == prev:
            continue

        t = round(i * 5 / max(fps, 1))
        m, s = divmod(t, 60)
        ts = f"{m:02d}:{s:02d}"
        color = "#f87171" if risk == "HIGH" else "#fbbf24" if risk == "MODERATE" else "#4ade80"
        msg = {
            "HIGH": "High risk detected - local hotspot is building up",
            "MODERATE": "Moderate risk - one area is getting more crowded",
            "LOW": "Smooth crowd flow restored",
        }[risk]
        events.append({"message": msg, "timestamp": ts, "color": color, "risk": risk})
        prev = risk

    events.append({"message": "Analysis started", "timestamp": "00:00", "color": "#4ade80", "risk": "LOW"})
    return list(reversed(events[:8]))


def _flow_label(turbulence: float) -> str:
    if turbulence > 0.5:
        return "Chaotic"
    if turbulence > 0.25:
        return "Converging"
    return "Uniform"
