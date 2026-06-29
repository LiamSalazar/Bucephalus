from __future__ import annotations

from uuid import uuid4

from bucephalus.game.models import Club, League, LeagueSettings, LeagueType, Player, SquadPlayer, TransferBid, User
from bucephalus.game.repository import GameRepository


class LeagueService:
    def __init__(self, repo: GameRepository) -> None:
        self.repo = repo

    def create_user(self, name: str, roles: list[str] | None = None) -> dict:
        user = User(id=str(uuid4()), name=name, roles=roles or ["manager"])
        payload = self.repo.add("users", user)
        self.repo.audit("create_user", payload)
        return payload

    def create_league(self, name: str, creator_user_id: str, league_type: str = "simulation_league") -> dict:
        league = League(id=str(uuid4()), name=name, creator_user_id=creator_user_id, competition_type=LeagueType(league_type), settings=LeagueSettings())
        payload = self.repo.add("leagues", league)
        self.repo.audit("create_league", payload)
        return payload

    def create_club(self, league_id: str, name: str, manager_user_id: str) -> dict:
        league = self.repo.get("leagues", league_id)
        budget = (league or {}).get("settings", {}).get("initial_budget", 300_000_000)
        club = Club(id=str(uuid4()), league_id=league_id, name=name, manager_user_id=manager_user_id, budget=budget)
        payload = self.repo.add("clubs", club)
        self.repo.audit("create_club", payload)
        return payload


class PlayerPoolService:
    def __init__(self, repo: GameRepository) -> None:
        self.repo = repo

    def load_default_pool(self) -> list[dict]:
        players = [
            Player(id="haaland", name="Erling Haaland", canonical_position="CF", value=120_000_000, attributes={"finishing": 0.98, "pressing": 0.48, "pace": 0.78, "association": 0.55, "aerial": 0.95}),
            Player(id="mbappe", name="Kylian Mbappe", canonical_position="LW", value=130_000_000, attributes={"finishing": 0.92, "pressing": 0.50, "pace": 0.98, "association": 0.66, "transition": 0.96}),
            Player(id="vinicius", name="Vinicius Junior", canonical_position="LW", value=110_000_000, attributes={"dribbling": 0.96, "creation": 0.86, "pressing": 0.62, "pace": 0.96, "association": 0.74}),
            Player(id="rodri", name="Rodri", canonical_position="DM", value=105_000_000, attributes={"control": 0.97, "press_resistance": 0.96, "defense": 0.88, "compactness": 0.92, "fatigue": 0.88}),
            Player(id="valverde", name="Federico Valverde", canonical_position="CM", value=95_000_000, attributes={"pressing": 0.90, "transition": 0.84, "coverage": 0.92, "fatigue": 0.94, "progression": 0.82}),
            Player(id="bellingham", name="Jude Bellingham", canonical_position="AM", value=115_000_000, attributes={"box_arrival": 0.90, "control": 0.82, "pressing": 0.78, "association": 0.80, "transition": 0.80}),
            Player(id="pedri", name="Pedri", canonical_position="CM", value=90_000_000, attributes={"control": 0.94, "association": 0.92, "press_resistance": 0.90, "progression": 0.82}),
            Player(id="vitinha", name="Vitinha", canonical_position="CM", value=80_000_000, attributes={"control": 0.91, "association": 0.90, "press_resistance": 0.88, "centrality": 0.88}),
            Player(id="dias", name="Ruben Dias", canonical_position="CB", value=75_000_000, attributes={"defense": 0.92, "compactness": 0.90, "aerial": 0.86}),
            Player(id="courtois", name="Thibaut Courtois", canonical_position="GK", value=55_000_000, attributes={"goalkeeping": 0.94, "aerial": 0.82}),
            Player(id="carvajal", name="Dani Carvajal", canonical_position="RB", value=35_000_000, attributes={"defense": 0.78, "width": 0.78, "pressing": 0.74}),
            Player(id="grimaldo", name="Alex Grimaldo", canonical_position="LB", value=45_000_000, attributes={"width": 0.88, "creation": 0.80, "progression": 0.82}),
            Player(id="alisson", name="Alisson Becker", canonical_position="GK", value=50_000_000, attributes={"goalkeeping": 0.92}),
            Player(id="saliba", name="William Saliba", canonical_position="CB", value=70_000_000, attributes={"defense": 0.88, "compactness": 0.84}),
            Player(id="ake", name="Nathan Ake", canonical_position="CB", value=42_000_000, attributes={"defense": 0.80, "compactness": 0.82}),
            Player(id="hakimi", name="Achraf Hakimi", canonical_position="RB", value=65_000_000, attributes={"width": 0.90, "pace": 0.90, "transition": 0.82}),
            Player(id="camavinga", name="Eduardo Camavinga", canonical_position="DM", value=70_000_000, attributes={"pressing": 0.82, "coverage": 0.86, "progression": 0.80}),
            Player(id="odegaard", name="Martin Odegaard", canonical_position="AM", value=85_000_000, attributes={"creation": 0.88, "association": 0.86, "control": 0.84}),
            Player(id="saka", name="Bukayo Saka", canonical_position="RW", value=105_000_000, attributes={"creation": 0.84, "pressing": 0.72, "width": 0.84}),
            Player(id="kane", name="Harry Kane", canonical_position="ST", value=95_000_000, attributes={"finishing": 0.92, "association": 0.82, "creation": 0.74}),
            Player(id="tchouameni", name="Aurelien Tchouameni", canonical_position="DM", value=75_000_000, attributes={"defense": 0.84, "coverage": 0.84, "compactness": 0.82}),
            Player(id="gvardiol", name="Josko Gvardiol", canonical_position="LB", value=80_000_000, attributes={"defense": 0.84, "width": 0.76, "progression": 0.76}),
            Player(id="lautaro", name="Lautaro Martinez", canonical_position="ST", value=90_000_000, attributes={"finishing": 0.88, "pressing": 0.78, "association": 0.72}),
        ]
        existing = {row["id"] for row in self.repo.list("players")}
        for player in players:
            if player.id not in existing:
                self.repo.add("players", player)
        self.repo.audit("load_default_player_pool", {"players": len(players)})
        return self.repo.list("players")


class TransferMarketService:
    def __init__(self, repo: GameRepository) -> None:
        self.repo = repo

    def sign_player(self, club_id: str, player_id: str, amount: float | None = None) -> dict:
        club = self.repo.get("clubs", club_id)
        player = self.repo.get("players", player_id)
        if club is None or player is None:
            raise ValueError("club or player not found")
        price = float(amount if amount is not None else player["value"])
        if club["budget"] < price:
            raise ValueError("insufficient budget")
        if any(row["player_id"] == player_id for row in self.repo.list("squad_players")):
            raise ValueError("player already assigned")
        club["budget"] -= price
        self.repo.replace("clubs", club_id, club)
        self.repo.add("squad_players", SquadPlayer(club_id=club_id, player_id=player_id, acquisition_value=price))
        bid = TransferBid(id=str(uuid4()), league_id=club["league_id"], club_id=club_id, player_id=player_id, amount=price)
        payload = self.repo.add("transfer_bids", bid)
        self.repo.audit("sign_player", payload)
        return payload

    def draft_players(self, club_id: str, player_ids: list[str]) -> list[dict]:
        signed = []
        for player_id in player_ids:
            signed.append(self.sign_player(club_id, player_id))
        return signed
