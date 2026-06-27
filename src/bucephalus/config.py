from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from bucephalus.utils.paths import ProjectPaths


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[2]
    paths: ProjectPaths = ProjectPaths()
    statsbomb_base_url: str = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
    default_max_matches: int = 3
    default_use_sample: bool = True
    default_skip_360: bool = False
    random_seed: int = 202607

    @property
    def data_root(self) -> Path:
        return Path(os.getenv("BUCEPHALUS_DATA_ROOT", str(self.paths.data)))

    @property
    def raw_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def interim_dir(self) -> Path:
        return self.data_root / "interim"

    @property
    def processed_dir(self) -> Path:
        return self.data_root / "processed"

    @property
    def features_dir(self) -> Path:
        return self.data_root / "features"

    @property
    def samples_dir(self) -> Path:
        return self.data_root / "samples"

    @property
    def outputs_dir(self) -> Path:
        return self.paths.outputs

    @property
    def eda_outputs_dir(self) -> Path:
        return self.paths.eda_outputs

    @property
    def quality_outputs_dir(self) -> Path:
        return self.paths.quality_outputs


settings = Settings()
