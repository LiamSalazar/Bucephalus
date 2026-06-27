from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = Path(__file__).resolve().parents[3]
    data_root: Path | None = None

    @property
    def data(self) -> Path:
        env_root = os.getenv("BUCEPHALUS_DATA_ROOT")
        if self.data_root is not None:
            return Path(self.data_root)
        if env_root:
            return Path(env_root)
        return self.root / "data"

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def interim(self) -> Path:
        return self.data / "interim"

    @property
    def processed(self) -> Path:
        return self.data / "processed"

    @property
    def features(self) -> Path:
        return self.data / "features"

    @property
    def samples(self) -> Path:
        return self.data / "samples"

    @property
    def outputs(self) -> Path:
        if self.data_root is not None:
            return Path(self.data_root).parent / "outputs"
        if os.getenv("BUCEPHALUS_DATA_ROOT"):
            return self.data.parent / "outputs"
        return self.root / "outputs"

    @property
    def eda_outputs(self) -> Path:
        return self.outputs / "eda"

    @property
    def eda_tables(self) -> Path:
        return self.eda_outputs / "tables"

    @property
    def eda_figures(self) -> Path:
        return self.eda_outputs / "figures"

    @property
    def quality_outputs(self) -> Path:
        return self.outputs / "quality"

    @property
    def models_outputs(self) -> Path:
        return self.outputs / "models"

    @property
    def evaluation_outputs(self) -> Path:
        return self.outputs / "evaluation"

    @property
    def duckdb_path(self) -> Path:
        return self.processed / "bucephalus.duckdb"

    def ensure(self) -> None:
        for path in [
            self.raw,
            self.interim,
            self.processed,
            self.features,
            self.samples,
            self.eda_tables,
            self.eda_figures,
            self.quality_outputs,
            self.models_outputs,
            self.evaluation_outputs,
        ]:
            path.mkdir(parents=True, exist_ok=True)
