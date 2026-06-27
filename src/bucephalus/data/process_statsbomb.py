from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import polars as pl

from bucephalus.config import settings
from bucephalus.data.load_raw import iter_json_rows, raw_json_files
from bucephalus.utils.paths import ProjectPaths

LOGGER = logging.getLogger(__name__)


def process_raw_to_parquet(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    competitions = _competitions(paths)
    matches = _matches(paths)
    events = _events(paths)
    lineups = _lineups(paths)
    three_sixty = _three_sixty(paths)

    _write(competitions, paths.processed / "competitions.parquet")
    _write(matches, paths.processed / "matches.parquet")
    _write(lineups, paths.processed / "lineups.parquet")
    _write(events, paths.processed / "events.parquet")
    _write(three_sixty, paths.processed / "three_sixty.parquet")
    _write(_teams(matches, events, lineups), paths.processed / "teams.parquet")
    _write(_players(events, lineups), paths.processed / "players.parquet")

    _write(_filter_event(events, "Shot"), paths.processed / "shots.parquet")
    _write(_filter_event(events, "Pass"), paths.processed / "passes.parquet")
    _write(_filter_event(events, "Carry"), paths.processed / "carries.parquet")
    _write(_filter_event(events, "Pressure"), paths.processed / "pressures.parquet")
    _write(_filter_event(events, "Duel"), paths.processed / "duels.parquet")
    _write(_filter_event(events, "Goal Keeper"), paths.processed / "goalkeeper_actions.parquet")
    LOGGER.info("Processed Parquet files written to %s.", paths.processed)


def _competitions(paths: ProjectPaths) -> pl.DataFrame:
    files = raw_json_files("competitions", paths)
    rows = []
    for _, data in iter_json_rows(files):
        rows.extend(data)
    return _df(
        rows,
        {
            "competition_id": pl.Int64,
            "season_id": pl.Int64,
            "country_name": pl.Utf8,
            "competition_name": pl.Utf8,
            "competition_gender": pl.Utf8,
            "season_name": pl.Utf8,
        },
    )


def _matches(paths: ProjectPaths) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for path, data in iter_json_rows(raw_json_files("matches", paths)):
        source = _source(path, paths)
        for row in data:
            rows.append(
                {
                    "match_id": _as_int(row.get("match_id")),
                    "match_date": row.get("match_date"),
                    "kick_off": row.get("kick_off"),
                    "competition_id": _nested(row, "competition", "competition_id"),
                    "competition_name": _nested(row, "competition", "competition_name"),
                    "season_id": _nested(row, "season", "season_id"),
                    "season_name": _nested(row, "season", "season_name"),
                    "home_team_id": _nested(row, "home_team", "home_team_id"),
                    "home_team_name": _nested(row, "home_team", "home_team_name"),
                    "away_team_id": _nested(row, "away_team", "away_team_id"),
                    "away_team_name": _nested(row, "away_team", "away_team_name"),
                    "home_score": _as_int(row.get("home_score")),
                    "away_score": _as_int(row.get("away_score")),
                    "stage_name": _nested(row, "competition_stage", "name"),
                    "source_file": source,
                }
            )
    return _df(rows, MATCH_SCHEMA)


def _events(paths: ProjectPaths) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for path, data in iter_json_rows(raw_json_files("events", paths)):
        match_id = _as_int(path.stem)
        for row in data:
            location = row.get("location") or []
            pass_end = _nested_list(row, "pass", "end_location")
            carry_end = _nested_list(row, "carry", "end_location")
            shot = row.get("shot") or {}
            rows.append(
                {
                    "match_id": match_id,
                    "event_id": row.get("id"),
                    "event_index": _as_int(row.get("index")),
                    "period": _as_int(row.get("period")),
                    "timestamp": row.get("timestamp"),
                    "minute": _as_int(row.get("minute")),
                    "second": _as_int(row.get("second")),
                    "event_type": _nested(row, "type", "name"),
                    "possession": _as_int(row.get("possession")),
                    "possession_team_id": _nested(row, "possession_team", "id"),
                    "possession_team_name": _nested(row, "possession_team", "name"),
                    "team_id": _nested(row, "team", "id"),
                    "team_name": _nested(row, "team", "name"),
                    "player_id": _nested(row, "player", "id"),
                    "player_name": _nested(row, "player", "name"),
                    "position_id": _nested(row, "position", "id"),
                    "position_name": _nested(row, "position", "name"),
                    "location_x": _list_item(location, 0),
                    "location_y": _list_item(location, 1),
                    "pass_end_x": _list_item(pass_end, 0),
                    "pass_end_y": _list_item(pass_end, 1),
                    "carry_end_x": _list_item(carry_end, 0),
                    "carry_end_y": _list_item(carry_end, 1),
                    "shot_xg": _as_float(shot.get("statsbomb_xg")),
                    "shot_outcome": _nested(row, "shot", "outcome", "name"),
                    "shot_type": _nested(row, "shot", "type", "name"),
                    "duel_type": _nested(row, "duel", "type", "name"),
                    "duel_outcome": _nested(row, "duel", "outcome", "name"),
                    "goalkeeper_type": _nested(row, "goalkeeper", "type", "name"),
                    "goalkeeper_outcome": _nested(row, "goalkeeper", "outcome", "name"),
                    "play_pattern": _nested(row, "play_pattern", "name"),
                    "under_pressure": bool(row.get("under_pressure", False)),
                    "source_file": _source(path, paths),
                }
            )
    return _df(rows, EVENTS_SCHEMA)


def _lineups(paths: ProjectPaths) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for path, data in iter_json_rows(raw_json_files("lineups", paths)):
        match_id = _as_int(path.stem)
        for team in data:
            for player in team.get("lineup", []):
                positions = player.get("positions") or []
                rows.append(
                    {
                        "match_id": match_id,
                        "team_id": _as_int(team.get("team_id")),
                        "team_name": team.get("team_name"),
                        "player_id": _as_int(player.get("player_id")),
                        "player_name": player.get("player_name"),
                        "player_nickname": player.get("player_nickname"),
                        "country_id": _nested(player, "country", "id"),
                        "country_name": _nested(player, "country", "name"),
                        "positions_json": json.dumps(positions, ensure_ascii=False),
                        "position_names": "; ".join(
                            [p.get("position", "") for p in positions if p.get("position")]
                        ),
                        "source_file": _source(path, paths),
                    }
                )
    return _df(rows, LINEUPS_SCHEMA)


def _three_sixty(paths: ProjectPaths) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for path, data in iter_json_rows(raw_json_files("three-sixty", paths)):
        match_id = _as_int(path.stem)
        for row in data:
            rows.append(
                {
                    "match_id": match_id,
                    "event_id": row.get("event_uuid"),
                    "visible_area_json": json.dumps(row.get("visible_area"), ensure_ascii=False),
                    "freeze_frame_json": json.dumps(row.get("freeze_frame"), ensure_ascii=False),
                    "source_file": _source(path, paths),
                }
            )
    return _df(rows, THREE_SIXTY_SCHEMA)


def _teams(matches: pl.DataFrame, events: pl.DataFrame, lineups: pl.DataFrame) -> pl.DataFrame:
    frames = []
    if not matches.is_empty():
        frames.extend(
            [
                matches.select(
                    pl.col("home_team_id").alias("team_id"),
                    pl.col("home_team_name").alias("team_name"),
                    pl.col("competition_id"),
                ),
                matches.select(
                    pl.col("away_team_id").alias("team_id"),
                    pl.col("away_team_name").alias("team_name"),
                    pl.col("competition_id"),
                ),
            ]
        )
    if not events.is_empty():
        frames.append(events.select("team_id", "team_name", pl.lit(None).alias("competition_id")))
    if not lineups.is_empty():
        frames.append(lineups.select("team_id", "team_name", pl.lit(None).alias("competition_id")))
    if not frames:
        return _df([], TEAM_SCHEMA)
    return (
        pl.concat(frames, how="vertical_relaxed")
        .drop_nulls("team_id")
        .group_by("team_id")
        .agg(
            pl.col("team_name").drop_nulls().first(),
            pl.col("competition_id").drop_nulls().first(),
        )
    )


def _players(events: pl.DataFrame, lineups: pl.DataFrame) -> pl.DataFrame:
    frames = []
    if not events.is_empty():
        frames.append(
            events.select(
                "player_id",
                "player_name",
                "team_id",
                "team_name",
                pl.lit(None).alias("country_name"),
                pl.col("position_name").alias("position_names"),
            )
        )
    if not lineups.is_empty():
        frames.append(lineups.select("player_id", "player_name", "team_id", "team_name", "country_name", "position_names"))
    if not frames:
        return _df([], PLAYER_SCHEMA)
    return pl.concat(frames, how="vertical_relaxed").drop_nulls("player_id").unique()


def _filter_event(events: pl.DataFrame, event_type: str) -> pl.DataFrame:
    if events.is_empty():
        return events
    return events.filter(pl.col("event_type") == event_type)


def _df(rows: list[dict[str, Any]], schema: dict[str, pl.DataType]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(rows, schema=schema, strict=False)


def _write(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    LOGGER.info("Wrote %s rows to %s.", df.height, path.name)


def _source(path: Path, paths: ProjectPaths) -> str:
    return str(path.relative_to(paths.root))


def _nested(row: dict[str, Any], *keys: str) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _nested_list(row: dict[str, Any], *keys: str) -> list[Any]:
    value = _nested(row, *keys)
    return value if isinstance(value, list) else []


def _list_item(values: list[Any], idx: int) -> float | None:
    if len(values) <= idx:
        return None
    return _as_float(values[idx])


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


MATCH_SCHEMA = {
    "match_id": pl.Int64,
    "match_date": pl.Utf8,
    "kick_off": pl.Utf8,
    "competition_id": pl.Int64,
    "competition_name": pl.Utf8,
    "season_id": pl.Int64,
    "season_name": pl.Utf8,
    "home_team_id": pl.Int64,
    "home_team_name": pl.Utf8,
    "away_team_id": pl.Int64,
    "away_team_name": pl.Utf8,
    "home_score": pl.Int64,
    "away_score": pl.Int64,
    "stage_name": pl.Utf8,
    "source_file": pl.Utf8,
}

EVENTS_SCHEMA = {
    "match_id": pl.Int64,
    "event_id": pl.Utf8,
    "event_index": pl.Int64,
    "period": pl.Int64,
    "timestamp": pl.Utf8,
    "minute": pl.Int64,
    "second": pl.Int64,
    "event_type": pl.Utf8,
    "possession": pl.Int64,
    "possession_team_id": pl.Int64,
    "possession_team_name": pl.Utf8,
    "team_id": pl.Int64,
    "team_name": pl.Utf8,
    "player_id": pl.Int64,
    "player_name": pl.Utf8,
    "position_id": pl.Int64,
    "position_name": pl.Utf8,
    "location_x": pl.Float64,
    "location_y": pl.Float64,
    "pass_end_x": pl.Float64,
    "pass_end_y": pl.Float64,
    "carry_end_x": pl.Float64,
    "carry_end_y": pl.Float64,
    "shot_xg": pl.Float64,
    "shot_outcome": pl.Utf8,
    "shot_type": pl.Utf8,
    "duel_type": pl.Utf8,
    "duel_outcome": pl.Utf8,
    "goalkeeper_type": pl.Utf8,
    "goalkeeper_outcome": pl.Utf8,
    "play_pattern": pl.Utf8,
    "under_pressure": pl.Boolean,
    "source_file": pl.Utf8,
}

LINEUPS_SCHEMA = {
    "match_id": pl.Int64,
    "team_id": pl.Int64,
    "team_name": pl.Utf8,
    "player_id": pl.Int64,
    "player_name": pl.Utf8,
    "player_nickname": pl.Utf8,
    "country_id": pl.Int64,
    "country_name": pl.Utf8,
    "positions_json": pl.Utf8,
    "position_names": pl.Utf8,
    "source_file": pl.Utf8,
}

THREE_SIXTY_SCHEMA = {
    "match_id": pl.Int64,
    "event_id": pl.Utf8,
    "visible_area_json": pl.Utf8,
    "freeze_frame_json": pl.Utf8,
    "source_file": pl.Utf8,
}

TEAM_SCHEMA = {"team_id": pl.Int64, "team_name": pl.Utf8, "competition_id": pl.Int64}
PLAYER_SCHEMA = {
    "player_id": pl.Int64,
    "player_name": pl.Utf8,
    "team_id": pl.Int64,
    "team_name": pl.Utf8,
    "country_name": pl.Utf8,
    "position_names": pl.Utf8,
}
