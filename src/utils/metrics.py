import numpy as np


def compute_mae(preds: list, targets: list) -> float:
    return float(np.mean(np.abs(np.array(preds) - np.array(targets))))


def compute_rmse(preds: list, targets: list) -> float:
    return float(np.sqrt(np.mean((np.array(preds) - np.array(targets)) ** 2)))


def compute_accuracy(preds: list, targets: list) -> float:
    preds   = np.array(preds)
    targets = np.array(targets)
    return float((preds == targets).mean())