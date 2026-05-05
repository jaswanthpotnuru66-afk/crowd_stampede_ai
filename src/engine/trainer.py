from pathlib import Path

import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.engine.losses import CrowdLoss
from src.models.crowd_monitor import CrowdMonitor
from src.utils.logger import get_logger

log = get_logger("trainer")


class Trainer:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.device = cfg.get("inference", {}).get("device", "cpu")
        if self.device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
        self.train_cfg = cfg.get("training") or cfg.get("train") or {}
        self.paths_cfg = cfg.get("paths", {})

        self.model = CrowdMonitor(cfg).to(self.device)
        self.loss_fn = CrowdLoss(
            density_weight=self.train_cfg.get("density_loss_weight", 1.0),
            risk_weight=self.train_cfg.get("risk_loss_weight", 4.0),
            risk_class_weights=self.train_cfg.get("risk_class_weights"),
            focal_gamma=self.train_cfg.get("focal_gamma", 2.0),
            label_smoothing=self.train_cfg.get("label_smoothing", 0.1),
        ).to(self.device)
        self.density_scale = float(self.train_cfg.get("density_scale", 500.0))
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.train_cfg["lr"],
            weight_decay=self.train_cfg["weight_decay"],
        )
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=self.train_cfg["epochs"])

        self.ckpt_dir = Path(self.paths_cfg.get("checkpoints", "checkpoints"))
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.best_mae = float("inf")
        self.start_epoch = 1
        self._maybe_resume()

    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        epochs = self.train_cfg["epochs"]
        log.info(f"Starting training for {epochs} epochs on {self.device}")
        if self.start_epoch > 1:
            log.info(f"Resuming from epoch {self.start_epoch:03d} with best_mae={self.best_mae:.2f}")

        for epoch in range(self.start_epoch, epochs + 1):
            train_loss = self._train_epoch(train_loader, epoch)
            val_mae = self._val_epoch(val_loader)
            self.scheduler.step()

            log.info(f"Epoch {epoch:03d} | loss={train_loss:.4f} | val_mae={val_mae:.2f}")

            self._save("last.pth", epoch=epoch, val_mae=val_mae)

            if epoch % self.train_cfg.get("save_every", 5) == 0:
                self._save(f"epoch_{epoch:03d}.pth", epoch=epoch, val_mae=val_mae)

            if val_mae < self.best_mae:
                self.best_mae = val_mae
                self._save("best.pth", epoch=epoch, val_mae=val_mae)
                log.info(f"  New best MAE: {val_mae:.2f} -> saved best.pth")

        log.info("Training complete.")

    def _train_epoch(self, loader: DataLoader, epoch: int) -> float:
        self.model.train()
        total_loss = 0.0

        pbar = tqdm(loader, desc=f"Train {epoch}", leave=False)
        for imgs, density_maps, risk_labels in pbar:
            imgs = imgs.to(self.device)
            density_maps = density_maps.to(self.device)
            risk_labels = risk_labels.to(self.device)

            pred_density, risk_logits, _ = self.model(imgs)
            density_target = density_maps[:, -1].sum(dim=[1, 2])
            loss = self.loss_fn(
                pred_density / self.density_scale,
                density_target / self.density_scale,
                risk_logits,
                risk_labels,
            )

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.train_cfg.get("grad_clip", 1.0),
            )
            self.optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        return total_loss / max(len(loader), 1)

    @torch.no_grad()
    def _val_epoch(self, loader: DataLoader) -> float:
        self.model.eval()
        maes = []

        for imgs, density_maps, _ in loader:
            imgs = imgs.to(self.device)
            pred_density, _, _ = self.model(imgs)

            gt_count = density_maps[:, -1].sum(dim=[1, 2]).cpu().numpy()
            pred_count = pred_density.cpu().numpy()
            maes.extend(abs(pred_count - gt_count).tolist())

        return float(sum(maes) / max(len(maes), 1))

    def _save(self, name: str, epoch: int | None = None, val_mae: float | None = None):
        path = self.ckpt_dir / name
        torch.save(
            {
                "epoch": epoch,
                "model": self.model.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "scheduler": self.scheduler.state_dict(),
                "best_mae": self.best_mae,
                "val_mae": val_mae,
            },
            path,
        )

    def _maybe_resume(self):
        if not self.train_cfg.get("resume", False):
            return

        resume_path = Path(self.train_cfg.get("resume_path", self.ckpt_dir / "last.pth"))
        if not resume_path.exists():
            return

        checkpoint = torch.load(resume_path, map_location=self.device)
        state_dict = checkpoint.get("model", checkpoint)
        self.model.load_state_dict(state_dict)

        if "optimizer" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer"])
        if "scheduler" in checkpoint:
            self.scheduler.load_state_dict(checkpoint["scheduler"])

        self.best_mae = float(checkpoint.get("best_mae", checkpoint.get("val_mae", self.best_mae)))
        last_epoch = int(checkpoint.get("epoch") or 0)
        self.start_epoch = last_epoch + 1
        log.info(f"Loaded resume checkpoint from {resume_path}")
