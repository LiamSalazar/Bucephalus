from __future__ import annotations

import csv
import json
import random
from datetime import UTC, datetime

import polars as pl

from bucephalus.simulation.markov_calibration import event_to_state
from bucephalus.simulation.markov_engine import simulate_possession
from bucephalus.tactics.schemas import TacticalState
from bucephalus.utils.paths import ProjectPaths


def validate_markov_matrix(matrix: pl.DataFrame) -> dict:
    row_sums = matrix.group_by("from_state").agg(pl.col("probability").sum().alias("row_sum"))
    rows_sum = bool(row_sums.select((pl.col("row_sum") - 1).abs().max()).item() < 1e-9)
    no_negative = bool(matrix.filter(pl.col("probability") < 0).is_empty())
    return {
        "rows_sum_to_one": rows_sum,
        "no_negative_probabilities": no_negative,
        "states_count": row_sums.height,
        "passed": rows_sum and no_negative,
    }


def validate_markov_against_events(paths: ProjectPaths, n_possessions: int = 500) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    matrix_path = paths.features / "markov_transition_matrix_global.parquet"
    if not events_path.exists() or not matrix_path.exists():
        return _write_empty(paths, "events or Markov matrix missing")
    events = pl.read_parquet(events_path)
    matrix = pl.read_parquet(matrix_path)
    matrix_check = validate_markov_matrix(matrix)
    real_states = events.with_columns(
        pl.struct(events.columns).map_elements(event_to_state, return_dtype=pl.Utf8).alias("state")
    )
    real_dist = real_states.group_by("state").agg(pl.len().alias("real_count"))
    state = TacticalState.from_team_baseline(
        {
            "team_name": "validation_state",
            "possession_baseline": 0.5,
            "pressing_baseline": 0.5,
            "directness_baseline": 0.5,
            "transition_baseline": 0.5,
            "width_baseline": 0.5,
            "centrality_baseline": 0.5,
            "defensive_exposure_baseline": 0.4,
            "second_half_intensity_baseline": 0.5,
            "late_goal_for_baseline": 0.3,
            "reliability_score": 0.7,
        }
    )
    rng = random.Random(42)
    sim_states = []
    shots = goals = turnovers = lengths = 0
    for _ in range(n_possessions):
        possession = simulate_possession(state, state, rng)
        sim_states.extend(possession["sequence"])
        shots += int(possession["shot_generated"])
        goals += int(possession["goal_generated"])
        turnovers += int(possession["turnover_generated"])
        lengths += len(possession["sequence"])
    sim_dist = pl.DataFrame({"state": sim_states}).group_by("state").agg(pl.len().alias("sim_count"))
    comparison = real_dist.join(sim_dist, on="state", how="outer", coalesce=True).fill_null(0).with_columns(
        (pl.col("real_count") / pl.col("real_count").sum()).alias("real_share"),
        (pl.col("sim_count") / pl.col("sim_count").sum()).alias("sim_share"),
    )
    comparison.write_csv(paths.evaluation_outputs / "markov_state_distribution_comparison.csv")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": matrix_check["passed"],
        "matrix": matrix_check,
        "real_events": events.height,
        "simulated_possessions": n_possessions,
        "shots_per_possession_simulated": shots / max(1, n_possessions),
        "goals_per_shot_simulated": goals / max(1, shots),
        "turnovers_per_possession_simulated": turnovers / max(1, n_possessions),
        "mean_possession_length_simulated": lengths / max(1, n_possessions),
    }
    (paths.evaluation_outputs / "markov_validation_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    payload = {"generated_at": datetime.now(UTC).isoformat(), "passed": False, "reason": reason}
    (paths.evaluation_outputs / "markov_validation_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (paths.evaluation_outputs / "markov_state_distribution_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["state", "real_count", "sim_count"])
        writer.writeheader()
    return payload
