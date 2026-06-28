from __future__ import annotations

import polars as pl

from bucephalus.simulation.markov_calibration import calibrate_markov_matrix
from bucephalus.simulation.markov_validation import validate_markov_matrix
from bucephalus.utils.paths import ProjectPaths


def test_markov_calibration_outputs_valid_matrix(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame(
        {
            "match_id": [1] * 120,
            "possession": list(range(120)),
            "team_id": [10] * 120,
            "event_index": list(range(120)),
            "event_type": ["Pass"] * 119 + ["Shot"],
            "shot_outcome": [None] * 119 + ["Goal"],
            "location_x": [30.0, 70.0, 95.0, 110.0] * 30,
            "play_pattern_name": ["Regular Play"] * 120,
        }
    ).write_parquet(paths.processed / "events.parquet")
    report = calibrate_markov_matrix(paths)
    matrix = pl.read_parquet(paths.features / "markov_transition_matrix_global.parquet")
    assert report["rows_sum_to_one"]
    assert validate_markov_matrix(matrix)["no_negative_probabilities"]
