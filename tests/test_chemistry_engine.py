from __future__ import annotations

from bucephalus.game.chemistry import calculate_chemistry

from tests.game_helpers import seed_game


def test_chemistry_flags_haaland_mbappe_and_vinicius_haaland(tmp_path):
    repo, _, _, _ = seed_game(tmp_path)
    haaland_mbappe = [repo.get("players", pid) for pid in ["haaland", "mbappe"]]
    vinicius_haaland = [repo.get("players", pid) for pid in ["vinicius", "haaland"]]

    assert calculate_chemistry(haaland_mbappe)["role_overlap_penalty"] > 0
    assert calculate_chemistry(vinicius_haaland)["progression_synergy"] > 0.55
