from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/bucephalus-matplotlib")

import matplotlib.pyplot as plt
import polars as pl

from bucephalus.config import settings
from bucephalus.eda.fat_tails import fat_tail_summary
from bucephalus.features.build_basic_features import build_team_profiles
from bucephalus.utils.paths import ProjectPaths

LOGGER = logging.getLogger(__name__)


def run_eda(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    events = _read(paths.processed / "events.parquet")
    matches = _read(paths.processed / "matches.parquet")
    lineups = _read(paths.processed / "lineups.parquet")
    if events.is_empty() or matches.is_empty():
        LOGGER.warning("Missing processed events or matches; EDA skipped.")
        return

    tables = {
        "goals_by_match": goals_by_match(matches),
        "goals_by_team_match": goals_by_team_match(matches),
        "event_type_counts": event_type_counts(events),
        "team_match_counts": team_match_counts(events),
        "minute_intervals": minute_intervals(events),
        "position_performance": position_performance(events),
        "player_stability": player_stability(events),
        "team_profiles": build_team_profiles(events, matches),
    }
    for name, df in tables.items():
        _write_table(df, paths.eda_tables / f"{name}.parquet")

    metrics = _metric_vectors(tables, events)
    _write_table(fat_tail_summary(metrics), paths.eda_tables / "fat_tail_summary.parquet")
    _write_figures(tables, paths.eda_figures)
    LOGGER.info("EDA outputs written to %s.", paths.eda_outputs)
    if lineups.is_empty():
        LOGGER.info("Lineups unavailable; position analyses use event position fields only.")


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


def team_match_counts(events: pl.DataFrame) -> pl.DataFrame:
    return events.group_by(["match_id", "team_id", "team_name"]).agg(
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


def minute_intervals(events: pl.DataFrame, interval: int = 15) -> pl.DataFrame:
    return (
        events.with_columns(((pl.col("minute") // interval) * interval).alias("minute_bucket"))
        .group_by("minute_bucket")
        .agg(
            pl.len().alias("events"),
            ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal")).sum().alias("goals"),
            (pl.col("event_type") == "Shot").sum().alias("shots"),
            (pl.col("event_type") == "Pressure").sum().alias("pressures"),
            (pl.col("period") == 1).sum().alias("first_half_events"),
            (pl.col("period") == 2).sum().alias("second_half_events"),
        )
        .sort("minute_bucket")
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
    pm = events.drop_nulls("player_id").group_by(["player_id", "player_name", "match_id"]).agg(
        pl.len().alias("events"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        pl.col("shot_xg").sum().alias("xg"),
    )
    return pm.group_by(["player_id", "player_name"]).agg(
        pl.col("match_id").n_unique().alias("matches_count"),
        pl.col("events").mean().alias("avg_events"),
        pl.col("events").std().alias("std_events"),
        pl.col("shots").mean().alias("avg_shots"),
        pl.col("xg").mean().alias("avg_xg"),
    )


def _metric_vectors(tables: dict[str, pl.DataFrame], events: pl.DataFrame) -> dict[str, list[float]]:
    team_match = tables["team_match_counts"]
    metrics = {
        "goals_by_match": tables["goals_by_match"]["goals"].to_list(),
        "goals_by_team_match": tables["goals_by_team_match"]["goals"].to_list(),
        "shots_by_team_match": team_match["shots"].to_list(),
        "shots_on_target_by_team_match": team_match["shots_on_target"].to_list(),
        "passes_by_team_match": team_match["passes"].to_list(),
        "pressures_by_team_match": team_match["pressures"].to_list(),
        "duels_by_team_match": team_match["duels"].to_list(),
        "xg_by_team_match": team_match["xg"].to_list(),
    }
    if "shot_xg" in events.columns:
        metrics["xg_per_shot"] = events.filter(pl.col("shot_xg").is_not_null())["shot_xg"].to_list()
    return metrics


def _write_figures(tables: dict[str, pl.DataFrame], figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    for table_name, column in [
        ("goals_by_match", "goals"),
        ("goals_by_team_match", "goals"),
        ("team_match_counts", "shots"),
        ("team_match_counts", "passes"),
        ("team_match_counts", "pressures"),
    ]:
        df = tables[table_name]
        if column not in df.columns or df.is_empty():
            continue
        values = [v for v in df[column].to_list() if v is not None]
        if not values:
            continue
        plt.figure(figsize=(7, 4))
        plt.hist(values, bins=min(12, max(3, len(set(values)))))
        plt.title(f"{column} distribution")
        plt.xlabel(column)
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(figure_dir / f"{table_name}_{column}.png")
        plt.close()


def _read(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else pl.DataFrame()


def _write_table(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
