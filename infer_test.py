import runtime_bootstrap
import json
import torch
import numpy as np
from src.utils.config import load_config
from src.data.dataset import HajjV2VideoDataset
from torch.utils.data import DataLoader
from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
from src.engine.evaluator import _classification_report, _format_report

def main():
    cfg = load_config()
    data_cfg = cfg["data"]
    risk_cfg = cfg.get("risk", {})
    risk_thresholds = (
        float(risk_cfg.get("label_low_count", 386.0)),
        float(risk_cfg.get("label_high_count", 436.6)),
    )

    test_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["test_list"],
        train=False,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )
    test_loader = DataLoader(test_ds, batch_size=2, shuffle=False)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CrowdMonitor(cfg)
    load_model_weights(model, "checkpoints/best.pth", map_location=device)
    model.to(device).eval()

    all_gt, all_preds = [], []
    maes = []
    with torch.no_grad():
        for imgs, density_maps, risk_labels in test_loader:
            pred_density, _, _ = model(imgs.to(device))
            
            gt_count = density_maps[:, -1].sum(dim=[1, 2]).numpy()
            pred_count = pred_density.cpu().numpy()
            maes.extend(abs(pred_count - gt_count).tolist())

            all_gt.extend(risk_labels.numpy().tolist())
            all_preds.extend(risk_logits.argmax(dim=1).cpu().numpy().tolist())

    report = _classification_report(all_gt, all_preds)
    print(f"MAE: {np.mean(maes):.4f}")
    print(_format_report(report))

if __name__ == "__main__":
    main()
