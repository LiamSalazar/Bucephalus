from __future__ import annotations

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.tactics.schemas import TacticalState


def evaluate_fatigue(state: TacticalState) -> dict[str, float]:
    pressing_weight = float(get_parameter("fatigue_pressing_weight", 0.35))
    tempo_weight = float(get_parameter("fatigue_tempo_weight", 0.25))
    load = _clamp(pressing_weight * state.pressing + tempo_weight * state.tempo + 0.20 * state.line_height + 0.20 * state.risk_tolerance)
    sustainable = _clamp(0.6 * state.fatigue_resistance + 0.4 * state.second_half_intensity)
    second_half_modifier = _clamp(1 - 0.35 * max(0, load - sustainable))
    after_70_risk = _clamp(load * (1 - sustainable) + 0.15 * (1 - state.defensive_compactness))
    attacking_drop = _clamp(after_70_risk * (1 - 0.5 * state.late_goal_threat))
    return {
        "fatigue_load": load,
        "second_half_performance_modifier": second_half_modifier,
        "after_70_defensive_risk": after_70_risk,
        "after_70_attacking_drop": attacking_drop,
    }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
