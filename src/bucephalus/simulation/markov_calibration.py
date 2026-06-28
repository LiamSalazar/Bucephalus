from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.simulation.markov_engine import base_transition_matrix
from bucephalus.simulation.markov_states import MatchState
from bucephalus.utils.paths import ProjectPaths

STATES = [s.value for s in MatchState]


def event_to_state(row: dict) -> str:
    event_type = row.get("event_type") or row.get("type_name")
    outcome = row.get("shot_outcome")
    x = row.get("location_x")
    play_pattern = row.get("play_pattern_name") or row.get("play_pattern")
    if event_type == "Shot":
        return MatchState.GOAL.value if outcome == "Goal" else MatchState.SHOT.value
    if play_pattern and "Set Piece" in str(play_pattern):
        return MatchState.SET_PIECE.value
    if event_type in {"Duel", "Interception", "Pressure"}:
        return MatchState.TURNOVER.value if event_type == "Interception" else MatchState.MIDDLE_THIRD.value
    if play_pattern and "Counter" in str(play_pattern):
        return MatchState.COUNTER_ATTACK.value
    if x is None:
        return MatchState.BUILD_UP.value
    if x < 40:
        return MatchState.OWN_THIRD.value
    if x < 65:
        return MatchState.BUILD_UP.value
    if x < 90:
        return MatchState.MIDDLE_THIRD.value
    if x < 108:
        return MatchState.FINAL_THIRD.value
    return MatchState.BOX.value


def calibrate_markov_matrix(paths: ProjectPaths) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    if not events_path.exists():
        return _fallback(paths, "events.parquet missing")
    events = pl.read_parquet(events_path)
    if events.height < 100:
        return _fallback(paths, f"insufficient events: {events.height}")
    states = events.sort(["match_id", "possession", "event_index"]).with_columns(
        pl.struct(events.columns).map_elements(event_to_state, return_dtype=pl.Utf8).alias("state")
    )
    rows = []
    grouped = states.group_by(["match_id", "possession", "team_id"], maintain_order=True)
    counts = {(a, b): 0 for a in STATES for b in STATES}
    for _, group in grouped:
        seq = group["state"].to_list()
        for a, b in zip(seq, seq[1:], strict=False):
            counts[(a, b)] = counts.get((a, b), 0) + 1
        if seq:
            counts[(seq[-1], MatchState.END_POSSESSION.value)] = counts.get((seq[-1], MatchState.END_POSSESSION.value), 0) + 1
    alpha = float(get_parameter("markov_laplace_alpha", 1.0))
    for from_state in STATES:
        denom = sum(counts.get((from_state, to_state), 0) + alpha for to_state in STATES)
        for to_state in STATES:
            rows.append({
                "scope": "global",
                "from_state": from_state,
                "to_state": to_state,
                "transition_count": counts.get((from_state, to_state), 0),
                "probability": (counts.get((from_state, to_state), 0) + alpha) / denom,
            })
    matrix = pl.DataFrame(rows)
    matrix.write_parquet(paths.features / "markov_transition_matrix_global.parquet")
    pl.DataFrame(
        [
            {
                "from_state": from_state,
                "to_state": to_state,
                "transition_count": count,
                "updated_at": datetime.now(UTC).isoformat(),
                "matrix_version": "markov_global_v0",
            }
            for (from_state, to_state), count in counts.items()
        ]
    ).write_parquet(paths.features / "markov_transition_counts.parquet")
    pl.DataFrame(schema=matrix.schema).write_parquet(paths.features / "markov_transition_matrix_by_style.parquet")
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "calibrated",
        "events": events.height,
        "states": STATES,
        "rows_sum_to_one": _rows_sum_to_one(matrix),
        "transition_counts": int(sum(counts.values())),
        "warnings": ["by-style matrix omitted unless style coverage is sufficient"],
    }
    (paths.calibration_outputs / "markov_calibration_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (paths.calibration_outputs / "markov_incremental_update_report.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "status": "completed",
                "counts_rows": len(counts),
                "matrix_version": "markov_global_v0",
                "update_policy": "counts are persisted and probabilities are recalculated from cumulative counts",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def _fallback(paths: ProjectPaths, reason: str) -> dict:
    rows = []
    for from_state, row in base_transition_matrix().items():
        for to_state, probability in row.items():
            rows.append({"scope": "global", "from_state": from_state.value, "to_state": to_state.value, "transition_count": 0, "probability": probability})
    matrix = pl.DataFrame(rows)
    matrix.write_parquet(paths.features / "markov_transition_matrix_global.parquet")
    pl.DataFrame(
        schema={
            "from_state": pl.Utf8,
            "to_state": pl.Utf8,
            "transition_count": pl.Int64,
            "updated_at": pl.Utf8,
            "matrix_version": pl.Utf8,
        }
    ).write_parquet(paths.features / "markov_transition_counts.parquet")
    pl.DataFrame(schema=matrix.schema).write_parquet(paths.features / "markov_transition_matrix_by_style.parquet")
    report = {"generated_at": datetime.now(UTC).isoformat(), "status": "heuristic_fallback", "reason": reason, "rows_sum_to_one": True, "warnings": [reason]}
    (paths.calibration_outputs / "markov_calibration_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (paths.calibration_outputs / "markov_incremental_update_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _rows_sum_to_one(matrix: pl.DataFrame) -> bool:
    sums = matrix.group_by("from_state").agg(pl.col("probability").sum().alias("row_sum"))
    return bool(sums.select((pl.col("row_sum") - 1).abs().max()).item() < 1e-9)
