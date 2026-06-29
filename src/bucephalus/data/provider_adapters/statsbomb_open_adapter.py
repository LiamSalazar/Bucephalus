from __future__ import annotations

import polars as pl

from bucephalus.data.provider_adapters.base import ProviderResult
from bucephalus.utils.paths import ProjectPaths


class StatsBombOpenAdapter:
    provider_name = "statsbomb_open"

    def __init__(self, paths: ProjectPaths | None = None) -> None:
        self.paths = paths or ProjectPaths()

    def _read(self, table: str) -> ProviderResult:
        path = self.paths.processed / f"{table}.parquet"
        if not path.exists():
            return ProviderResult(self.provider_name, "missing", warnings=[f"{table}.parquet missing"])
        rows = pl.read_parquet(path).to_dicts()
        return ProviderResult(self.provider_name, "ok", rows=rows)

    def fetch_competitions(self) -> ProviderResult:
        return self._read("competitions")

    def fetch_fixtures(self) -> ProviderResult:
        return self._read("matches")

    def fetch_teams(self) -> ProviderResult:
        return self._read("teams")

    def fetch_players(self) -> ProviderResult:
        return self._read("players")

    def fetch_lineups(self, match_id: int | None = None) -> ProviderResult:
        result = self._read("lineups")
        if match_id is not None:
            result.rows = [row for row in result.rows if row.get("match_id") == match_id]
        return result

    def fetch_events(self, match_id: int | None = None) -> ProviderResult:
        result = self._read("events")
        if match_id is not None:
            result.rows = [row for row in result.rows if row.get("match_id") == match_id]
        return result

    def fetch_match_stats(self, match_id: int | None = None) -> ProviderResult:
        result = self._read("team_match_features")
        if result.status == "missing":
            path = self.paths.features / "team_match_features.parquet"
            if path.exists():
                result = ProviderResult(self.provider_name, "ok", rows=pl.read_parquet(path).to_dicts())
        if match_id is not None:
            result.rows = [row for row in result.rows if row.get("statsbomb_match_id") == match_id or row.get("match_id") == match_id]
        return result

    def fetch_live_state(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return ProviderResult(self.provider_name, "not_live", warnings=["StatsBomb Open Data is historical, not live."])
