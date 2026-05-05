"""
Motion-based pseudo-label generation and lightweight live crowd heuristics.
"""
import json
import os
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from src.utils.person_counter import PersonCounter
from src.utils.config import load_config


class PseudoLabelGenerator:
    def __init__(self, img_size: int = 448, risk_cfg: dict | None = None):
        if risk_cfg is None:
            cfg = load_config()
            risk_cfg = {
                **cfg.get("risk", {}),
                **cfg.get("pseudo_labels", {}),
            }

        self.img_size = img_size
        self.prev_gray = None
        self.risk_cfg = risk_cfg or {}
        self.count_mode = str(self.risk_cfg.get("count_mode", "hybrid")).lower()
        self.yolo_weight = float(np.clip(float(self.risk_cfg.get("yolo_weight", 0.7)), 0.0, 1.0))
        self.dense_scene_threshold = float(self.risk_cfg.get("dense_scene_threshold", 0.14))
        self.min_detector_count = int(self.risk_cfg.get("min_detector_count", 3))
        self.zone_rows = int(self.risk_cfg.get("zone_rows", 2))
        self.zone_cols = int(self.risk_cfg.get("zone_cols", 3))
        self.zone_min_share = float(self.risk_cfg.get("zone_min_share", 0.12))
        self.hotspot_share_moderate = float(self.risk_cfg.get("hotspot_share_moderate", 0.20))
        self.hotspot_share_high = float(self.risk_cfg.get("hotspot_share_high", 0.28))
        self.zone_growth_moderate = float(self.risk_cfg.get("zone_growth_moderate", 0.02))
        self.zone_growth_high = float(self.risk_cfg.get("zone_growth_high", 0.05))
        self.total_growth_moderate = float(self.risk_cfg.get("total_growth_moderate", 0.05))
        self.total_growth_high = float(self.risk_cfg.get("total_growth_high", 0.10))
        self.distributed_zone_count = int(self.risk_cfg.get("distributed_zone_count", 4))
        self.free_flow_speed = float(self.risk_cfg.get("free_flow_speed", 0.9))
        self.congestion_speed = float(self.risk_cfg.get("congestion_speed", 0.45))
        self.speed_drop_moderate = float(self.risk_cfg.get("speed_drop_moderate", 0.15))
        self.speed_drop_high = float(self.risk_cfg.get("speed_drop_high", 0.35))
        self.turbulence_low = float(self.risk_cfg.get("turbulence_low", 0.18))
        # Density-coverage override thresholds for uniformly dense crowds.
        # With edge-based density, background textures raise values everywhere.
        # crowd_coverage >= 0.17 + dense_area_ratio >= 0.45 means the crowd
        # fills ~half the frame — only achievable in a genuinely packed scene.
        self.density_high_override = float(self.risk_cfg.get("density_high_override", 0.17))
        self.density_moderate_override = float(self.risk_cfg.get("density_moderate_override", 0.09))
        self.density_override_area_min = float(self.risk_cfg.get("density_override_area_min", 0.45))
        
        self.label_low = float(self.risk_cfg.get("label_low_count", 0.04))
        self.label_high = float(self.risk_cfg.get("label_high_count", 0.07))
        self.avg_speed_threshold = float(self.risk_cfg.get("avg_speed_threshold", 1.5))
        self.counter = None
        self.counter_error = None
        # Accumulated motion map: exponential decay over frames so that slow
        # or static crowds still build up a measurable density signal.
        self._acc_motion: np.ndarray | None = None

        if self.count_mode in {"detector", "hybrid"}:
            counter = PersonCounter(conf=float(self.risk_cfg.get("detector_conf", 0.35)))
            if counter.enabled:
                self.counter = counter
            else:
                self.counter_error = counter.error

    def reset(self):
        """Reset motion accumulator and previous frame. Call between videos to prevent carryover."""
        self.prev_gray = None
        self._acc_motion = None

    def _prepare_gray(self, frame: np.ndarray) -> np.ndarray:
        frame = cv2.resize(frame, (self.img_size, self.img_size))
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def get_density_map(self, frame: np.ndarray):
        gray = self._prepare_gray(frame)

        if self.prev_gray is None:
            self._acc_motion = np.zeros((self.img_size, self.img_size), dtype=np.float32)
            density_map = self._acc_motion.copy()
        else:
            diff = cv2.absdiff(gray, self.prev_gray).astype(np.float32) / 255.0
            _, motion_mask = cv2.threshold(diff, 10, 1.0, cv2.THRESH_BINARY)
            frame_motion = cv2.GaussianBlur(motion_mask, (31, 31), 9)

            # Moderate persistence (0.92) balances capturing static crowds
            # while preventing stale motion from previous frames/videos.
            # Reduces false HIGH predictions from accumulated background noise.
            ALPHA = 0.92
            if self._acc_motion is None:
                self._acc_motion = frame_motion
            else:
                self._acc_motion = ALPHA * self._acc_motion + (1.0 - ALPHA) * frame_motion

            # Motion-gated structural density
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))
            # Lower threshold (0.001) and larger dilation (61x61) ensures that 
            # stagnant crowds are "remembered" easily and captured by edges.
            active_region = cv2.dilate((self._acc_motion > 0.001).astype(np.float32), kernel)

            # Detect people edges (structural density)
            # We don't gate it entirely by motion anymore; we use a "leakage" factor 
            # so static people always contribute a baseline density.
            edges = cv2.Canny(gray, 20, 70).astype(np.float32) / 255.0
            structural = cv2.GaussianBlur(edges, (21, 21), 6)
            
            # Combine: motion + (structural gated but with 20% leakage for static people)
            motion_weight = self._acc_motion
            structural_weight = structural * (0.8 * active_region + 0.2)
            
            density_map = np.maximum(motion_weight, structural_weight * 1.5)

        density_map = np.clip(density_map, 0.0, 1.0)
        estimated_count = int(round(float(density_map.mean() * 1000)))
        return density_map.astype(np.float32), estimated_count

    def _resize_density_map(self, density_map: np.ndarray) -> np.ndarray:
        out_h, out_w = self.img_size // 8, self.img_size // 8
        density_small = cv2.resize(density_map, (out_w, out_h)).astype(np.float32)
        return np.maximum(density_small, 0.0)

    def _split_grid(self, arr: np.ndarray, reducer: str) -> np.ndarray:
        h, w = arr.shape[:2]
        row_edges = np.linspace(0, h, self.zone_rows + 1, dtype=int)
        col_edges = np.linspace(0, w, self.zone_cols + 1, dtype=int)
        zones = []

        for row in range(self.zone_rows):
            for col in range(self.zone_cols):
                y1, y2 = row_edges[row], row_edges[row + 1]
                x1, x2 = col_edges[col], col_edges[col + 1]
                patch = arr[y1:y2, x1:x2]
                if reducer == "sum":
                    zones.append(float(patch.sum()))
                else:
                    zones.append(float(patch.mean()) if patch.size else 0.0)

        return np.array(zones, dtype=np.float32)

    def _scale_density_to_count(self, density_map: np.ndarray, target_count: float) -> np.ndarray:
        density_small = self._resize_density_map(density_map)
        current_sum = float(density_small.sum())

        if target_count <= 0:
            return np.zeros_like(density_small, dtype=np.float32)
        if current_sum <= 1e-6:
            return np.full_like(
                density_small,
                fill_value=float(target_count) / max(density_small.size, 1),
                dtype=np.float32,
            )

        scaled = density_small * (float(target_count) / current_sum)
        return scaled.astype(np.float32)

    def _normalize_map(self, density_map: np.ndarray) -> np.ndarray:
        density_map = np.maximum(density_map.astype(np.float32), 0.0)
        peak = float(density_map.max())
        if peak <= 1e-6:
            return density_map
        return density_map / peak

    def _detector_density_map(self, frame: np.ndarray, detections: list[list[float]]) -> np.ndarray:
        resized = np.zeros((self.img_size, self.img_size), dtype=np.float32)
        frame_h, frame_w = frame.shape[:2]
        scale_x = self.img_size / max(frame_w, 1)
        scale_y = self.img_size / max(frame_h, 1)

        for x1, y1, x2, y2 in detections:
            cx = int(round(((x1 + x2) * 0.5) * scale_x))
            cy = int(round(((y1 + y2) * 0.5) * scale_y))
            cx = int(np.clip(cx, 0, self.img_size - 1))
            cy = int(np.clip(cy, 0, self.img_size - 1))
            box_w = max(int(round((x2 - x1) * scale_x)), 1)
            box_h = max(int(round((y2 - y1) * scale_y)), 1)
            radius = max(2, int(round(min(box_w, box_h) * 0.35)))
            cv2.circle(resized, (cx, cy), radius, 1.0, -1)

        detector_density = cv2.GaussianBlur(resized, (0, 0), sigmaX=4, sigmaY=4)
        return self._normalize_map(detector_density)

    def estimate_training_count(
        self,
        frame: np.ndarray,
        density_map: np.ndarray,
        heuristic_count: int,
    ) -> dict:
        detections = self.counter.detect_persons(frame) if self.counter is not None else None
        detector_count = len(detections) if detections is not None else None
        crowd_coverage = float(np.clip(density_map.mean(), 0.0, 1.0))
        detector_density = (
            self._detector_density_map(frame, detections)
            if detections
            else None
        )

        # Dense scenes are where detector-only counts become fragile because of
        # small, overlapping people. In those cases the motion/density prior
        # gets more say even if YOLO is available.
        if detector_count is None:
            target_count = int(heuristic_count)
            count_source = "heuristic"
        elif self.count_mode == "detector":
            target_count = int(detector_count)
            count_source = "detector"
        else:
            detector_weight = self.yolo_weight
            if crowd_coverage >= self.dense_scene_threshold:
                detector_weight *= 0.5
            if detector_count < self.min_detector_count and heuristic_count > detector_count:
                detector_weight *= 0.35

            target_count = int(round(
                detector_weight * detector_count +
                (1.0 - detector_weight) * heuristic_count
            ))
            count_source = "hybrid" if detector_count is not None else "heuristic"

        if detector_density is not None:
            spatial_weight = self.yolo_weight if detector_count >= self.min_detector_count else self.yolo_weight * 0.5
            if crowd_coverage >= self.dense_scene_threshold:
                spatial_weight *= 0.6
            combined_density = (
                spatial_weight * detector_density +
                (1.0 - spatial_weight) * self._normalize_map(density_map)
            )
        else:
            combined_density = density_map

        calibrated_density = self._scale_density_to_count(combined_density, target_count)
        return {
            "density_map": calibrated_density,
            "count": int(target_count),
            "detector_count": None if detector_count is None else int(detector_count),
            "heuristic_count": int(heuristic_count),
            "count_source": count_source,
            "crowd_coverage": crowd_coverage,
        }

    def get_optical_flow(self, frame: np.ndarray) -> np.ndarray:
        gray = self._prepare_gray(frame)

        if self.prev_gray is None:
            flow = np.zeros((self.img_size, self.img_size, 2), dtype=np.float32)
        else:
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray,
                gray,
                None,
                0.5,
                3,
                15,
                3,
                5,
                1.2,
                0,
            )

        self.prev_gray = gray
        return flow

    def get_risk_metrics(self, density: np.ndarray, flow: np.ndarray) -> dict:
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        crowd_coverage = float(np.clip(density.mean(), 0.0, 1.0))
        # Lower threshold (0.04 vs 0.08): blurred structural density is dampened;
        # 0.04 correctly captures dense packed crowds that are barely moving.
        dense_area_ratio = float((density > 0.04).mean())
        avg_speed = float(mag.mean())
        velocity_variance = float(np.var(mag))
        turbulence = float(np.clip(velocity_variance / 12.0 + avg_speed / 30.0, 0.0, 1.0))

        # ── Directional consistency via circular statistics ──────────────────
        # Only consider pixels with meaningful motion (avoids noisy static areas).
        motion_pixels = mag > 0.5
        if motion_pixels.sum() > 200:
            angles = ang[motion_pixels]
            # Mean Resultant Length R: 1 = all vectors aligned, 0 = random
            R = float(np.sqrt(np.sin(angles).mean() ** 2 + np.cos(angles).mean() ** 2))
        else:
            R = 1.0  # no motion → treat as uniform / static

        if R > 0.65:
            flow_direction = "Uniform"
        elif R > 0.35:
            flow_direction = "Converging"
        else:
            flow_direction = "Chaotic"
        # ────────────────────────────────────────────────────────────────────

        zone_counts = self._split_grid(density, reducer="sum")
        zone_speeds = self._split_grid(mag, reducer="mean")
        zone_shares = zone_counts / max(float(zone_counts.sum()), 1e-6)
        hotspot_index = int(zone_shares.argmax()) if zone_shares.size else 0
        hotspot_share = float(zone_shares[hotspot_index]) if zone_shares.size else 0.0
        hotspot_count = float(zone_counts[hotspot_index]) if zone_counts.size else 0.0
        hotspot_speed = float(zone_speeds[hotspot_index]) if zone_speeds.size else 0.0
        occupied_zones = int((zone_shares >= self.zone_min_share).sum())

        return {
            "crowd_coverage": crowd_coverage,
            "dense_area_ratio": dense_area_ratio,
            "avg_speed": avg_speed,
            "velocity_variance": velocity_variance,
            "turbulence": turbulence,
            "directional_consistency": round(R, 4),
            "flow_direction": flow_direction,
            "zone_counts": zone_counts.tolist(),
            "zone_shares": zone_shares.tolist(),
            "zone_speeds": zone_speeds.tolist(),
            "hotspot_index": hotspot_index,
            "hotspot_share": hotspot_share,
            "hotspot_count": hotspot_count,
            "hotspot_speed": hotspot_speed,
            "occupied_zones": occupied_zones,
        }

    def classify_risk(self, metrics: dict, metrics_history: list[dict]):
        """
        3-stage crowd risk classification:

        STAGE 1 – LOW:
            Sparse crowd, large gaps between people, everyone moving freely.

        STAGE 2 – MODERATE:
            More crowd present but still flowing through the area.
            People are moving; the location is not filling up.

        STAGE 3 – HIGH:
            Heavy crowd density + crowd is slow/static + more people being
            added (density growing). Classic pre-stampede conditions.
        """
        recent = metrics_history[-5:]

        crowd_coverage  = metrics["crowd_coverage"]
        dense_area_ratio = metrics["dense_area_ratio"]
        avg_speed       = metrics["avg_speed"]

        # ── Trend signals from recent history ─────────────────────────────────
        if len(recent) >= 2:
            avg_recent_speed    = float(np.mean([m["avg_speed"]        for m in recent]))
            avg_recent_coverage = float(np.mean([m["crowd_coverage"]   for m in recent]))
        else:
            avg_recent_speed    = avg_speed
            avg_recent_coverage = crowd_coverage

        speed_drop      = avg_recent_speed - avg_speed          # positive = slowing down
        density_growth  = crowd_coverage - avg_recent_coverage  # positive = getting denser

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 1 — LOW RISK
        # Few people, large open gaps, crowd moving freely.
        # ══════════════════════════════════════════════════════════════════════
        # crowd_coverage = accumulated motion mean (0→1)
        # avg_speed      = optical flow magnitude across 5-frame gaps (~pixels)
        #                  Walking person ≈ 3–8 px; slow crowd ≈ 1–3 px
        SPARSE_COVERAGE = self.label_low * 0.75   # scale relative to moderate threshold
        SPARSE_AREA     = self.density_moderate_override

        is_sparse = crowd_coverage < SPARSE_COVERAGE
        has_gaps  = dense_area_ratio < SPARSE_AREA

        if is_sparse and has_gaps:
            return 0, "LOW"

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 3 — HIGH RISK
        # Heavy motion coverage + crowd slowing down + density still growing.
        # ══════════════════════════════════════════════════════════════════════
        HEAVY_COVERAGE  = self.label_high
        HEAVY_AREA      = self.density_high_override
        SLOW_SPEED      = self.avg_speed_threshold
        SPEED_DROP_HIGH = SLOW_SPEED * 0.6
        GROWTH_THRESH   = 0.003  # density grew ≥ 0.3 percentage points

        is_heavy   = crowd_coverage >= HEAVY_COVERAGE or dense_area_ratio >= HEAVY_AREA
        is_slow    = avg_speed < SLOW_SPEED or speed_drop >= SPEED_DROP_HIGH
        is_growing = density_growth >= GROWTH_THRESH

        if is_heavy and (is_slow or is_growing):
            return 2, "HIGH"

        # Heavy + very slow (barely moving) = danger even without growth data
        if is_heavy and avg_speed < (SLOW_SPEED * 0.5):
            return 2, "HIGH"

        # Extreme motion coverage = frame completely filled with moving people
        if crowd_coverage >= (self.label_high * 2.2) or dense_area_ratio >= 0.60:
            return 2, "HIGH"

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 2 — MODERATE RISK
        # More crowd than LOW, people still moving through, not compressing.
        # ══════════════════════════════════════════════════════════════════════
        if crowd_coverage >= self.label_low or dense_area_ratio >= self.density_moderate_override:
            return 1, "MODERATE"

        # Heavy crowd but still moving fast = MODERATE, not yet HIGH
        if is_heavy and not is_slow:
            return 1, "MODERATE"

        return 0, "LOW"


