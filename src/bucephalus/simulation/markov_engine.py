from __future__ import annotations

import random

from bucephalus.simulation.markov_states import TERMINAL_STATES, MatchState
from bucephalus.tactics.schemas import TacticalState


def base_transition_matrix() -> dict[MatchState, dict[MatchState, float]]:
    matrix = {
        MatchState.OWN_THIRD: {MatchState.BUILD_UP: 0.55, MatchState.MIDDLE_THIRD: 0.18, MatchState.TURNOVER: 0.18, MatchState.SET_PIECE: 0.04, MatchState.END_POSSESSION: 0.05},
        MatchState.BUILD_UP: {MatchState.MIDDLE_THIRD: 0.45, MatchState.FINAL_THIRD: 0.18, MatchState.TURNOVER: 0.22, MatchState.SET_PIECE: 0.05, MatchState.END_POSSESSION: 0.10},
        MatchState.MIDDLE_THIRD: {MatchState.FINAL_THIRD: 0.38, MatchState.BOX: 0.12, MatchState.TURNOVER: 0.25, MatchState.SET_PIECE: 0.08, MatchState.END_POSSESSION: 0.17},
        MatchState.FINAL_THIRD: {MatchState.BOX: 0.30, MatchState.SHOT: 0.18, MatchState.TURNOVER: 0.26, MatchState.SET_PIECE: 0.12, MatchState.END_POSSESSION: 0.14},
        MatchState.BOX: {MatchState.SHOT: 0.38, MatchState.GOAL: 0.04, MatchState.TURNOVER: 0.30, MatchState.SET_PIECE: 0.10, MatchState.END_POSSESSION: 0.18},
        MatchState.SHOT: {MatchState.GOAL: 0.10, MatchState.SET_PIECE: 0.08, MatchState.END_POSSESSION: 0.82},
        MatchState.COUNTER_ATTACK: {MatchState.FINAL_THIRD: 0.35, MatchState.BOX: 0.20, MatchState.SHOT: 0.16, MatchState.TURNOVER: 0.20, MatchState.END_POSSESSION: 0.09},
        MatchState.SET_PIECE: {MatchState.SHOT: 0.18, MatchState.BOX: 0.15, MatchState.TURNOVER: 0.25, MatchState.END_POSSESSION: 0.42},
        MatchState.GOAL: {MatchState.GOAL: 1.0},
        MatchState.TURNOVER: {MatchState.TURNOVER: 1.0},
        MatchState.END_POSSESSION: {MatchState.END_POSSESSION: 1.0},
    }
    return {state: _normalize(row) for state, row in matrix.items()}


def adjusted_transition_matrix(
    team: TacticalState,
    opponent: TacticalState,
    base_matrix: dict[MatchState, dict[MatchState, float]] | None = None,
) -> dict[MatchState, dict[MatchState, float]]:
    matrix = {s: dict(row) for s, row in (base_matrix or base_transition_matrix()).items()}
    progression = 0.08 * team.directness + 0.06 * team.tempo + 0.05 * team.centrality
    press_disruption = 0.10 * opponent.pressing * (1 - team.possession)
    matrix[MatchState.BUILD_UP][MatchState.FINAL_THIRD] += progression
    matrix[MatchState.BUILD_UP][MatchState.TURNOVER] += press_disruption
    matrix[MatchState.MIDDLE_THIRD][MatchState.FINAL_THIRD] += progression
    matrix[MatchState.FINAL_THIRD][MatchState.SHOT] += 0.08 * team.risk_tolerance + 0.05 * team.centrality
    matrix[MatchState.BOX][MatchState.SHOT] += 0.08 * team.risk_tolerance
    matrix[MatchState.SHOT][MatchState.GOAL] += 0.04 * team.set_piece_dependency + 0.04 * team.late_goal_threat
    matrix[MatchState.TURNOVER] = {MatchState.TURNOVER: 1.0}
    return {state: _normalize(row) for state, row in matrix.items()}


def simulate_possession(
    team: TacticalState,
    opponent: TacticalState,
    rng: random.Random,
    max_steps: int = 12,
    base_matrix: dict[MatchState, dict[MatchState, float]] | None = None,
) -> dict:
    matrix = adjusted_transition_matrix(team, opponent, base_matrix=base_matrix)
    state = MatchState.OWN_THIRD
    sequence = [state.value]
    shot = goal = turnover = counter = False
    xg = 0.0
    for _ in range(max_steps):
        if state in TERMINAL_STATES:
            break
        state = _draw(matrix[state], rng)
        sequence.append(state.value)
        if state == MatchState.SHOT:
            shot = True
            xg += 0.05 + 0.12 * team.centrality + 0.08 * team.risk_tolerance
        elif state == MatchState.GOAL:
            goal = True
            xg += 0.25
        elif state == MatchState.TURNOVER:
            turnover = True
            counter = rng.random() < opponent.transition * (0.2 + team.line_height * 0.4)
    return {
        "sequence": sequence,
        "terminal_state": state.value,
        "shot_generated": shot,
        "goal_generated": goal,
        "xg_proxy": min(xg, 1.0),
        "turnover_generated": turnover,
        "counter_attack_allowed": counter,
    }


def validate_transition_matrix(matrix: dict[MatchState, dict[MatchState, float]]) -> bool:
    return all(abs(sum(row.values()) - 1.0) < 1e-9 for row in matrix.values())


def _draw(row: dict[MatchState, float], rng: random.Random) -> MatchState:
    threshold = rng.random()
    cumulative = 0.0
    for state, probability in row.items():
        cumulative += probability
        if threshold <= cumulative:
            return state
    return next(reversed(row))


def _normalize(row: dict[MatchState, float]) -> dict[MatchState, float]:
    clean = {k: max(0.0, v) for k, v in row.items()}
    total = sum(clean.values()) or 1.0
    return {k: v / total for k, v in clean.items()}
