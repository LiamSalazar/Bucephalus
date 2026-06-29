from __future__ import annotations

import torch
from torch import nn


class GRUSequenceModel(nn.Module):
    def __init__(self, input_dim: int = 8, hidden_dim: int = 24, dropout: float = 0.25):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Sequential(nn.Linear(hidden_dim, 16), nn.ReLU(), nn.Dropout(dropout), nn.Linear(16, 1))

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        out, _ = self.gru(x)
        if mask is not None:
            lengths = mask.sum(dim=1).clamp(min=1).long() - 1
            batch_idx = torch.arange(out.shape[0], device=out.device)
            pooled = out[batch_idx, lengths]
        else:
            pooled = out[:, -1]
        logits = self.head(self.dropout(pooled)).squeeze(-1)
        return logits
