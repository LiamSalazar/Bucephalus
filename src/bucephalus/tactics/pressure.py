from __future__ import annotations

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.tactics.schemas import TacticalState


def press_resistance_proxy(state: TacticalState) -> float:
    return _clamp((state.possession + (1 - state.directness) + state.centrality + state.second_half_intensity + state.reliability_score) / 5)


def evaluate_pressure(state: TacticalState, opponent: TacticalState) -> dict[str, float]:
    resistance = press_resistance_proxy(opponent)
    resistance_weight = float(get_parameter("pressure_effective_press_resistance_weight", 0.55))
    recovery_weight = float(get_parameter("pressure_recovery_weight", 0.45))
    fatigue_weight = float(get_parameter("fatigue_pressing_weight", 0.45))
    effective_press = state.pressing * (1 - resistance_weight * resistance)
    return {
        "opponent_press_resistance_proxy": resistance,
        "high_recovery_boost": _clamp(recovery_weight * effective_press),
        "territorial_control_boost": _clamp(0.30 * effective_press + 0.15 * state.line_height),
        "shot_creation_boost": _clamp(0.25 * effective_press + 0.10 * state.tempo),
        "opponent_build_up_disruption": _clamp(0.50 * effective_press),
        "fatigue_cost": _clamp(fatigue_weight * state.pressing + 0.25 * state.tempo + 0.20 * state.line_height),
        "transition_exposure_cost": _clamp(0.35 * state.pressing + 0.35 * state.line_height + 0.30 * opponent.transition),
        "card_risk_proxy": _clamp(0.25 * state.pressing + 0.20 * state.risk_tolerance),
        "second_half_drop_risk": _clamp((state.pressing + state.tempo + state.line_height) / 3 * (1 - state.fatigue_resistance)),
    }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
