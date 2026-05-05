"""
Risk-Head Fine-Tuning Script
=============================
Freezes the Swin backbone + LSTM, unfreezes only the risk_head Linear layer,
and trains it for a few epochs with corrected class weights.

This is a fast fix for the collapsed classifier (predicting everything as Low).
Typical runtime: ~10-20 minutes instead of 7+ hours.

Usage:
    python finetune_risk_head.py
"""
import runtime_bootstrap
from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.data.dataset import HajjV2VideoDataset
from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
from src.utils.config import load_config
from src.utils.logger import get_logger

log = get_logger("finetune_risk")

# ── tune these if needed ──────────────────────────────────────────
FINETUNE_EPOCHS  = 3
LR               = 5e-4
# Corrected weights: Moderate is scarce in train (151 vs Low=346, High=448)
# Use inverse-frequency: total=945, Low=346→945/346≈2.7, Mod=151→6.3, High=448→2.1
CLASS_WEIGHTS    = [2.7, 6.3, 2.1]
# ─────────────────────────────────────────────────────────────────


def evaluate_risk(model, loader, device):
    """Quick accuracy check for the risk classifier."""
    model.eval()
    correct = total = 0
    per_class = {0: [0, 0], 1: [0, 0], 2: [0, 0]}
    with torch.no_grad():
        for imgs, _, risk_labels in loader:
            imgs = imgs.to(device)
            _, risk_logits, _ = model(imgs)
            preds = risk_logits.argmax(dim=1).cpu()
            for gt, pred in zip(risk_labels.numpy(), preds.numpy()):
                per_class[int(gt)][1] += 1
                if int(gt) == int(pred):
                    per_class[int(gt)][0] += 1
            correct += (preds == risk_labels).sum().item()
            total   += risk_labels.size(0)

    acc = correct / max(total, 1)
    names = ["Low", "Moderate", "High"]
    for idx, name in enumerate(names):
        c, t = per_class[idx]
        recall = c / max(t, 1)
        log.info(f"  {name:10s}: recall={recall:.2f}  ({c}/{t})")
    return acc


def main():
    cfg = load_config()
    data_cfg = cfg["data"]
    risk_cfg = cfg.get("risk", {})
    risk_thresholds = (
        float(risk_cfg.get("label_low_count", 0.04)),
        float(risk_cfg.get("label_high_count", 0.07)),
    )

    # ── datasets ──────────────────────────────────────────────────
    train_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["train_list"],
        seq_len=data_cfg["seq_len"],
        stride=30,  # Balanced speed: sample every ~1 second for training
        img_size=224, 
        train=True,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )
    val_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["val_list"],
        seq_len=data_cfg["seq_len"],
        stride=60, # High-speed: sample every ~2 seconds for fast feedback
        img_size=224,
        train=False,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )

    train_loader = DataLoader(train_ds, batch_size=4, shuffle=True,
                              num_workers=0, pin_memory=False)
    val_loader   = DataLoader(val_ds,   batch_size=2, shuffle=False,
                              num_workers=0)

    log.info(f"Train={len(train_ds)} sequences  |  Val={len(val_ds)} sequences")

    # ── load best checkpoint ──────────────────────────────────────
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CrowdMonitor(cfg).to(device)

    ckpt_candidates = [
        Path(cfg["paths"]["checkpoints"]) / "best.pth",
        Path(cfg["paths"]["checkpoints"]) / "epoch_050.pth",
    ]
    ckpt = next((p for p in ckpt_candidates if p.exists()), None)
    if ckpt is None:
        raise FileNotFoundError("No checkpoint found. Run train.py first.")
    log.info(f"Loading checkpoint: {ckpt}")
    load_model_weights(model, ckpt, map_location=device)

    # ── freeze everything except risk_head ────────────────────────
    for name, param in model.named_parameters():
        param.requires_grad = ("risk_head" in name)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    log.info(f"Trainable params: {trainable:,} / {total:,}")

    # ── loss with corrected class weights ─────────────────────────
    cw = torch.tensor(CLASS_WEIGHTS, dtype=torch.float32).to(device)
    ce_loss = nn.CrossEntropyLoss(weight=cw)

    optimizer = AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=LR, weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=FINETUNE_EPOCHS)

    # baseline
    log.info("=== Baseline (before fine-tuning) ===")
    val_acc = evaluate_risk(model, val_loader, device)
    log.info(f"Val accuracy: {val_acc:.4f}")

    best_acc = val_acc
    ckpt_dir = Path(cfg["paths"]["checkpoints"])

    for epoch in range(1, FINETUNE_EPOCHS + 1):
        model.train()
        total_loss = 0.0
        pbar = tqdm(train_loader, desc=f"FT Epoch {epoch}", leave=False)
        for imgs, _, risk_labels in pbar:
            imgs        = imgs.to(device)
            risk_labels = risk_labels.to(device)

            # Backbone + LSTM are frozen (requires_grad=False), only risk_head trains.
            # A single forward pass is correct — PyTorch won't track gradients for
            # frozen params, so memory is efficient and the graph is clean.
            _, risk_logits, _ = model(imgs)

            loss = ce_loss(risk_logits, risk_labels)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.temporal.risk_head.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        scheduler.step()
        avg_loss = total_loss / max(len(train_loader), 1)

        val_acc = evaluate_risk(model, val_loader, device)
        log.info(f"Epoch {epoch:03d} | loss={avg_loss:.4f} | val_acc={val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            # Save the full model state (backbone + lstm + updated risk_head)
            full_ckpt = {
                "model": model.state_dict(),
                "epoch": f"finetune_{epoch}",
                "val_acc": val_acc,
            }
            torch.save(full_ckpt, ckpt_dir / "best.pth")
            log.info(f"  → New best val_acc={val_acc:.4f}, saved best.pth")

    log.info(f"Fine-tuning complete. Best val_acc: {best_acc:.4f}")
    log.info("Now run: python evaluate.py")


if __name__ == "__main__":
    main()
