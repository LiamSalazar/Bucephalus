from __future__ import annotations

from tests.test_tactical_sliders import _state
from bucephalus.tactics.fatigue import evaluate_fatigue
from bucephalus.tactics.pressure import evaluate_pressure


def test_high_pressure_increases_benefits_and_costs() -> None:
    base = _state()
    high = base.model_copy(update={"pressing": 0.9, "tempo": 0.8, "fatigue_resistance": 0.2})
    low = base.model_copy(update={"pressing": 0.2})
    hp = evaluate_pressure(high, base)
    lp = evaluate_pressure(low, base)
    assert hp["high_recovery_boost"] > lp["high_recovery_boost"]
    assert hp["fatigue_cost"] > lp["fatigue_cost"]
    assert evaluate_fatigue(high)["after_70_defensive_risk"] > evaluate_fatigue(low)["after_70_defensive_risk"]


def test_press_resistant_opponent_dampens_benefit() -> None:
    team = _state().model_copy(update={"pressing": 0.8})
    resistant = _state().model_copy(update={"possession": 0.9, "directness": 0.1, "centrality": 0.9})
    weak = _state().model_copy(update={"possession": 0.2, "directness": 0.9, "centrality": 0.2})
    assert evaluate_pressure(team, resistant)["high_recovery_boost"] < evaluate_pressure(team, weak)["high_recovery_boost"]
