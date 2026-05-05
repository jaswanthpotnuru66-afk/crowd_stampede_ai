import cv2
import numpy as np


RISK_COLORS = {
    "LOW":      (0,  200,  80),
    "MODERATE": (0,  180, 240),
    "HIGH":     (0,   60, 230),
}


def overlay_density_map(frame: np.ndarray, density: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    h, w = frame.shape[:2]
    dmap = cv2.resize(density, (w, h))
    dmap = (dmap / (dmap.max() + 1e-8) * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(dmap, cv2.COLORMAP_JET)
    return cv2.addWeighted(frame, 1 - alpha, heatmap, alpha, 0)


def draw_risk_label(frame: np.ndarray, risk_class: str, count: int) -> np.ndarray:
    color = RISK_COLORS.get(risk_class, (200, 200, 200))
    h, w  = frame.shape[:2]

    cv2.rectangle(frame, (0, h - 40), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, f"{risk_class} RISK | Count: {count}",
                (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def draw_zone_grid(frame: np.ndarray, zone_risks: list, rows: int = 2, cols: int = 3) -> np.ndarray:
    h, w  = frame.shape[:2]
    zh, zw = h // rows, w // cols
    colors = {"low": (0,200,80), "moderate": (0,180,240), "high": (0,60,230)}

    for i, risk in enumerate(zone_risks):
        r, c  = divmod(i, cols)
        x1, y1 = c * zw, r * zh
        x2, y2 = x1 + zw, y1 + zh
        color   = colors.get(risk, (128, 128, 128))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"Z{i+1}", (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return frame