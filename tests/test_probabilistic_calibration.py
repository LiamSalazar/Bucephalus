from __future__ import annotations

import polars as pl

from bucephalus.calibration.bootstrap import bootstrap_tactical_parameters
from bucephalus.utils.paths import ProjectPaths


def test_bootstrap_outputs_uncertainty(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame(
        [
            {"possession_proxy": 0.4, "pressing_proxy": 0.3, "directness_proxy": 0.5, "transition_proxy": 0.2},
            {"possession_proxy": 0.5, "pressing_proxy": 0.4, "directness_proxy": 0.6, "transition_proxy": 0.3},
            {"possession_proxy": 0.6, "pressing_proxy": 0.5, "directness_proxy": 0.4, "transition_proxy": 0.4},
            {"possession_proxy": 0.7, "pressing_proxy": 0.6, "directness_proxy": 0.3, "transition_proxy": 0.5},
            {"possession_proxy": 0.3, "pressing_proxy": 0.2, "directness_proxy": 0.7, "transition_proxy": 0.6},
            {"possession_proxy": 0.45, "pressing_proxy": 0.35, "directness_proxy": 0.55, "transition_proxy": 0.25},
        ]
    ).write_parquet(paths.features / "team_match_features.parquet")
    payload = bootstrap_tactical_parameters(paths, n_bootstraps=10, random_seed=1)
    assert payload["status"] == "completed"
    assert (paths.calibration_outputs / "tactical_parameter_uncertainty.json").exists()
