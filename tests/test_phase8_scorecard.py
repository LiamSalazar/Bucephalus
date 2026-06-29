from __future__ import annotations

import json


def test_scorecard_components_if_present():
    try:
        payload = json.load(open("outputs/evaluation/phase8_model_scorecard.json", encoding="utf-8"))
    except FileNotFoundError:
        return
    components = {row["component"] for row in payload["rows"]}
    assert {"xG", "hazard", "sequence", "GNN"}.issubset(components)
