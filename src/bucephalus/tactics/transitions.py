from __future__ import annotations

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.tactics.schemas import TacticalState


def evaluate_transition(state: TacticalState, opponent: TacticalState) -> dict[str, float]:
    directness_weight = float(get_parameter("transition_directness_weight", 0.25))
    return {
        "attacking_transition_boost": _clamp(0.45 * state.transition + directness_weight * state.directness + 0.15 * opponent.defensive_exposure),
        "defensive_transition_risk": _clamp(0.35 * state.line_height + 0.25 * state.risk_tolerance + 0.30 * opponent.transition - 0.25 * state.defensive_compactness),
        "counter_attack_threat": _clamp(0.45 * state.transition + 0.30 * state.directness + 0.10 * state.tempo),
        "vulnerability_to_direct_play": _clamp(0.35 * state.line_height + 0.30 * state.defensive_exposure + 0.25 * opponent.directness),
    }


def evaluate_possession(state: TacticalState) -> dict[str, float]:
    low_progression = state.possession * (1 - max(state.directness, state.centrality, state.transition))
    return {
        "control_boost": _clamp(0.45 * state.possession + 0.20 * state.centrality),
        "chance_creation_stability": _clamp(0.30 * state.possession + 0.25 * state.centrality + 0.15 * state.tempo),
        "tempo_suppression": _clamp(state.possession * (1 - state.tempo)),
        "vulnerability_if_low_progression": _clamp(low_progression),
    }


def evaluate_low_block(state: TacticalState, opponent: TacticalState) -> dict[str, float]:
    compact = state.defensive_compactness
    return {
        "space_behind_reduction": _clamp(0.50 * compact + 0.20 * (1 - state.line_height)),
        "shot_volume_conceded_risk": _clamp(0.35 * (1 - state.pressing) + 0.25 * opponent.possession),
        "counter_attack_boost": _clamp(0.35 * compact + 0.30 * state.transition + 0.20 * state.directness),
        "pressure_absorption_risk": _clamp(0.40 * opponent.pressing + 0.25 * opponent.tempo - 0.25 * state.second_half_intensity),
        "late_concession_risk": _clamp(0.35 * opponent.pressing + 0.30 * opponent.second_half_intensity - 0.25 * state.fatigue_resistance),
    }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
