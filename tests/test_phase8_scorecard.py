from __future__ import annotations

import json


def test_scorecard_components_if_present():
    try:
        payload = json.load(open("outputs/evaluation/phase8_model_scorecard.json", encoding="utf-8"))
    except FileNotFoundError:
        return
    components = {row["component"] for row in payload["rows"]}
    assert {"xG", "hazard", "EPV", "sequence", "MC Dropout", "vectorized Monte Carlo", "pass network", "GNN", "explainability"}.issubset(components)
    valid = {"champion", "candidate", "experimental", "rejected", "insufficient_data"}
    for row in payload["rows"]:
        assert row["status"] in valid
        if row["status"] == "champion":
            assert row["improvement_pct"] is not None
            assert row["improvement_pct"] > 0
