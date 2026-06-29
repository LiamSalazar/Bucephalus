from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    admin_global = "admin_global"
    league_creator = "league_creator"
    manager = "manager"
    analyst = "analyst"
    viewer = "viewer"
    data_operator = "data_operator"


class LeagueType(StrEnum):
    live_tournament = "live_tournament"
    simulation_league = "simulation_league"
    hybrid_league = "hybrid_league"
    sandbox_league = "sandbox_league"
    research_league = "research_league"


class ResolutionMode(StrEnum):
    live = "live"
    simulated = "simulated"
    hybrid = "hybrid"
    manual = "manual"


class PlayerStatus(StrEnum):
    active_real_tournament = "active_real_tournament"
    eliminated = "eliminated"
    injured = "injured"
    suspended = "suspended"
    not_called = "not_called"
    transferred_out = "transferred_out"
    simulated_degraded = "simulated_degraded"
    manual_disabled = "manual_disabled"


class User(BaseModel):
    id: str
    name: str
    roles: list[Role] = Field(default_factory=lambda: [Role.manager])


class LeagueSettings(BaseModel):
    initial_budget: float = 300_000_000
    squad_size_min: int = 11
    squad_size_max: int = 25
    max_players_per_real_team: int = 4
    formation_rules: list[str] = Field(default_factory=lambda: ["4-3-3", "4-2-3-1", "4-4-2", "3-5-2"])
    transfer_rules: dict = Field(default_factory=dict)
    eliminated_player_policy: str = "simulated_degraded"
    scoring_mode: str = "simulation_points"
    resolution_mode: ResolutionMode = ResolutionMode.simulated
    market_mode: str = "draft"
    season_reset_policy: str = "seasonal_redraft"
    keeper_rights_policy: str = "optional_discount"
    confidence_policy: str = "show_model_confidence"


class League(BaseModel):
    id: str
    name: str
    creator_user_id: str
    competition_type: LeagueType = LeagueType.simulation_league
    settings: LeagueSettings = Field(default_factory=LeagueSettings)


class Club(BaseModel):
    id: str
    league_id: str
    name: str
    manager_user_id: str
    budget: float = 300_000_000
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0


class Player(BaseModel):
    id: str
    name: str
    canonical_position: str
    real_team: str | None = None
    value: float = 10_000_000
    status: PlayerStatus = PlayerStatus.active_real_tournament
    attributes: dict[str, float] = Field(default_factory=dict)


class SquadPlayer(BaseModel):
    club_id: str
    player_id: str
    acquisition_value: float = 0
    acquired_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class LineupSlot(BaseModel):
    player_id: str
    role: str
    position: str


class Lineup(BaseModel):
    id: str
    club_id: str
    formation: str
    slots: list[LineupSlot]


class TacticalPlan(BaseModel):
    club_id: str
    manual_override: bool = False
    sliders: dict[str, float] = Field(default_factory=dict)


class TransferBid(BaseModel):
    id: str
    league_id: str
    club_id: str
    player_id: str
    amount: float
    status: str = "accepted"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Fixture(BaseModel):
    id: str
    league_id: str
    home_club_id: str
    away_club_id: str
    status: str = "scheduled"


class MatchResult(BaseModel):
    fixture_id: str
    home_score: int
    away_score: int
    report_path: str


class SimulationRun(BaseModel):
    id: str
    fixture_id: str | None = None
    payload: dict
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class AuditLog(BaseModel):
    id: str
    action: str
    payload: dict
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