def generate_pseudo_labels(
    frames_dir: str,
    output_dir: str,
    csrnet_weights: str = None,
    device: str = "cuda",
    img_size: int = 448,
    count_cfg: dict | None = None,
):
    del csrnet_weights, device
    os.makedirs(output_dir, exist_ok=True)
    frame_paths = sorted(Path(frames_dir).glob("*.jpg"))

    if not frame_paths:
        print("No frames found in", frames_dir)
        return 0

    generator = PseudoLabelGenerator(img_size=img_size, risk_cfg=count_cfg)
    written = 0
    metadata_path = Path(output_dir) / "_pseudo_label_metadata.jsonl"
    if metadata_path.exists():
        metadata_path.unlink()

    if generator.counter_error:
        print(f"YOLO counter unavailable, falling back to heuristic counts: {generator.counter_error}")

    prev_video_name = None
    with metadata_path.open("a", encoding="utf-8") as meta_f:
        for path in tqdm(frame_paths, desc="Generating pseudo labels (hybrid)"):
            img = cv2.imread(str(path))
            if img is None:
                continue

            # Extract video name from frame filename (e.g., "video1_frame001.jpg" → "video1")
            current_video_name = path.stem.rsplit("_f", 1)[0] if "_f" in path.stem else path.stem
            
            # Reset motion accumulator when switching to a new video
            if prev_video_name is not None and current_video_name != prev_video_name:
                generator.reset()
            prev_video_name = current_video_name

            density_map, heuristic_count = generator.get_density_map(img)
            generator.get_optical_flow(img)
            target = generator.estimate_training_count(img, density_map, heuristic_count)

            np.save(os.path.join(output_dir, path.stem + ".npy"), target["density_map"])
            meta_f.write(json.dumps({
                "frame": path.name,
                "count": target["count"],
                "detector_count": target["detector_count"],
                "heuristic_count": target["heuristic_count"],
                "count_source": target["count_source"],
                "crowd_coverage": round(target["crowd_coverage"], 6),
            }) + "\n")
            written += 1

    print(f"Generated {written} pseudo labels in {output_dir}")
    print(f"Metadata saved to {metadata_path}")
    return written


