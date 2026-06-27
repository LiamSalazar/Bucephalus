from __future__ import annotations

import subprocess
import sys

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.data.research_summary import write_research_dataset_summary
from bucephalus.data.validation import validate_data_quality
from bucephalus.features.feature_store import build_feature_store
from bucephalus.utils.paths import ProjectPaths


def test_phase_4_5_smoke(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    download_sample(paths=paths, max_matches=2, force_fallback=True)
    process_raw_to_parquet(paths)
    validate_data_quality(paths)
    write_research_dataset_summary(paths)
    build_master_entities(paths)
    build_feature_store(paths)
    subprocess.run([sys.executable, "scripts/07_train_baseline_models.py", "--data-root", str(paths.data)], check=True)
    subprocess.run([sys.executable, "scripts/98_run_phase_4_5_check.py", "--data-root", str(paths.data), "--skip-tests"], check=True)
