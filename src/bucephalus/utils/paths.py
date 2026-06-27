from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = Path(__file__).resolve().parents[3]

    @property
    def data(self) -> Path:
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

    def ensure(self) -> None:
        for path in [
            self.raw,
            self.interim,
            self.processed,
            self.features,
            self.samples,
            self.eda_tables,
            self.eda_figures,
        ]:
            path.mkdir(parents=True, exist_ok=True)
