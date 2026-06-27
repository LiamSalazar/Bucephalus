from __future__ import annotations

from pydantic import BaseModel, Field


class TacticalState(BaseModel):
    team_id: str | None = None
    team_name: str = "unknown"
    possession: float = Field(ge=0, le=1)
    pressing: float = Field(ge=0, le=1)
    directness: float = Field(ge=0, le=1)
    transition: float = Field(ge=0, le=1)
    width: float = Field(ge=0, le=1)
    centrality: float = Field(ge=0, le=1)
    set_piece_dependency: float = Field(ge=0, le=1)
    defensive_exposure: float = Field(ge=0, le=1)
    second_half_intensity: float = Field(ge=0, le=1)
    late_goal_threat: float = Field(ge=0, le=1)
    fatigue_resistance: float = Field(ge=0, le=1)
    defensive_compactness: float = Field(ge=0, le=1)
    line_height: float = Field(ge=0, le=1)
    tempo: float = Field(ge=0, le=1)
    risk_tolerance: float = Field(ge=0, le=1)
    reliability_score: float = Field(default=0.0, ge=0, le=1)

    @classmethod
    def from_team_baseline(cls, row: dict) -> "TacticalState":
        possession = _clamp(row.get("possession_baseline"))
        pressing = _clamp(row.get("pressing_baseline"))
        directness = _clamp(row.get("directness_baseline"), midpoint=0.5)
        transition = _clamp(row.get("transition_baseline"))
        width = _clamp(row.get("width_baseline"))
        centrality = _clamp(row.get("centrality_baseline"))
        exposure = _clamp(row.get("defensive_exposure_baseline"))
        second_half = _clamp(row.get("second_half_intensity_baseline"))
        late_for = _clamp(row.get("late_goal_for_baseline"))
        return cls(
            team_id=row.get("bucephalus_team_id"),
            team_name=row.get("team_name") or "unknown",
            possession=possession,
            pressing=pressing,
            directness=directness,
            transition=transition,
            width=width,
            centrality=centrality,
            set_piece_dependency=_clamp(row.get("set_piece_dependency_baseline")),
            defensive_exposure=exposure,
            second_half_intensity=second_half,
            late_goal_threat=late_for,
            fatigue_resistance=_clamp((second_half + (1 - exposure)) / 2),
            defensive_compactness=_clamp(1 - exposure),
            line_height=_clamp((pressing + possession) / 2),
            tempo=_clamp((directness + pressing + transition) / 3),
            risk_tolerance=_clamp((transition + exposure + directness) / 3),
            reliability_score=_clamp(row.get("reliability_score")),
        )


class TacticalAdjustmentReport(BaseModel):
    warnings: list[str]
    applied_deltas: dict[str, float]
    before: TacticalState
    after: TacticalState


class MatchupReport(BaseModel):
    home_attack_modifier: float
    away_attack_modifier: float
    home_defense_modifier: float
    away_defense_modifier: float
    home_xg_modifier: float
    away_xg_modifier: float
    home_fatigue_modifier: float
    away_fatigue_modifier: float
    home_transition_risk: float
    away_transition_risk: float
    home_late_goal_risk: float
    away_late_goal_risk: float
    key_advantages: list[str]
    key_risks: list[str]
    explanation_bullets: list[str]


def _clamp(value, midpoint: float = 0.0) -> float:
    if value is None:
        value = midpoint
    return max(0.0, min(1.0, float(value)))
