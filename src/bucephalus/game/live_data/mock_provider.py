from __future__ import annotations

import json
from datetime import UTC, datetime

from bucephalus.utils.paths import ProjectPaths


class MockLiveProvider:
    provider_name = "mock_provider"

    def get_fixtures(self) -> list[dict]:
        return [{"id": "mock-fixture-1", "home": "Bucephalus Royals", "away": "Alexandria Analysts"}]

    def get_live_matches(self) -> list[dict]:
        return [{"id": "mock-fixture-1", "minute": 0, "status": "scheduled"}]

    def get_lineups(self, match_id: str) -> dict:
        return {"match_id": match_id, "home": [], "away": []}

    def get_events(self, match_id: str) -> list[dict]:
        _ = match_id
        return []

    def get_match_stats(self, match_id: str) -> dict:
        return {"match_id": match_id, "xg_home": None, "xg_away": None}

    def get_player_stats(self, match_id: str) -> list[dict]:
        _ = match_id
        return []

    def get_standings(self) -> list[dict]:
        return []

    def get_squads(self) -> list[dict]:
        return []


def write_provider_health_report(paths: ProjectPaths | None = None) -> dict:
    paths = paths or ProjectPaths()
    provider = MockLiveProvider()
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "providers": [{"provider": provider.provider_name, "status": "ok", "fixtures": len(provider.get_fixtures())}],
        "warnings": ["commercial live providers require API keys; mock provider used for tests"],
    }
    out = paths.outputs / "live" / "provider_health_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
