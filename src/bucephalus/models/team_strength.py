from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_team_strength_timeseries(paths: ProjectPaths) -> dict:
    paths.ensure()
    source_path = paths.features / "team_match_features.parquet"
    if not source_path.exists():
        return _write_empty(paths, "team_match_features.parquet missing")
    df = pl.read_parquet(source_path)
    sort_columns = [col for col in ["match_date", "statsbomb_match_id", "bucephalus_team_id"] if col in df.columns]
    df = df.sort(sort_columns)
    required = {"bucephalus_team_id", "team_name", "match_date", "goals_for", "goals_against"}
    missing = sorted(required - set(df.columns))
    if missing or df.is_empty():
        return _write_empty(paths, f"missing columns or rows: {missing}")

    states: dict[str, dict] = defaultdict(_initial_state)
    rows = []
    errors = []
    for row in df.to_dicts():
        team_id = str(row["bucephalus_team_id"])
        state = states[team_id]
        pred_gf = max(0.05, 1.15 + state["attack_strength"] - state["defense_strength"] * 0.15)
        pred_ga = max(0.05, 1.05 + state["defense_strength"] - state["attack_strength"] * 0.10)
        gf = float(row.get("goals_for") or 0.0)
        ga = float(row.get("goals_against") or 0.0)
        rows.append(
            {
                "bucephalus_team_id": row["bucephalus_team_id"],
                "team_name": row["team_name"],
                "match_date": row["match_date"],
                "pre_match_attack_strength": state["attack_strength"],
                "pre_match_defense_strength": state["defense_strength"],
                "pre_match_attack_uncertainty": state["attack_uncertainty"],
                "pre_match_defense_uncertainty": state["defense_uncertainty"],
                "predicted_goals_for": pred_gf,
                "predicted_goals_against": pred_ga,
                "goals_for": gf,
                "goals_against": ga,
                "matches_observed_before": state["matches_observed"],
            }
        )
        errors.append(abs(gf - pred_gf) + abs(ga - pred_ga))
        rate = 0.12 / (1 + 0.08 * state["matches_observed"])
        xg_for = row.get("xg_for")
        xg_against = row.get("xg_against")
        attack_obs = float(xg_for) if xg_for is not None else gf
        defense_obs = float(xg_against) if xg_against is not None else ga
        state["attack_strength"] += rate * (attack_obs - pred_gf)
        state["defense_strength"] += rate * (pred_ga - defense_obs)
        state["form_momentum"] = 0.75 * state["form_momentum"] + 0.25 * (gf - ga)
        state["matches_observed"] += 1
        state["attack_uncertainty"] = max(0.08, state["attack_uncertainty"] * 0.94)
        state["defense_uncertainty"] = max(0.08, state["defense_uncertainty"] * 0.94)
        state["last_updated"] = row["match_date"]

    output = pl.DataFrame(rows)
    output.write_parquet(paths.features / "team_strength_timeseries.parquet")
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model_type": "sequential_team_strength_v0",
        "rows": output.height,
        "teams": output["bucephalus_team_id"].n_unique(),
        "uses_future_data": False,
        "status": "candidate",
    }
    (paths.models_outputs / "team_strength_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    backtest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": output.height,
        "mean_absolute_goal_error_per_team_match": float(sum(errors) / max(1, len(errors))),
        "uses_pre_match_state": True,
    }
    (paths.evaluation_outputs / "team_strength_backtest.json").write_text(json.dumps(backtest, indent=2), encoding="utf-8")
    return backtest


def latest_team_strength(paths: ProjectPaths, team_id: str | None) -> dict | None:
    path = paths.features / "team_strength_timeseries.parquet"
    if not path.exists() or team_id is None:
        return None
    df = pl.read_parquet(path).filter(pl.col("bucephalus_team_id") == team_id).sort("match_date")
    if df.is_empty():
        return None
    return df.tail(1).to_dicts()[0]


def _initial_state() -> dict:
    return {
        "attack_strength": 0.0,
        "defense_strength": 0.0,
        "attack_uncertainty": 1.0,
        "defense_uncertainty": 1.0,
        "form_momentum": 0.0,
        "last_updated": None,
        "matches_observed": 0,
    }


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    schema = {
        "bucephalus_team_id": pl.Utf8,
        "team_name": pl.Utf8,
        "match_date": pl.Utf8,
        "pre_match_attack_strength": pl.Float64,
        "pre_match_defense_strength": pl.Float64,
        "pre_match_attack_uncertainty": pl.Float64,
        "pre_match_defense_uncertainty": pl.Float64,
        "predicted_goals_for": pl.Float64,
        "predicted_goals_against": pl.Float64,
        "goals_for": pl.Float64,
        "goals_against": pl.Float64,
        "matches_observed_before": pl.Int64,
    }
    pl.DataFrame(schema=schema).write_parquet(paths.features / "team_strength_timeseries.parquet")
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "skipped", "reason": reason}
    (paths.models_outputs / "team_strength_registry.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "team_strength_backtest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
