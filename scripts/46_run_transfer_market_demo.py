from bucephalus.game.repository import GameRepository
from bucephalus.game.services import TransferMarketService


if __name__ == "__main__":
    repo = GameRepository()
    club = repo.list("clubs")[0]
    market = TransferMarketService(repo)
    # Demonstrates rejected bid by budget/duplicate constraints without mutating valid squads.
    try:
        market.sign_player(club["id"], "haaland", amount=999_000_000)
        result = "unexpected_success"
    except ValueError as exc:
        result = f"rejected: {exc}"
    print({"transfer_demo": result, "transactions": len(repo.list("transfer_bids"))})
