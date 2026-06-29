from __future__ import annotations

import torch
from torch import nn


class ManualGCN(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 16, dropout: float = 0.2):
        super().__init__()
        self.lin1 = nn.Linear(input_dim, hidden_dim)
        self.lin2 = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Sequential(nn.Linear(hidden_dim, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x: torch.Tensor, adj: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        h = torch.relu(torch.bmm(adj, self.lin1(x)))
        h = self.dropout(torch.relu(torch.bmm(adj, self.lin2(h))))
        masked = h * mask.unsqueeze(-1)
        pooled = masked.sum(dim=1) / mask.sum(dim=1).clamp(min=1).unsqueeze(-1)
        return self.head(pooled).squeeze(-1)
