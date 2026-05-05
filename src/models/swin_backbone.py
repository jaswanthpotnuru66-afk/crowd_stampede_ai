import torch
import torch.nn as nn
import timm


class SwinBackbone(nn.Module):
    """
    Swin Transformer backbone for spatial feature extraction.
    Outputs per-frame feature vectors of dim `out_dim`.
    """

    def __init__(self, variant: str = "swin_tiny_patch4_window7_224",
                 pretrained: bool = True, out_dim: int = 512):
        super().__init__()
        self.swin = timm.create_model(
            variant,
            pretrained=pretrained,
            num_classes=0,          # remove head
            global_pool="avg",
        )
        feat_dim = self.swin.num_features
        self.proj = nn.Sequential(
            nn.Linear(feat_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.GELU(),
        )

    def forward(self, x):
        """x: (B, C, H, W) → (B, out_dim)"""
        feat = self.swin(x)
        return self.proj(feat)