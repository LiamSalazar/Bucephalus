from __future__ import annotations

import torch

from bucephalus.graphs.gnn_model import ManualGCN


def test_gnn_forward_backward():
    model = ManualGCN(input_dim=3, hidden_dim=4)
    x = torch.rand(2, 5, 3)
    adj = torch.eye(5).repeat(2, 1, 1)
    mask = torch.ones(2, 5)
    y = model(x, adj, mask)
    loss = y.sum()
    loss.backward()
    assert y.shape == (2,)
