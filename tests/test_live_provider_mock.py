from __future__ import annotations

import json

from bucephalus.game.live_data.mock_provider import MockLiveProvider, write_provider_health_report
from bucephalus.utils.paths import ProjectPaths


def test_mock_live_provider_health_report(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    provider = MockLiveProvider()
    report = write_provider_health_report(paths)

    assert provider.get_live_matches()
    assert report["providers"][0]["status"] == "ok"
    assert json.loads(paths.outputs.joinpath("live", "provider_health_report.json").read_text())
