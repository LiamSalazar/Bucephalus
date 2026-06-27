from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths
from bucephalus.utils.text import normalize_text

ROLE_BASIS = "future tactical eligibility may use attributes, zones, roles and compatibility; not historical position only"


def normalize_name(value: str | None) -> str:
    return normalize_text(value)


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

    master_players = _master_players(players)
    master_teams = _master_teams(teams)
    master_competitions = _master_competitions(competitions)
    master_matches = _master_matches(matches)
    links = _external_links(master_players, master_teams, master_competitions, master_matches)
    report = _resolution_report(master_players, master_teams)

    master_players.write_parquet(paths.processed / "master_players.parquet")
    master_teams.write_parquet(paths.processed / "master_teams.parquet")
    master_competitions.write_parquet(paths.processed / "master_competitions.parquet")
    master_matches.write_parquet(paths.processed / "master_matches.parquet")
    links.write_parquet(paths.processed / "external_entity_links.parquet")
    (paths.processed / "entity_resolution_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _master_players(players: pl.DataFrame) -> pl.DataFrame:
    schema = {
        "bucephalus_player_id": pl.Utf8,
        "canonical_player_name": pl.Utf8,
        "normalized_player_name": pl.Utf8,
        "statsbomb_player_id": pl.Int64,
        "known_team_ids_json": pl.Utf8,
        "known_team_names_json": pl.Utf8,
        "known_position_names_json": pl.Utf8,
        "country_name": pl.Utf8,
        "aliases_json": pl.Utf8,
        "future_role_eligibility_basis": pl.Utf8,
    }
    if players.is_empty():
        return pl.DataFrame(schema=schema)
    grouped = (
        players.with_columns(
            pl.col("player_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_player_name")
        )
        .group_by("player_id")
        .agg(
            pl.col("player_name").drop_nulls().sort().first().alias("canonical_player_name"),
            pl.col("normalized_player_name").drop_nulls().sort().first(),
            pl.col("player_name").drop_nulls().unique().sort().alias("aliases"),
            pl.col("team_id").drop_nulls().unique().sort().alias("team_ids"),
            pl.col("team_name").drop_nulls().unique().sort().alias("team_names"),
            pl.col("country_name").drop_nulls().first(),
            pl.col("position_names").drop_nulls().unique().sort().alias("positions"),
        )
    )
    return grouped.select(
        pl.struct(["player_id", "canonical_player_name"]).map_elements(
            lambda r: stable_entity_id("ply", r["player_id"], normalize_name(r["canonical_player_name"])),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_player_id"),
        "canonical_player_name",
        "normalized_player_name",
        pl.col("player_id").alias("statsbomb_player_id"),
        pl.col("team_ids").map_elements(_json_list, return_dtype=pl.Utf8).alias("known_team_ids_json"),
        pl.col("team_names").map_elements(_json_list, return_dtype=pl.Utf8).alias("known_team_names_json"),
        pl.col("positions").map_elements(_json_list, return_dtype=pl.Utf8).alias("known_position_names_json"),
        "country_name",
        pl.col("aliases").map_elements(_json_list, return_dtype=pl.Utf8).alias("aliases_json"),
        pl.lit(ROLE_BASIS).alias("future_role_eligibility_basis"),
    ).sort("bucephalus_player_id")


def _master_teams(teams: pl.DataFrame) -> pl.DataFrame:
    schema = {
        "bucephalus_team_id": pl.Utf8,
        "canonical_team_name": pl.Utf8,
        "normalized_team_name": pl.Utf8,
        "statsbomb_team_id": pl.Int64,
        "country_name": pl.Utf8,
        "aliases_json": pl.Utf8,
        "competition_ids_json": pl.Utf8,
    }
    if teams.is_empty():
        return pl.DataFrame(schema=schema)
    grouped = (
        teams.with_columns(pl.col("team_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_team_name"))
        .group_by("team_id")
        .agg(
            pl.col("team_name").drop_nulls().sort().first().alias("canonical_team_name"),
            pl.col("normalized_team_name").drop_nulls().sort().first(),
            pl.col("team_name").drop_nulls().unique().sort().alias("aliases"),
            pl.col("competition_id").drop_nulls().unique().sort().alias("competition_ids"),
        )
    )
    return grouped.select(
        pl.struct(["team_id", "canonical_team_name"]).map_elements(
            lambda r: stable_entity_id("team", r["team_id"], normalize_name(r["canonical_team_name"])),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_team_id"),
        "canonical_team_name",
        "normalized_team_name",
        pl.col("team_id").alias("statsbomb_team_id"),
        pl.lit(None, dtype=pl.Utf8).alias("country_name"),
        pl.col("aliases").map_elements(_json_list, return_dtype=pl.Utf8).alias("aliases_json"),
        pl.col("competition_ids").map_elements(_json_list, return_dtype=pl.Utf8).alias("competition_ids_json"),
    ).sort("bucephalus_team_id")


def _master_competitions(competitions: pl.DataFrame) -> pl.DataFrame:
    schema = {
        "bucephalus_competition_id": pl.Utf8,
        "statsbomb_competition_id": pl.Int64,
        "statsbomb_season_id": pl.Int64,
        "competition_name": pl.Utf8,
        "season_name": pl.Utf8,
        "country_name": pl.Utf8,
        "normalized_competition_name": pl.Utf8,
    }
    if competitions.is_empty():
        return pl.DataFrame(schema=schema)
    return competitions.unique(["competition_id", "season_id"]).select(
        pl.struct(["competition_id", "season_id"]).map_elements(
            lambda r: stable_entity_id("comp", r["competition_id"], r["season_id"]),
            return_dtype=pl.Utf8,
        ).alias("bucephalus_competition_id"),
        pl.col("competition_id").alias("statsbomb_competition_id"),
        pl.col("season_id").alias("statsbomb_season_id"),
        "competition_name",
        "season_name",
        "country_name",
        pl.col("competition_name").map_elements(normalize_name, return_dtype=pl.Utf8).alias("normalized_competition_name"),
    ).sort("bucephalus_competition_id")


def _master_matches(matches: pl.DataFrame) -> pl.DataFrame:
    schema = {
        "bucephalus_match_id": pl.Utf8,
        "statsbomb_match_id": pl.Int64,
        "match_date": pl.Utf8,
        "competition_id": pl.Int64,
        "season_id": pl.Int64,
        "home_team_id": pl.Int64,
        "home_team_name": pl.Utf8,
        "away_team_id": pl.Int64,
        "away_team_name": pl.Utf8,
        "home_score": pl.Int64,
        "away_score": pl.Int64,
        "stage_name": pl.Utf8,
    }
    if matches.is_empty():
        return pl.DataFrame(schema=schema)
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
    ).sort("bucephalus_match_id")


def _external_links(
    players: pl.DataFrame, teams: pl.DataFrame, competitions: pl.DataFrame, matches: pl.DataFrame
) -> pl.DataFrame:
    frames = []
    if not players.is_empty():
        frames.append(
            players.select(
                pl.lit("player").alias("entity_type"),
                pl.col("bucephalus_player_id").alias("bucephalus_entity_id"),
                pl.lit("statsbomb").alias("provider"),
                pl.col("statsbomb_player_id").cast(pl.Utf8).alias("provider_entity_id"),
                pl.col("canonical_player_name").alias("provider_entity_name"),
                pl.lit(None, dtype=pl.Utf8).alias("provider_metadata_json"),
            )
        )
    if not teams.is_empty():
        frames.append(
            teams.select(
                pl.lit("team").alias("entity_type"),
                pl.col("bucephalus_team_id").alias("bucephalus_entity_id"),
                pl.lit("statsbomb").alias("provider"),
                pl.col("statsbomb_team_id").cast(pl.Utf8).alias("provider_entity_id"),
                pl.col("canonical_team_name").alias("provider_entity_name"),
                pl.lit(None, dtype=pl.Utf8).alias("provider_metadata_json"),
            )
        )
    if not competitions.is_empty():
        frames.append(
            competitions.select(
                pl.lit("competition").alias("entity_type"),
                pl.col("bucephalus_competition_id").alias("bucephalus_entity_id"),
                pl.lit("statsbomb").alias("provider"),
                pl.concat_str(["statsbomb_competition_id", "statsbomb_season_id"], separator=":").alias("provider_entity_id"),
                pl.concat_str(["competition_name", "season_name"], separator=" ").alias("provider_entity_name"),
                pl.lit(None, dtype=pl.Utf8).alias("provider_metadata_json"),
            )
        )
    if not matches.is_empty():
        frames.append(
            matches.select(
                pl.lit("match").alias("entity_type"),
                pl.col("bucephalus_match_id").alias("bucephalus_entity_id"),
                pl.lit("statsbomb").alias("provider"),
                pl.col("statsbomb_match_id").cast(pl.Utf8).alias("provider_entity_id"),
                pl.concat_str(["home_team_name", "away_team_name"], separator=" vs ").alias("provider_entity_name"),
                pl.lit(None, dtype=pl.Utf8).alias("provider_metadata_json"),
            )
        )
    if not frames:
        return pl.DataFrame(schema=EXTERNAL_LINKS_SCHEMA)
    return pl.concat(frames, how="vertical_relaxed").filter(pl.col("provider_entity_id").is_not_null())


def _resolution_report(players: pl.DataFrame, teams: pl.DataFrame) -> dict[str, Any]:
    player_collisions = _collisions(players, "normalized_player_name", "bucephalus_player_id")
    team_collisions = _collisions(teams, "normalized_team_name", "bucephalus_team_id")
    return {
        "entity_counts": {
            "players": players.height,
            "teams": teams.height,
        },
        "potential_duplicate_players": player_collisions,
        "potential_duplicate_teams": team_collisions,
        "normalized_name_collisions": {
            "players": len(player_collisions),
            "teams": len(team_collisions),
        },
        "players_without_external_id": int(players.filter(pl.col("statsbomb_player_id").is_null()).height) if not players.is_empty() else 0,
        "teams_without_external_id": int(teams.filter(pl.col("statsbomb_team_id").is_null()).height) if not teams.is_empty() else 0,
        "warnings": ["fuzzy matching not enabled; extension point is normalized-name collision review"],
    }


def _collisions(df: pl.DataFrame, name_col: str, id_col: str) -> list[dict[str, Any]]:
    if df.is_empty() or name_col not in df.columns:
        return []
    rows = (
        df.group_by(name_col)
        .agg(pl.col(id_col).n_unique().alias("entities"), pl.col(id_col).unique().alias("ids"))
        .filter((pl.col(name_col) != "") & (pl.col("entities") > 1))
        .to_dicts()
    )
    return [{"normalized_name": row[name_col], "entity_ids": _series_or_list(row["ids"])} for row in rows]


def _read(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else pl.DataFrame()


def _json_list(values: object) -> str:
    return json.dumps(_series_or_list(values), ensure_ascii=False)


def _series_or_list(values: object) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, pl.Series):
        values = values.to_list()
    if not isinstance(values, list):
        values = [values]
    return [value for value in values if value is not None and not (isinstance(value, str) and value == "")]


EXTERNAL_LINKS_SCHEMA = {
    "entity_type": pl.Utf8,
    "bucephalus_entity_id": pl.Utf8,
    "provider": pl.Utf8,
    "provider_entity_id": pl.Utf8,
    "provider_entity_name": pl.Utf8,
    "provider_metadata_json": pl.Utf8,
}
