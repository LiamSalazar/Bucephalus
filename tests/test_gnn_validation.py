from __future__ import annotations

import numpy as np

from bucephalus.graphs.graph_dataset import _normalize_adj


def test_gnn_normalized_adjacency_finite():
    adj = _normalize_adj(np.eye(3))
    assert np.isfinite(adj).all()
