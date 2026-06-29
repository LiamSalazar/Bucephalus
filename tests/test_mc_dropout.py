from __future__ import annotations

import polars as pl
import torch

from bucephalus.deep.sequence_encoder import GRUSequenceModel
from bucephalus.deep.inference import run_mc_dropout
from bucephalus.utils.paths import ProjectPaths


def test_mc_dropout_produces_variance(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    model = GRUSequenceModel(input_dim=8, hidden_dim=4, dropout=0.5)
    torch.save({"state_dict": model.state_dict(), "input_dim": 8, "hidden_dim": 4, "dropout": 0.5}, paths.models_outputs / "sequence_model.pt")
    pl.DataFrame(
        [
            {"match_id": 1, "possession": 1, "event_index": 1, "type_name": "Pass", "location_x": 40, "location_y": 30},
            {"match_id": 1, "possession": 1, "event_index": 2, "type_name": "Shot", "location_x": 100, "location_y": 40},
        ]
    ).write_parquet(paths.processed / "events.parquet")
    payload = run_mc_dropout(paths, n_mc_samples=10)
    assert payload["status"] == "completed"
    assert payload["mean_epistemic_uncertainty"] > 0
