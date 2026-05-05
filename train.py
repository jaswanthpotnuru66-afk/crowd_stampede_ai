"""
STEP 2 - Train the Swin-LSTM model.

Usage:
    python train.py
"""
import runtime_bootstrap
from torch.utils.data import DataLoader

from src.data.dataset import HajjV2VideoDataset
from src.engine.trainer import Trainer
from src.utils.config import load_config


def main():
    cfg = load_config()
    data_cfg = cfg["data"]
    train_cfg = cfg["training"]
    risk_cfg = cfg.get("risk", {})
    risk_thresholds = (
        float(risk_cfg.get("label_low_count", 0.04)),
        float(risk_cfg.get("label_high_count", 0.07)),
    )

    # CPU SPEED OPTIMIZATION: Increasing stride reduces total training volume
    # from ~900 sequences to ~220 sequences for the fast 5-epoch demo.
    stride = train_cfg.get("stride", 5)
    train_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["train_list"],
        seq_len=train_cfg["seq_len"],
        stride=stride, 
        img_size=data_cfg["img_size"],
        train=True,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )
    val_ds = HajjV2VideoDataset(
        root=data_cfg["root"],
        split_file=data_cfg["val_list"],
        seq_len=train_cfg["seq_len"],
        stride=stride,
        img_size=data_cfg["img_size"],
        train=False,
        risk_thresholds=risk_thresholds,
        risk_cfg=risk_cfg,
    )

    print(f"Train sequences: {len(train_ds)}  |  Val sequences: {len(val_ds)}")

    train_loader = DataLoader(
        train_ds,
        batch_size=train_cfg["batch_size"],
        shuffle=True,
        num_workers=data_cfg["num_workers"],
        pin_memory=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=2,
        shuffle=False,
        num_workers=max(data_cfg["num_workers"] // 2, 0),
        pin_memory=False,
    )

    trainer = Trainer(cfg)
    trainer.train(train_loader, val_loader)

    print("\nNext step: python export_onnx.py")


if __name__ == "__main__":
    main()
