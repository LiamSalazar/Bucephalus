from __future__ import annotations

import pytest

from bucephalus.game.services import TransferMarketService

from tests.game_helpers import seed_game


def test_market_respects_budget_and_uniqueness(tmp_path):
    repo, _, club_a, _ = seed_game(tmp_path)
    market = TransferMarketService(repo)

    with pytest.raises(ValueError):
        market.sign_player(club_a["id"], "haaland", amount=1_000_000)
    with pytest.raises(ValueError):
        market.sign_player(club_a["id"], "lautaro", amount=999_000_000)
