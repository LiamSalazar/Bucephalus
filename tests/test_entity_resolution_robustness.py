from __future__ import annotations

import json

import polars as pl

from bucephalus.data.entity_resolution import _master_players, stable_entity_id


def test_canonical_name_stable_under_order_and_aliases_preserved() -> None:
    rows = [
        {"player_id": 1, "player_name": "J. Bellingham", "team_id": 10, "team_name": "A", "country_name": "England", "position_names": "Midfield"},
        {"player_id": 1, "player_name": "Jude Bellingham", "team_id": 10, "team_name": "A", "country_name": "England", "position_names": "Midfield"},
        {"player_id": 1, "player_name": "Jude Bellingham", "team_id": 11, "team_name": "B", "country_name": "England", "position_names": "Midfield"},
    ]
    a = _master_players(pl.DataFrame(rows))
    b = _master_players(pl.DataFrame(list(reversed(rows))))
    assert a["canonical_player_name"][0] == b["canonical_player_name"][0] == "Jude Bellingham"
    aliases = json.loads(a["aliases_json"][0])
    assert "J. Bellingham" in aliases
    assert stable_entity_id("ply", 1, "jude bellingham") == stable_entity_id("ply", 1, "jude bellingham")
