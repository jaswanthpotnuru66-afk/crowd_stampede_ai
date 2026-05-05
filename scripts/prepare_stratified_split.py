"""
Stratified Train/Val/Test Split Generator
==========================================
Re-splits the HajjV2 dataset so that train, val, and test have the SAME
class distribution (Low / Moderate / High density). This fixes the #1
cause of poor test accuracy: train had Low=37%,Mod=16%,High=47%
while test had Low=19%,Mod=75%,High=6%.

Run ONCE before retraining:
    python scripts/prepare_stratified_split.py

This overwrites train_list.txt, val_list.txt, test_list.txt in data/hajjv2/.
Back up old splits first if needed.
"""
import sys
import random
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_bootstrap  # noqa: F401
from src.utils.config import load_config

# ── Ratios ────────────────────────────────────────────────────────
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
TEST_RATIO  = 0.15
SEED        = 42
# ─────────────────────────────────────────────────────────────────


def score_video(labels_dir: Path, video_name: str, seq_len: int, stride: int) -> float:
    """Compute mean coverage across all sequences from this video."""
    paths = sorted(labels_dir.glob(f"{video_name}_*.npy"))
    if not paths:
        return 0.0
        
    # Get mean (coverage) for each frame
    means = [float(np.load(str(p)).mean()) for p in paths]

    # All sequence windows for this video
    scores = []
    for start in range(0, max(len(means) - seq_len * stride + 1, 0), stride):
        seq = means[start: start + seq_len * stride: stride]
        if len(seq) == seq_len:
            scores.append(float(np.mean(seq)))

    return float(np.mean(scores)) if scores else 0.0


def classify(score: float, low_thresh: float, high_thresh: float) -> str:
    if score < low_thresh:
        return "Low"
    if score < high_thresh:
        return "Moderate"
    return "High"


def stratified_split(videos_by_class: dict, train_r: float, val_r: float,
                     rng: random.Random) -> tuple[list, list, list]:
    """Within each class, shuffle and split proportionally."""
    train_all, val_all, test_all = [], [], []
    for cls, names in videos_by_class.items():
        rng.shuffle(names)
        n = len(names)
        n_train = max(int(n * train_r), 1)
        n_val   = max(int(n * val_r),   1)
        train_all.extend(names[:n_train])
        val_all.extend(names[n_train: n_train + n_val])
        test_all.extend(names[n_train + n_val:])
        print(f"  {cls:10s}: total={n:3d}  train={n_train:3d}  val={n_val:3d}  "
              f"test={n - n_train - n_val:3d}")
    return train_all, val_all, test_all


def write_list(path: Path, names: list[str]):
    path.write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")
    print(f"  Wrote {len(names):4d} videos -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Stratified video split for HajjV2")
    parser.add_argument("--train", type=float, default=TRAIN_RATIO)
    parser.add_argument("--val",   type=float, default=VAL_RATIO)
    parser.add_argument("--seed",  type=int,   default=SEED)
    args = parser.parse_args()

    cfg          = load_config()
    data_cfg     = cfg["data"]
    training_cfg = cfg.get("training", {})
    risk_cfg     = cfg.get("risk", {})
    root      = Path(data_cfg["root"])
    labels_dir = root / "pseudo_labels"
    frames_dir = root / "extracted_frames"

    low_thresh  = float(risk_cfg.get("label_low_count",  0.04))
    high_thresh = float(risk_cfg.get("label_high_count", 0.07))
    seq_len     = int(data_cfg.get("seq_len", training_cfg.get("seq_len", 8)))
    stride      = int(data_cfg.get("stride", training_cfg.get("stride", 5)))

    # Discover all unique video names from the frames directory
    video_names = sorted({p.stem.rsplit("_", 1)[0] for p in frames_dir.glob("*.jpg")})
    if not video_names:
        # Fallback: read existing lists
        existing = set()
        for txt in [data_cfg["train_list"], data_cfg["val_list"], data_cfg["test_list"]]:
            p = Path(txt)
            if p.exists():
                existing.update(l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip())
        video_names = sorted(existing)

    print(f"\nFound {len(video_names)} unique videos in {frames_dir}")
    print(f"Thresholds: Low < {low_thresh:.1f}  |  Moderate < {high_thresh:.1f}  |  High >= {high_thresh:.1f}")
    print(f"seq_len={seq_len}, stride={stride}\n")

    # Classify each video by its dominant density class
    videos_by_class = defaultdict(list)
    for vname in video_names:
        score = score_video(labels_dir, vname, seq_len, stride)
        cls   = classify(score, low_thresh, high_thresh)
        videos_by_class[cls].append(vname)

    print("Video class distribution:")
    for cls, names in sorted(videos_by_class.items()):
        print(f"  {cls:10s}: {len(names)} videos")

    rng = random.Random(args.seed)
    print(f"\nSplitting (train={args.train:.0%}, val={args.val:.0%}, "
          f"test={1-args.train-args.val:.0%}, seed={args.seed}):")
    train_list, val_list, test_list = stratified_split(
        videos_by_class, args.train, args.val, rng
    )

    # Back up originals
    for name in ("train_list.txt", "val_list.txt", "test_list.txt"):
        orig = root / name
        if orig.exists():
            backup = orig.with_suffix(".txt.bak")
            backup.write_bytes(orig.read_bytes())
            print(f"  Backed up {orig.name} -> {backup.name}")

    print("\nWriting new splits:")
    write_list(root / "train_list.txt", train_list)
    write_list(root / "val_list.txt",   val_list)
    write_list(root / "test_list.txt",  test_list)

    print("\nDone! Now re-run training:")
    print("  python train.py")


if __name__ == "__main__":
    main()
