from bucephalus.game.live_data.mock_provider import write_provider_health_report
from bucephalus.game.repository import GameRepository


if __name__ == "__main__":
    repo = GameRepository()
    repo.reset()
    print({"game_db": str(repo.path), "provider_health": write_provider_health_report()})
