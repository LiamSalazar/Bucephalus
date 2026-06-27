from __future__ import annotations

import duckdb

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths

CATALOG_TABLES = [
    "competitions",
    "matches",
    "teams",
    "players",
    "lineups",
    "events",
    "shots",
    "passes",
    "carries",
    "pressures",
    "duels",
    "goalkeeper_actions",
    "three_sixty",
    "master_players",
    "master_teams",
    "master_competitions",
    "master_matches",
    "external_entity_links",
]


def build_duckdb_catalog(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    con = duckdb.connect(str(paths.duckdb_path))
    try:
        for table in CATALOG_TABLES:
            parquet_path = paths.processed / f"{table}.parquet"
            if parquet_path.exists():
                con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{_sql_path(parquet_path)}')")
    finally:
        con.close()


def connect_catalog(paths: ProjectPaths | None = None) -> duckdb.DuckDBPyConnection:
    paths = paths or settings.paths
    return duckdb.connect(str(paths.duckdb_path))


def list_catalog_views(paths: ProjectPaths | None = None) -> list[str]:
    con = connect_catalog(paths)
    try:
        rows = con.execute("SHOW TABLES").fetchall()
        names = {row[0] for row in rows}
        return [table for table in CATALOG_TABLES if table in names]
    finally:
        con.close()


def _sql_path(path) -> str:
    return str(path).replace("'", "''")
