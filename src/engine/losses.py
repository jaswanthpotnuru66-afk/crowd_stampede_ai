import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss for imbalanced multi-class classification.
    Down-weights easy examples (high confidence correct predictions) so the
    model focuses training effort on hard, misclassified minority samples.
    FL(p_t) = -(1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None,
                 label_smoothing: float = 0.1):
        super().__init__()
        self.gamma           = gamma
        self.weight          = weight
        self.label_smoothing = label_smoothing

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Standard CE with label smoothing first
        ce = F.cross_entropy(
            logits, targets,
            weight=self.weight,
            label_smoothing=self.label_smoothing,
            reduction="none",
        )
        # p_t = probability of the correct class
        with torch.no_grad():
            pt = torch.exp(-F.cross_entropy(logits, targets, reduction="none"))
        focal_weight = (1.0 - pt) ** self.gamma
        return (focal_weight * ce).mean()


class CrowdLoss(nn.Module):
    def __init__(
        self,
        density_weight: float = 1.0,
        risk_weight: float = 4.0,
        risk_class_weights: list[float] | None = None,
        focal_gamma: float = 2.0,
        label_smoothing: float = 0.1,
    ):
        super().__init__()
        self.density_weight = density_weight
        self.risk_weight    = risk_weight
        self.mse            = nn.MSELoss()
        class_weights = None
        if risk_class_weights is not None:
            class_weights = torch.tensor(risk_class_weights, dtype=torch.float32)
        self.focal = FocalLoss(
            gamma=focal_gamma,
            weight=class_weights,
            label_smoothing=label_smoothing,
        )

    def forward(
        self,
        pred_density:  torch.Tensor,   # (B,)
        gt_density:    torch.Tensor,   # (B,)
        risk_logits:   torch.Tensor,   # (B, 3)
        risk_labels:   torch.Tensor,   # (B,)
    ) -> torch.Tensor:
        loss_d = self.mse(pred_density, gt_density)
        loss_r = self.focal(risk_logits, risk_labels)
        return self.density_weight * loss_d + self.risk_weight * loss_r
