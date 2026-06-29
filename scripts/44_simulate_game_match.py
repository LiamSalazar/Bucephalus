from bucephalus.game.repository import GameRepository
from bucephalus.game.simulation_service import SimulationService


if __name__ == "__main__":
    repo = GameRepository()
    clubs = repo.list("clubs")[:2]
    league_id = clubs[0]["league_id"]
    service = SimulationService(repo)
    fixture = service.create_fixture(league_id, clubs[0]["id"], clubs[1]["id"])
    result = service.simulate_fixture(fixture["id"], n_simulations=500, seed=42)
    print({"fixture": fixture, "probabilities": result["win_draw_loss_probabilities"], "report": result["report_json"]})
