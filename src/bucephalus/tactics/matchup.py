from __future__ import annotations

from bucephalus.tactics.explanations import tactical_bullets
from bucephalus.tactics.fatigue import evaluate_fatigue
from bucephalus.tactics.pressure import evaluate_pressure
from bucephalus.tactics.schemas import MatchupReport, TacticalState
from bucephalus.tactics.transitions import evaluate_low_block, evaluate_possession, evaluate_transition


def evaluate_matchup(home: TacticalState, away: TacticalState) -> MatchupReport:
    hp, ap = evaluate_pressure(home, away), evaluate_pressure(away, home)
    hf, af = evaluate_fatigue(home), evaluate_fatigue(away)
    ht, at = evaluate_transition(home, away), evaluate_transition(away, home)
    hpos, apos = evaluate_possession(home), evaluate_possession(away)
    hblock, ablock = evaluate_low_block(home, away), evaluate_low_block(away, home)

    home_attack = _mod(0.12 * hp["shot_creation_boost"] + 0.12 * ht["attacking_transition_boost"] + 0.08 * hpos["chance_creation_stability"] - 0.10 * ablock["space_behind_reduction"])
    away_attack = _mod(0.12 * ap["shot_creation_boost"] + 0.12 * at["attacking_transition_boost"] + 0.08 * apos["chance_creation_stability"] - 0.10 * hblock["space_behind_reduction"])
    home_def = _mod(0.10 * home.defensive_compactness - 0.12 * ht["defensive_transition_risk"] - 0.08 * hp["transition_exposure_cost"])
    away_def = _mod(0.10 * away.defensive_compactness - 0.12 * at["defensive_transition_risk"] - 0.08 * ap["transition_exposure_cost"])
    key_advantages, key_risks = [], []
    if hp["opponent_build_up_disruption"] > ap["opponent_build_up_disruption"]:
        key_advantages.append("home_pressing_disruption_proxy")
    else:
        key_advantages.append("away_pressing_disruption_proxy")
    if ht["defensive_transition_risk"] > 0.55:
        key_risks.append("home_high_line_transition_risk_proxy")
    if at["defensive_transition_risk"] > 0.55:
        key_risks.append("away_high_line_transition_risk_proxy")

    return MatchupReport(
        home_attack_modifier=home_attack,
        away_attack_modifier=away_attack,
        home_defense_modifier=home_def,
        away_defense_modifier=away_def,
        home_xg_modifier=_clamp(home_attack - (away_def - 1)),
        away_xg_modifier=_clamp(away_attack - (home_def - 1)),
        home_fatigue_modifier=hf["second_half_performance_modifier"],
        away_fatigue_modifier=af["second_half_performance_modifier"],
        home_transition_risk=ht["defensive_transition_risk"],
        away_transition_risk=at["defensive_transition_risk"],
        home_late_goal_risk=hf["after_70_defensive_risk"],
        away_late_goal_risk=af["after_70_defensive_risk"],
        key_advantages=key_advantages,
        key_risks=key_risks,
        explanation_bullets=tactical_bullets(home, away, hf, af),
    )


def _mod(value: float) -> float:
    return max(0.65, min(1.35, 1 + value))


def _clamp(value: float) -> float:
    return max(0.65, min(1.35, value))
