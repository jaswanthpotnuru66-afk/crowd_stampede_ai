import numpy as np
import torch
from torch.utils.data import DataLoader

from src.utils.logger import get_logger

log = get_logger("evaluator")

CLASS_NAMES = ["Low", "Moderate", "High"]


def _confusion_matrix(y_true: list[int], y_pred: list[int], num_classes: int = 3) -> list[list[int]]:
    matrix = [[0 for _ in range(num_classes)] for _ in range(num_classes)]
    for true, pred in zip(y_true, y_pred):
        if 0 <= true < num_classes and 0 <= pred < num_classes:
            matrix[true][pred] += 1
    return matrix


def _classification_report(y_true: list[int], y_pred: list[int]) -> dict:
    matrix = _confusion_matrix(y_true, y_pred, len(CLASS_NAMES))
    report = {}

    for idx, name in enumerate(CLASS_NAMES):
        tp = matrix[idx][idx]
        fp = sum(matrix[row][idx] for row in range(len(CLASS_NAMES)) if row != idx)
        fn = sum(matrix[idx][col] for col in range(len(CLASS_NAMES)) if col != idx)
        support = sum(matrix[idx])

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)

        report[name.lower()] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1-score": float(f1),
            "support": int(support),
        }

    accuracy = sum(matrix[i][i] for i in range(len(CLASS_NAMES))) / max(len(y_true), 1)
    report["accuracy"] = float(accuracy)
    return report


def _format_report(report: dict) -> str:
    lines = ["              precision    recall  f1-score   support"]
    for name in CLASS_NAMES:
        item = report[name.lower()]
        lines.append(
            f"{name:>10}      {item['precision']:.2f}      {item['recall']:.2f}"
            f"      {item['f1-score']:.2f}        {item['support']}"
        )
    lines.append(f"\n  accuracy                          {report['accuracy']:.2f}")
    return "\n".join(lines)


class Evaluator:
    def __init__(self, model, device: str = "cuda"):
        self.model = model
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).eval()

    @torch.no_grad()
    def evaluate(self, loader: DataLoader) -> dict:
        maes, mses = [], []
        all_preds, all_gt = [], []

        for imgs, density_maps, risk_labels in loader:
            imgs = imgs.to(self.device)
            pred_density, risk_logits, _ = self.model(imgs)

            gt_count = density_maps[:, -1].sum(dim=[1, 2]).cpu().numpy()
            pred_count = pred_density.cpu().numpy()

            maes.extend(abs(pred_count - gt_count).tolist())
            mses.extend(((pred_count - gt_count) ** 2).tolist())

            preds = risk_logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds.tolist())
            all_gt.extend(risk_labels.numpy().tolist())

        mae = float(np.mean(maes))
        rmse = float(np.sqrt(np.mean(mses)))
        report = _classification_report(all_gt, all_preds)
        conf = _confusion_matrix(all_gt, all_preds)

        log.info(f"MAE:  {mae:.4f}")
        log.info(f"RMSE: {rmse:.4f}")
        log.info("\n" + _format_report(report))

        return {
            "mae": mae,
            "rmse": rmse,
            "confusion_matrix": conf,
            "report": report,
        }
