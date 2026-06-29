from __future__ import annotations

import polars as pl

from bucephalus.graphs.pass_network import build_pass_networks
from bucephalus.utils.paths import ProjectPaths


def test_pass_network_generates_proxy_edges(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame([
        {"match_id": 1, "possession": 1, "event_index": 1, "event_id": "a", "type_name": "Pass", "team_id": 1, "team_name": "A", "player_id": 10, "player_name": "P1", "position_name": "CM", "location_x": 30, "location_y": 40, "pass_end_x": 50, "pass_end_y": 40, "under_pressure": False},
        {"match_id": 1, "possession": 1, "event_index": 2, "event_id": "b", "type_name": "Carry", "team_id": 1, "team_name": "A", "player_id": 11, "player_name": "P2", "position_name": "FW", "location_x": 50, "location_y": 40, "pass_end_x": None, "pass_end_y": None, "under_pressure": False},
    ]).write_parquet(paths.processed / "events.parquet")
    payload = build_pass_networks(paths)
    assert payload["status"] == "completed"
    assert payload["receiver_policy"] == "next_same_team_event_proxy"
    assert pl.read_parquet(paths.features / "pass_network_edges.parquet").height == 1


def test_pass_network_uses_real_receiver_when_present(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame([
        {"match_id": 1, "possession": 1, "event_index": 1, "event_id": "a", "type_name": "Pass", "team_id": 1, "team_name": "A", "player_id": 10, "player_name": "P1", "position_name": "CM", "location_x": 30, "location_y": 40, "pass_end_x": 50, "pass_end_y": 40, "pass_recipient_id": 11, "pass_recipient_name": "P2", "under_pressure": False},
        {"match_id": 1, "possession": 1, "event_index": 2, "event_id": "b", "type_name": "Carry", "team_id": 1, "team_name": "A", "player_id": 11, "player_name": "P2", "position_name": "FW", "location_x": 50, "location_y": 40, "pass_end_x": None, "pass_end_y": None, "pass_recipient_id": None, "pass_recipient_name": None, "under_pressure": False},
    ]).write_parquet(paths.processed / "events.parquet")
    payload = build_pass_networks(paths)
    edges = pl.read_parquet(paths.features / "pass_network_edges.parquet")
    assert payload["receiver_policy"] == "statsbomb_pass_recipient"
    assert edges["receiver_id"][0] == 11
