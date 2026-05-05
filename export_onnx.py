"""
STEP 4 - Export trained model to ONNX for fast inference.

Usage:
    python export_onnx.py
"""
import runtime_bootstrap
from pathlib import Path

import torch

from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
from src.utils.config import load_config


def main():
    cfg = load_config()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt_candidates = [
        Path(cfg["paths"]["checkpoints"]) / "best.pth",
        Path(cfg["paths"]["checkpoints"]) / "best_model.pth",
    ]
    ckpt = next((path for path in ckpt_candidates if path.exists()), None)
    if ckpt is None:
        raise FileNotFoundError("No trained checkpoint found in checkpoints/")

    out_path = Path(cfg["paths"]["exports"]) / "crowd_model.onnx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    model = CrowdMonitor(cfg)
    load_model_weights(model, ckpt, map_location=device)
    model = model.to(device).eval()

    seq_len = cfg["data"]["seq_len"]
    img_size = cfg["data"]["img_size"]
    dummy = torch.randn(1, seq_len, 3, img_size, img_size).to(device)

    torch.onnx.export(
        model,
        dummy,
        str(out_path),
        opset_version=17,
        input_names=["frames"],
        output_names=["pred_density", "risk_logits", "turbulence"],
        dynamic_axes={"frames": {0: "batch"}},
    )

    print(f"Exported ONNX model to {out_path}")
    print("Next step: run the API with uvicorn api.main:app --reload")


if __name__ == "__main__":
    main()
