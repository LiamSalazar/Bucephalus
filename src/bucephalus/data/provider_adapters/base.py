from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ProviderResult:
    provider: str
    status: str
    rows: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ProviderAdapter(Protocol):
    provider_name: str

    def fetch_competitions(self) -> ProviderResult: ...
    def fetch_fixtures(self) -> ProviderResult: ...
    def fetch_teams(self) -> ProviderResult: ...
    def fetch_players(self) -> ProviderResult: ...
    def fetch_lineups(self, match_id: int | None = None) -> ProviderResult: ...
    def fetch_events(self, match_id: int | None = None) -> ProviderResult: ...
    def fetch_match_stats(self, match_id: int | None = None) -> ProviderResult: ...
    def fetch_live_state(self, match_id: int | None = None) -> ProviderResult: ...


class KeyedAPIAdapter:
    provider_name = "base_api"
    env_var = ""

    def __init__(self, api_key: str | None = None) -> None:
        import os

        self.api_key = api_key or os.getenv(self.env_var)

    def _unavailable(self, method: str) -> ProviderResult:
        warning = f"{self.env_var} not configured; {method} disabled."
        return ProviderResult(provider=self.provider_name, status="provider_unavailable", warnings=[warning])

    def fetch_competitions(self) -> ProviderResult:
        return self._unavailable("fetch_competitions")

    def fetch_fixtures(self) -> ProviderResult:
        return self._unavailable("fetch_fixtures")

    def fetch_teams(self) -> ProviderResult:
        return self._unavailable("fetch_teams")

    def fetch_players(self) -> ProviderResult:
        return self._unavailable("fetch_players")

    def fetch_lineups(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._unavailable("fetch_lineups")

    def fetch_events(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._unavailable("fetch_events")

    def fetch_match_stats(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._unavailable("fetch_match_stats")

    def fetch_live_state(self, match_id: int | None = None) -> ProviderResult:
        _ = match_id
        return self._unavailable("fetch_live_state")
