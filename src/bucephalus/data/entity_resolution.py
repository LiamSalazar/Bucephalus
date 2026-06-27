from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.'-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stable_entity_id(prefix: str, *parts: object) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def build_master_entities(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    players = _read(paths.processed / "players.parquet")
    teams = _read(paths.processed / "teams.parquet")
    competitions = _read(paths.processed / "competitions.parquet")
    matches = _read(paths.processed / "matches.parquet")

    _master_players(players).write_parquet(paths.processed / "master_players.parquet")
    _master_teams(teams).write_parquet(paths.processed / "master_teams.parquet")
    _master_competitions(competitions).write_parquet(paths.processed / "master_competitions.parquet")
    _master_matches(matches).write_parquet(paths.processed / "master_matches.parquet")


def _master_players(players: pl.DataFrame) -> pl.DataFrame:
    if players.is_empty():
        return pl.DataFrame(
            schema={
                "bucephalus_player_id": pl.Utf8,
                "statsbomb_player_id": pl.Int64,
                "canonical_name": pl.Utf8,
                "normalized_name": pl.Utf8,
                "aliases_json": pl.Utf8,
                "current_team_ids_json": pl.Utf8,
                "country_name": pl.Utf8,
                "positions_json": pl.Utf8,
                "future_role_eligibility_basis": pl.Utf8,
            }
        )
    grouped = (
        players.with_columns(
            pl.col("player_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_name")
        )
        .group_by("player_id")
        .agg(
            pl.col("player_name").drop_nulls().first().alias("canonical_name"),
            pl.col("normalized_name").drop_nulls().first(),
            pl.col("player_name").drop_nulls().unique().alias("aliases"),
            pl.col("team_id").drop_nulls().unique().alias("team_ids"),
            pl.col("country_name").drop_nulls().first(),
            pl.col("position_names").drop_nulls().unique().alias("positions"),
        )
    )
    return grouped.select(
        pl.struct(["player_id", "canonical_name"]).map_elements(
            lambda r: stable_entity_id("ply", r["player_id"], normalize_name(r["canonical_name"])),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_player_id"),
        pl.col("player_id").alias("statsbomb_player_id"),
        "canonical_name",
        "normalized_name",
        pl.col("aliases").map_elements(_json_list, return_dtype=pl.Utf8).alias("aliases_json"),
        pl.col("team_ids").map_elements(_json_list, return_dtype=pl.Utf8).alias("current_team_ids_json"),
        "country_name",
        pl.col("positions").map_elements(_json_list, return_dtype=pl.Utf8).alias("positions_json"),
        pl.lit(
            "future_attributes_plus_tactical_compatibility_not_nominal_position_only"
        ).alias("future_role_eligibility_basis"),
    )


def _master_teams(teams: pl.DataFrame) -> pl.DataFrame:
    if teams.is_empty():
        return pl.DataFrame(schema={})
    grouped = (
        teams.with_columns(pl.col("team_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_name"))
        .group_by("team_id")
        .agg(
            pl.col("team_name").drop_nulls().first().alias("canonical_name"),
            pl.col("normalized_name").drop_nulls().first(),
            pl.col("team_name").drop_nulls().unique().alias("aliases"),
            pl.col("competition_id").drop_nulls().unique().alias("competition_ids"),
        )
    )
    return grouped.select(
        pl.struct(["team_id", "canonical_name"]).map_elements(
            lambda r: stable_entity_id("team", r["team_id"], normalize_name(r["canonical_name"])),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_team_id"),
        pl.col("team_id").alias("statsbomb_team_id"),
        "canonical_name",
        "normalized_name",
        pl.lit(None, dtype=pl.Utf8).alias("country_name"),
        pl.col("aliases").map_elements(_json_list, return_dtype=pl.Utf8).alias("aliases_json"),
        pl.col("competition_ids").map_elements(_json_list, return_dtype=pl.Utf8).alias("competition_ids_json"),
    )


def _master_competitions(competitions: pl.DataFrame) -> pl.DataFrame:
    if competitions.is_empty():
        return pl.DataFrame(schema={})
    return competitions.unique(["competition_id", "season_id"]).select(
        pl.struct(["competition_id", "season_id"]).map_elements(
            lambda r: stable_entity_id("comp", r["competition_id"], r["season_id"]),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_competition_id"),
        "competition_id",
        "season_id",
        "competition_name",
        "season_name",
        "country_name",
        pl.col("competition_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_name"),
    )


def _master_matches(matches: pl.DataFrame) -> pl.DataFrame:
    if matches.is_empty():
        return pl.DataFrame(schema={})
    return matches.select(
        pl.col("match_id").map_elements(lambda x: stable_entity_id("match", x), return_dtype=pl.Utf8).alias(
            "bucephalus_match_id"
        ),
        pl.col("match_id").alias("statsbomb_match_id"),
        "match_date",
        "competition_id",
        "season_id",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_score",
        "away_score",
        "stage_name",
    )


def _read(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else pl.DataFrame()


def _json_list(values: object) -> str:
    if values is None:
        return "[]"
    if isinstance(values, pl.Series):
        values = values.to_list()
    if not isinstance(values, list):
        values = [values]
    clean = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        clean.append(value)
    return json.dumps(clean, ensure_ascii=False)
