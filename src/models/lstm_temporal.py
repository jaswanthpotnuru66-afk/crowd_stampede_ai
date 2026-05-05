import torch
import torch.nn as nn


class LSTMTemporal(nn.Module):
    """
    LSTM module that models temporal crowd evolution.
    Input: (B, T, feat_dim)
    Output: density count, risk logits, turbulence score
    """

    def __init__(self, input_dim: int = 512, hidden_dim: int = 512,
                 num_layers: int = 2, num_classes: int = 3, dropout: float = 0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.density_head = nn.Linear(hidden_dim, 1)
        self.risk_head = nn.Linear(hidden_dim, num_classes)
        self.turbulence_head = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        """x: (B, T, input_dim)"""
        out, (h_n, _) = self.lstm(x)

        # Density & turbulence use the final timestep (most recent state)
        last = self.dropout(out[:, -1, :])           # (B, hidden_dim)
        density    = self.density_head(last).squeeze(-1)
        turbulence = torch.sigmoid(self.turbulence_head(last)).squeeze(-1)

        # Risk head uses mean pooling across ALL timesteps — sees the full
        # crowd dynamics pattern (build-up, peak, dispersion) not just the end
        pooled      = self.dropout(out.mean(dim=1))  # (B, hidden_dim)
        risk_logits = self.risk_head(pooled)

        return density, risk_logits, turbulence