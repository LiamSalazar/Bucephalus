from __future__ import annotations

import numpy as np
import json

from bucephalus.graphs.graph_dataset import _normalize_adj


def test_gnn_normalized_adjacency_finite():
    adj = _normalize_adj(np.eye(3))
    assert np.isfinite(adj).all()


def test_gnn_validation_report_if_present():
    try:
        report = json.load(open("outputs/evaluation/gnn_validation_report.json", encoding="utf-8"))
    except FileNotFoundError:
        return
    if report.get("status") == "insufficient_data":
        return
    assert "tabular_graph_mae" in report
    assert report["random_labels_test"] in {"passed", "warning"}
    assert report["does_gnn_add_value_beyond_graph_metrics"] in {"YES", "NO", "INCONCLUSIVE"}
