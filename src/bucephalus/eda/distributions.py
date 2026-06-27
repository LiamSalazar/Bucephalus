from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/bucephalus-matplotlib")

import matplotlib.pyplot as plt
import polars as pl

from bucephalus.config import settings
from bucephalus.eda.fat_tails import fat_tail_summary
from bucephalus.features.build_basic_features import build_player_match_basic, build_team_profiles_baseline
from bucephalus.utils.paths import ProjectPaths

LOGGER = logging.getLogger(__name__)


def run_eda(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    events = _read(paths.processed / "events.parquet")
    matches = _read(paths.processed / "matches.parquet")
    master_teams = _read(paths.processed / "master_teams.parquet")
    if events.is_empty() or matches.is_empty():
        LOGGER.warning("Missing processed events or matches; EDA skipped.")
        return
    events = _ensure_event_columns(events)
    team_match = team_match_summary(events, matches)
    player_match = build_player_match_basic(events)
    tables = {
        "event_type_counts": event_type_counts(events),
        "goals_by_match": goals_by_match(matches),
        "goals_by_team_match": goals_by_team_match(matches),
        "shots_distribution": _distribution(team_match, "shots"),
        "shots_on_target_distribution": _distribution(team_match, "shots_on_target"),
        "xg_distribution": _distribution(team_match, "xg"),
        "passes_distribution": _distribution(team_match, "passes"),
        "pressures_distribution": _distribution(team_match, "pressures"),
        "duels_distribution": _distribution(team_match, "duels"),
        "aerial_duels_distribution": _distribution(team_match, "aerial_duels"),
        "events_by_minute_interval": _minute_metric(events, "events"),
        "goals_by_minute_interval": _minute_metric(events, "goals"),
        "shots_by_minute_interval": _minute_metric(events, "shots"),
        "first_half_vs_second_half": first_half_vs_second_half(events),
        "events_after_70": events_after_70(events),
        "player_match_summary": player_match,
        "player_stability_candidates": player_stability(events),
        "position_summary": position_performance(events),
        "team_match_summary": team_match,
        "team_profiles_baseline": build_team_profiles_baseline(events, matches, master_teams),
    }
    tables["fat_tail_summary"] = fat_tail_summary(_metric_vectors(tables))
    for name, df in tables.items():
        _write_table(df, paths.eda_tables / f"{name}.parquet")
    _write_figures(tables, paths.eda_figures)
    LOGGER.info("EDA outputs written to %s.", paths.eda_outputs)


def goals_by_match(matches: pl.DataFrame) -> pl.DataFrame:
    return matches.select(
        "match_id",
        (pl.col("home_score") + pl.col("away_score")).alias("goals"),
        "home_score",
        "away_score",
    )


def goals_by_team_match(matches: pl.DataFrame) -> pl.DataFrame:
    home = matches.select(
        "match_id",
        pl.col("home_team_id").alias("team_id"),
        pl.col("home_team_name").alias("team_name"),
        pl.col("home_score").alias("goals"),
    )
    away = matches.select(
        "match_id",
        pl.col("away_team_id").alias("team_id"),
        pl.col("away_team_name").alias("team_name"),
        pl.col("away_score").alias("goals"),
    )
    return pl.concat([home, away], how="vertical_relaxed")


def event_type_counts(events: pl.DataFrame) -> pl.DataFrame:
    return events.group_by("event_type").agg(pl.len().alias("count")).sort("count", descending=True)


def team_match_summary(events: pl.DataFrame, matches: pl.DataFrame | None = None) -> pl.DataFrame:
    events = _ensure_event_columns(events)
    result = events.group_by(["match_id", "team_id", "team_name"]).agg(
        pl.len().alias("events"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome").is_in(["Goal", "Saved"]))).sum().alias(
            "shots_on_target"
        ),
        (pl.col("event_type") == "Pass").sum().alias("passes"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures"),
        (pl.col("event_type") == "Duel").sum().alias("duels"),
        pl.col("duel_type").str.contains("Aerial", literal=False).fill_null(False).sum().alias("aerial_duels"),
        (pl.col("event_type") == "Goal Keeper").sum().alias("goalkeeper_actions"),
        pl.col("shot_xg").sum().alias("xg"),
        ((pl.col("event_type") == "Shot") & (pl.col("minute") >= 70)).sum().alias("shots_after_70"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal") & (pl.col("minute") >= 70)).sum().alias(
            "goals_after_70"
        ),
    )
    if matches is None or matches.is_empty():
        return result
    return result.join(goals_by_team_match(matches), on=["match_id", "team_id", "team_name"], how="left")


def minute_intervals(events: pl.DataFrame) -> pl.DataFrame:
    return (
        _events_with_minute_bucket(events)
        .group_by("minute_interval")
        .agg(
            pl.len().alias("events"),
            ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal")).sum().alias("goals"),
            (pl.col("event_type") == "Shot").sum().alias("shots"),
            (pl.col("event_type") == "Pressure").sum().alias("pressures"),
        )
        .sort("minute_interval")
    )


def first_half_vs_second_half(events: pl.DataFrame) -> pl.DataFrame:
    return events.with_columns(
        pl.when(pl.col("period") == 1).then(pl.lit("first_half")).otherwise(pl.lit("second_half")).alias("half")
    ).group_by("half").agg(
        pl.len().alias("events"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal")).sum().alias("goals"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures"),
    )


def events_after_70(events: pl.DataFrame) -> pl.DataFrame:
    return events.filter(pl.col("minute") >= 70).group_by(["event_type"]).agg(pl.len().alias("count")).sort(
        "count", descending=True
    )


def position_performance(events: pl.DataFrame) -> pl.DataFrame:
    return events.drop_nulls("position_name").group_by("position_name").agg(
        pl.len().alias("events"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        pl.col("shot_xg").sum().alias("xg"),
        (pl.col("event_type") == "Pass").sum().alias("passes"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures"),
    )


def player_stability(events: pl.DataFrame) -> pl.DataFrame:
    pm = build_player_match_basic(events)
    if pm.is_empty():
        return pm
    return pm.group_by(["player_id", "player_name"]).agg(
        pl.col("match_id").n_unique().alias("matches_count"),
        pl.col("events").mean().alias("avg_events"),
        pl.col("events").std().alias("std_events"),
        pl.col("shots").mean().alias("avg_shots"),
        pl.col("xg").mean().alias("avg_xg"),
    ).filter(pl.col("matches_count") >= 1)


def _distribution(df: pl.DataFrame, column: str) -> pl.DataFrame:
    if df.is_empty() or column not in df.columns:
        return pl.DataFrame(schema={column: pl.Float64, "count": pl.Int64})
    return df.group_by(column).agg(pl.len().alias("count")).sort(column)


def _minute_metric(events: pl.DataFrame, metric: str) -> pl.DataFrame:
    buckets = minute_intervals(events)
    return buckets.select("minute_interval", metric) if metric in buckets.columns else pl.DataFrame()


def _events_with_minute_bucket(events: pl.DataFrame) -> pl.DataFrame:
    return events.with_columns(
        pl.when(pl.col("minute") <= 15)
        .then(pl.lit("00-15"))
        .when(pl.col("minute") <= 30)
        .then(pl.lit("16-30"))
        .when(pl.col("minute") <= 45)
        .then(pl.lit("31-45+"))
        .when(pl.col("minute") <= 60)
        .then(pl.lit("46-60"))
        .when(pl.col("minute") <= 75)
        .then(pl.lit("61-75"))
        .otherwise(pl.lit("76-90+"))
        .alias("minute_interval")
    )


def _metric_vectors(tables: dict[str, pl.DataFrame]) -> dict[str, list[float | None]]:
    team_match = tables["team_match_summary"]
    player_match = tables["player_match_summary"]
    metrics = {
        "goals_by_team_match": tables["goals_by_team_match"]["goals"].to_list(),
        "shots_by_team_match": team_match["shots"].to_list(),
        "shots_on_target_by_team_match": team_match["shots_on_target"].to_list(),
        "xg_by_team_match": team_match["xg"].to_list(),
        "passes_by_team_match": team_match["passes"].to_list(),
        "pressures_by_team_match": team_match["pressures"].to_list(),
        "duels_by_team_match": team_match["duels"].to_list(),
        "goalkeeper_actions_by_match": team_match["goalkeeper_actions"].to_list(),
    }
    if not player_match.is_empty():
        metrics["player_shots_by_match"] = player_match["shots"].to_list()
        metrics["player_xg_by_match"] = player_match["xg"].to_list()
    return metrics


def _write_figures(tables: dict[str, pl.DataFrame], figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("goals_by_match", "goals"),
        ("team_match_summary", "xg"),
        ("team_match_summary", "shots"),
        ("events_by_minute_interval", "events"),
        ("goals_by_minute_interval", "goals"),
    ]
    for table_name, column in specs:
        df = tables[table_name]
        if column not in df.columns or df.is_empty():
            continue
        values = [v for v in df[column].to_list() if v is not None]
        if not values:
            continue
        plt.figure(figsize=(7, 4))
        if "minute_interval" in df.columns:
            plt.bar(df["minute_interval"].to_list(), values)
        else:
            plt.hist(values, bins=min(12, max(3, len(set(values)))))
        plt.title(f"{column} distribution")
        plt.xlabel(column)
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(figure_dir / f"{table_name}_{column}.png")
        plt.close()

    fat = tables.get("fat_tail_summary", pl.DataFrame())
    if not fat.is_empty() and {"metric", "p95", "p50"}.issubset(fat.columns):
        plt.figure(figsize=(9, 4))
        labels = fat["metric"].to_list()
        ratios = [(p95 / p50 if p50 not in (None, 0) else 0) for p95, p50 in zip(fat["p95"], fat["p50"], strict=False)]
        plt.bar(labels, ratios)
        plt.xticks(rotation=45, ha="right")
        plt.title("p95 / p50 metric comparison")
        plt.tight_layout()
        plt.savefig(figure_dir / "fat_tail_metric_comparison.png")
        plt.close()


def _ensure_event_columns(events: pl.DataFrame) -> pl.DataFrame:
    defaults = {
        "event_type": pl.lit(None, dtype=pl.Utf8),
        "duel_type": pl.lit(None, dtype=pl.Utf8),
        "shot_xg": pl.lit(None, dtype=pl.Float64),
        "shot_outcome": pl.lit(None, dtype=pl.Utf8),
        "minute": pl.lit(None, dtype=pl.Int64),
        "period": pl.lit(None, dtype=pl.Int64),
        "position_name": pl.lit(None, dtype=pl.Utf8),
    }
    expressions = [expr.alias(column) for column, expr in defaults.items() if column not in events.columns]
    return events.with_columns(expressions) if expressions else events


def _read(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else pl.DataFrame()


def _write_table(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
