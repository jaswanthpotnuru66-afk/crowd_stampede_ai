import torch
import torch.nn as nn
from .swin_backbone import SwinBackbone
from .lstm_temporal import LSTMTemporal


class CrowdMonitor(nn.Module):
    """
    Full Swin-LSTM crowd monitoring model.
    Accepts a sequence of frames and outputs:
      - estimated crowd count
      - risk classification (0=low, 1=moderate, 2=high)
      - turbulence score [0, 1]
    """

    def __init__(self, cfg: dict | None = None):
        super().__init__()
        cfg = cfg or {}
        model_cfg = cfg.get("model", cfg)
        self.backbone = SwinBackbone(
            variant=model_cfg.get("swin_variant", "swin_tiny_patch4_window7_224"),
            pretrained=True,
            out_dim=512,
        )
        self.temporal = LSTMTemporal(
            input_dim=512,
            hidden_dim=model_cfg.get("lstm_hidden", 512),
            num_layers=model_cfg.get("lstm_layers", 2),
            num_classes=model_cfg.get("num_classes", 3),
        )

    def forward(self, x):
        """
        x: (B, T, C, H, W)
        Returns: density, risk_logits, turbulence
        """
        B, T, C, H, W = x.shape
        x_flat = x.view(B * T, C, H, W)
        feats = self.backbone(x_flat)          # (B*T, 512)
        feats = feats.view(B, T, -1)           # (B, T, 512)
        density, risk_logits, turbulence = self.temporal(feats)
        return density, risk_logits, turbulence