def _ensure_split_files(dataset_root: Path, video_dir: Path):
    train_list = dataset_root / "train_list.txt"
    val_list = dataset_root / "val_list.txt"
    test_list = dataset_root / "test_list.txt"

    if train_list.exists() and val_list.exists() and test_list.exists():
        return

    videos = sorted(p.stem for p in video_dir.glob("*.mp4"))
    videos += sorted(p.stem for p in video_dir.glob("*.avi"))
    videos = sorted(dict.fromkeys(videos))

    if not videos:
        return

    n = len(videos)
    train_end = max(1, int(n * 0.7))
    val_end = max(train_end + 1, int(n * 0.8)) if n > 2 else train_end

    splits = {
        train_list: videos[:train_end],
        val_list: videos[train_end:val_end] or videos[:1],
        test_list: videos[val_end:] or videos[-1:],
    }

    for path, items in splits.items():
        path.write_text("\n".join(items) + ("\n" if items else ""), encoding="utf-8")


def generate_dataset_from_videos(
    video_dir: str,
    frames_dir: str,
    labels_dir: str,
    sample_rate: int = 2,
    cfg: dict | None = None,
):
    del sample_rate
    dataset_root = Path(video_dir).parent
    cfg = cfg or {}
    img_size = int(cfg.get("img_size", 448))
    written = generate_pseudo_labels(
        frames_dir,
        labels_dir,
        img_size=img_size,
        count_cfg=cfg,
    )
    _ensure_split_files(dataset_root, Path(video_dir))
    return written
