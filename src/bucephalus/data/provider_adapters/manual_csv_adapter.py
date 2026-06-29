from __future__ import annotations

from pathlib import Path

import polars as pl

from bucephalus.data.provider_adapters.base import ProviderResult
from bucephalus.utils.paths import ProjectPaths


class ManualCSVAdapter:
    provider_name = "manual_csv"

    def __init__(self, root: Path | None = None, paths: ProjectPaths | None = None) -> None:
        self.paths = paths or ProjectPaths()
        self.root = root or self.paths.samples / "manual_csv"

    def _read(self, name: str) -> ProviderResult:
        path = self.root / f"{name}.csv"
        if not path.exists():
            return ProviderResult(self.provider_name, "missing", warnings=[f"{path} missing"])
        return ProviderResult(self.provider_name, "ok", rows=pl.read_csv(path).to_dicts())

    def fetch_competitions(self) -> ProviderResult:
        return self._read("competitions")

    def fetch_fixtures(self) -> ProviderResult:
        return self._read("fixtures")

    def fetch_teams(self) -> ProviderResult:
        return self._read("teams")

    def fetch_players(self) -> ProviderResult:
        return self._read("players")

    def fetch_lineups(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._read("lineups")

    def fetch_events(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._read("events")

    def fetch_match_stats(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._read("match_stats")

    def fetch_live_state(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._read("live_state")
