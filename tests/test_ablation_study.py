from __future__ import annotations

import csv

from bucephalus.simulation.ablation import run_ablation_study
from bucephalus.utils.paths import ProjectPaths
from tests.test_scenario_simulation import test_scenario_simulates_from_tactical_inputs_and_sliders_change


def test_ablation_study_outputs_expected_models(tmp_path) -> None:
    test_scenario_simulates_from_tactical_inputs_and_sliders_change(tmp_path)
    paths = ProjectPaths(data_root=tmp_path / "data")
    run_ablation_study(paths, n_simulations=20)
    rows = list(csv.DictReader((paths.evaluation_outputs / "ablation_study.csv").open()))
    names = {row["ablation"] for row in rows}
    assert {"baseline_only", "full_calibrated_simulation"}.issubset(names)
