"""
STEP 3 - Evaluate trained model on test set.

Usage:
    python evaluate.py
"""
import runtime_bootstrap
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from src.data.dataset import HajjV2VideoDataset
from src.engine.evaluator import Evaluator
from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
from src.utils.config import load_config


def main():
    cfg = load_config()
    data_cfg = cfg["data"]
    risk_cfg = cfg.get("risk", {})
    risk_thresholds = (
        float(risk_cfg.get("label_low_count", 0.04)),
        float(risk_cfg.get("label_high_count", 0.07)),
    )

    test_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["test_list"],
        seq_len=data_cfg["seq_len"],
        stride=data_cfg["stride"],
        img_size=data_cfg["img_size"],
        train=False,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=2,
        shuffle=False,
        num_workers=max(data_cfg["num_workers"] // 2, 1),
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CrowdMonitor(cfg)
    ckpt_candidates = [
        Path(cfg["paths"]["checkpoints"]) / "best.pth",
        Path(cfg["paths"]["checkpoints"]) / "best_model.pth",
        Path(cfg["paths"]["checkpoints"]) / "epoch_050.pth",
    ]
    ckpt = next((path for path in ckpt_candidates if path.exists()), None)
    if ckpt is None:
        raise FileNotFoundError("No trained checkpoint found in checkpoints/")
    print(f"Loading checkpoint: {ckpt}")

    load_model_weights(model, ckpt, map_location=device)

    evaluator = Evaluator(model, device)
    results = evaluator.evaluate(test_loader)

    out_path = Path(cfg["paths"]["results"]) / "eval_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {out_path}")
    print(f"MAE:  {results['mae']:.4f}")
    print(f"RMSE: {results['rmse']:.4f}")
    print("\nConfusion Matrix (rows=GT, cols=Pred):")
    print("         Low  Moderate  High")
    for i, cname in enumerate(["Low     ", "Moderate", "High    "]):
        row = results['confusion_matrix'][i]
        print(f"  {cname}: {row}")
    print("\nPer-class report:")
    for cls in ["low", "moderate", "high"]:
        r = results['report'].get(cls, {})
        print(f"  {cls:10s}: P={r.get('precision',0):.2f}  R={r.get('recall',0):.2f}  F1={r.get('f1-score',0):.2f}  support={r.get('support',0)}")


if __name__ == "__main__":
    main()
