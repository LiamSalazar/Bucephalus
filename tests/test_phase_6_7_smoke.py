from __future__ import annotations

import subprocess
import sys

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.features.feature_store import build_feature_store
from bucephalus.tactics.style_profiles import build_tactical_engine_inputs
from bucephalus.utils.paths import ProjectPaths


def test_phase_6_7_smoke(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    download_sample(paths=paths, max_matches=2, force_fallback=True)
    process_raw_to_parquet(paths)
    build_master_entities(paths)
    build_feature_store(paths)
    build_tactical_engine_inputs(paths)
    subprocess.run([sys.executable, "scripts/10_run_tactical_scenario.py", "--auto-pick-teams", "--data-root", str(paths.data)], check=True)
    subprocess.run([sys.executable, "scripts/11_run_match_simulation.py", "--auto-pick-teams", "--n-simulations", "50", "--data-root", str(paths.data)], check=True)
    subprocess.run([sys.executable, "scripts/12_run_sensitivity_analysis.py", "--auto-pick-teams", "--values=-0.2,0,0.2", "--n-simulations", "30", "--data-root", str(paths.data)], check=True)
    subprocess.run([sys.executable, "scripts/97_run_phase_6_7_check.py", "--skip-tests", "--data-root", str(paths.data)], check=True)
