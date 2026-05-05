import numpy as np
import torch
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset
import cv2
import json

from .transforms import get_transforms


class CrowdSequenceDataset(Dataset):
    """
    Loads sequences of frames + pseudo density labels for Swin-LSTM training.
    Each item = (seq_frames, density_maps, risk_label)
    """

    def __init__(
        self,
        root: str,
        split_file: str,
        seq_len: int = 8,
        transform=None,
        stride: int = 1,
        risk_thresholds: tuple[float, float] = (386.0, 436.6),
        risk_cfg: dict | None = None,
    ):
        self.root = Path(root)
        self.seq_len = seq_len
        self.transform = transform
        self.stride = stride
        self.risk_thresholds = risk_thresholds
        self.risk_cfg = risk_cfg or {}
        self.zone_rows = int(self.risk_cfg.get("zone_rows", 2))
        self.zone_cols = int(self.risk_cfg.get("zone_cols", 3))
        self.zone_min_share = float(self.risk_cfg.get("zone_min_share", 0.12))
        self.hotspot_share_moderate = float(self.risk_cfg.get("hotspot_share_moderate", 0.30))
        self.hotspot_share_high = float(self.risk_cfg.get("hotspot_share_high", 0.42))
        self.zone_growth_moderate = float(self.risk_cfg.get("zone_growth_moderate", 0.06))
        self.zone_growth_high = float(self.risk_cfg.get("zone_growth_high", 0.12))
        self.total_growth_moderate = float(self.risk_cfg.get("total_growth_moderate", 0.08))
        self.total_growth_high = float(self.risk_cfg.get("total_growth_high", 0.18))
        self.count_guard_ratio = float(self.risk_cfg.get("count_guard_ratio", 0.15))
        self.distributed_zone_count = int(self.risk_cfg.get("distributed_zone_count", 3))
        self.avg_speed_threshold = float(self.risk_cfg.get("avg_speed_threshold", 1.5))
        self.dense_area_min_moderate = float(self.risk_cfg.get("density_moderate_override", 0.18))
        self.dense_area_min_high = float(self.risk_cfg.get("density_high_override", 0.25))

        frames_dir = self.root / "extracted_frames"
        labels_dir = self.root / "pseudo_labels"

        with open(split_file, "r", encoding="utf-8") as f:
            video_names = [l.strip() for l in f if l.strip()]

        self.sequences = []
        for vname in video_names:
            frames = sorted(frames_dir.glob(f"{vname}_*.jpg"))
            labels = sorted(labels_dir.glob(f"{vname}_*.npy"))
            pairs = list(zip(frames, labels))
            for i in range(0, max(len(pairs) - seq_len * stride + 1, 0), stride):
                seq = pairs[i: i + seq_len * stride: stride]
                if len(seq) == seq_len:
                    self.sequences.append(seq)

    def __len__(self):
        return len(self.sequences)

    def _zone_sums(self, density_map: np.ndarray) -> np.ndarray:
        h, w = density_map.shape
        row_edges = np.linspace(0, h, self.zone_rows + 1, dtype=int)
        col_edges = np.linspace(0, w, self.zone_cols + 1, dtype=int)
        zones = []

        for row in range(self.zone_rows):
            for col in range(self.zone_cols):
                y1, y2 = row_edges[row], row_edges[row + 1]
                x1, x2 = col_edges[col], col_edges[col + 1]
                zones.append(float(density_map[y1:y2, x1:x2].sum()))

        return np.array(zones, dtype=np.float32)

    def _compute_risk(self, density_maps, pil_frames):
        # Convert PIL frames to grayscale CV2 for optical flow
        cv_frames = [cv2.cvtColor(np.array(f), cv2.COLOR_RGB2GRAY) for f in pil_frames]
        
        # Calculate Optical Flow for the sequence
        speeds = []
        turbulences = []
        for i in range(len(cv_frames) - 1):
            flow = cv2.calcOpticalFlowFarneback(cv_frames[i], cv_frames[i+1], None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            speeds.append(mag.mean())
            
            # Simple directional consistency (1 - circular variance)
            # Higher turbulence = lower consistency
            cos_a = np.cos(ang)
            sin_a = np.sin(ang)
            mrl = np.sqrt(np.mean(cos_a)**2 + np.mean(sin_a)**2)
            turbulences.append(1.0 - mrl)

        avg_speed = float(np.mean(speeds)) if speeds else 0.0
        avg_turb = float(np.mean(turbulences)) if turbulences else 0.0
        
        # Density metrics
        final_dmap = density_maps[-1]
        crowd_coverage = float(np.clip(final_dmap.mean(), 0.0, 1.0))
        # Use low threshold as the density baseline
        dense_area_ratio = float((final_dmap > self.risk_thresholds[0]).mean())

        # Zone metrics
        zone_sums = self._zone_sums(final_dmap)
        hotspot_share = float(zone_sums.max() / max(zone_sums.sum(), 1e-6))

        # ── 3-STAGE RISK LOGIC (Synced with UI) ──────────────────────────────
        low_t, high_t = self.risk_thresholds

        # STAGE 3 — HIGH RISK (Extreme density or slow-moving build-up)
        is_heavy = (crowd_coverage > high_t or dense_area_ratio > self.dense_area_min_high)
        is_slow  = (avg_speed < self.avg_speed_threshold)
        is_chaos = (avg_turb > 0.20 or hotspot_share > 0.30)

        if is_heavy and (is_slow or is_chaos):
            return 2
        
        # STAGE 2 — MODERATE RISK (Notable crowd still moving)
        if crowd_coverage > low_t or dense_area_ratio > self.dense_area_min_moderate:
            return 1
            
        return 0

    def __getitem__(self, idx):
        seq = self.sequences[idx]
        pil_frames = [Image.open(str(fp)).convert("RGB") for fp, _ in seq]
        dmaps = [np.load(str(lp)).astype(np.float32) for _, lp in seq]

        if self.transform:
            frames_tensor = self.transform(pil_frames)
        else:
            import torchvision.transforms.functional as TF
            frames_tensor = torch.stack([TF.to_tensor(f) for f in pil_frames])

        dmaps_tensor = torch.from_numpy(np.stack(dmaps)).float()
        
        # Compute risk label using both density and frames (for speed)
        risk_label = torch.tensor(self._compute_risk(dmaps, pil_frames), dtype=torch.long)

        return frames_tensor, dmaps_tensor, risk_label


class HajjV2VideoDataset(CrowdSequenceDataset):
    """
    Backward-compatible wrapper used by the top-level scripts.
    """

    def __init__(
        self,
        root: str | None = None,
        labels_dir: str | None = None,
        split_file: str | None = None,
        seq_len: int = 8,
        stride: int = 1,
        img_size: int = 224,
        train: bool = True,
        scene_list: list[str] | None = None,
        risk_thresholds: tuple[float, float] = (386.0, 436.6),
        risk_cfg: dict | None = None,
    ):
        if root is None:
            if labels_dir is None:
                raise ValueError("Either root or labels_dir must be provided")
            root = str(Path(labels_dir).parent)

        root_path = Path(root)
        frames_dir = root_path / "extracted_frames"
        labels_path = root_path / "pseudo_labels"

        if split_file is not None:
            with open(split_file, "r", encoding="utf-8") as f:
                video_names = [line.strip() for line in f if line.strip()]
        elif scene_list is not None:
            video_names = list(scene_list)
        else:
            video_names = sorted({p.stem.split("_f")[0] for p in frames_dir.glob("*.jpg")})

        self.root = root_path
        self.seq_len = seq_len
        self.transform = get_transforms(img_size=img_size, is_train=train)
        self.stride = stride
        self.risk_thresholds = risk_thresholds
        self.risk_cfg = risk_cfg or {}
        self.zone_rows = int(self.risk_cfg.get("zone_rows", 2))
        self.zone_cols = int(self.risk_cfg.get("zone_cols", 3))
        self.zone_min_share = float(self.risk_cfg.get("zone_min_share", 0.12))
        self.hotspot_share_moderate = float(self.risk_cfg.get("hotspot_share_moderate", 0.30))
        self.hotspot_share_high = float(self.risk_cfg.get("hotspot_share_high", 0.42))
        self.zone_growth_moderate = float(self.risk_cfg.get("zone_growth_moderate", 0.06))
        self.zone_growth_high = float(self.risk_cfg.get("zone_growth_high", 0.12))
        self.total_growth_moderate = float(self.risk_cfg.get("total_growth_moderate", 0.08))
        self.total_growth_high = float(self.risk_cfg.get("total_growth_high", 0.18))
        self.count_guard_ratio = float(self.risk_cfg.get("count_guard_ratio", 0.15))
        self.distributed_zone_count = int(self.risk_cfg.get("distributed_zone_count", 3))
        self.avg_speed_threshold = float(self.risk_cfg.get("avg_speed_threshold", 1.5))
        self.dense_area_min_moderate = float(self.risk_cfg.get("density_moderate_override", 0.18))
        self.dense_area_min_high = float(self.risk_cfg.get("density_high_override", 0.25))
        self.sequences = []

        for vname in video_names:
            frames = sorted(frames_dir.glob(f"{vname}_*.jpg"))
            labels = sorted(labels_path.glob(f"{vname}_*.npy"))
            pairs = list(zip(frames, labels))
            for i in range(0, max(len(pairs) - seq_len * stride + 1, 0), stride):
                seq = pairs[i: i + seq_len * stride: stride]
                if len(seq) == seq_len:
                    self.sequences.append(seq)
