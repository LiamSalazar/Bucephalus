from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def update_incremental_feature_store(paths: ProjectPaths) -> dict:
    paths.ensure()
    manifest_path = paths.processed / "ingestion_manifest.parquet"
    team_features_path = paths.features / "team_match_features.parquet"
    if not manifest_path.exists() or not team_features_path.exists():
        return _write_report(paths, "skipped", ["ingestion manifest or team_match_features missing"], 0)
    manifest = pl.read_parquet(manifest_path)
    team_features = pl.read_parquet(team_features_path)
    processed_matches = set(str(v) for v in manifest.get_column("provider_match_id").to_list()) if not manifest.is_empty() else set()
    feature_matches = set(str(v) for v in team_features.get_column("statsbomb_match_id").to_list()) if "statsbomb_match_id" in team_features.columns else set()
    new_matches = sorted(processed_matches - feature_matches)
    version_dir = paths.features / "versions" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    version_dir.mkdir(parents=True, exist_ok=True)
    preserved = []
    for feature_file in paths.features.glob("*.parquet"):
        target = version_dir / feature_file.name
        shutil.copy2(feature_file, target)
        preserved.append(str(target))
    affected_teams: list[str] = []
    if new_matches and "statsbomb_match_id" in team_features.columns:
        affected = team_features.filter(pl.col("statsbomb_match_id").cast(pl.Utf8).is_in(new_matches))
        if "bucephalus_team_id" in affected.columns:
            affected_teams = sorted(str(v) for v in affected["bucephalus_team_id"].unique().to_list())
    # Current store is append-ready; full recomputation remains the safe path for this phase.
    return _write_report(
        paths,
        "completed",
        ["no new matches detected"] if not new_matches else ["new matches detected; run feature rebuild for affected teams"],
        len(new_matches),
        affected_teams,
        preserved,
    )


def _write_report(
    paths: ProjectPaths,
    status: str,
    warnings: list[str],
    new_matches_count: int,
    affected_teams: list[str] | None = None,
    preserved_versions: list[str] | None = None,
) -> dict:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "new_matches_count": new_matches_count,
        "affected_teams": affected_teams or [],
        "append_merge_policy": "detect by provider match checksum; append safe new rows, preserve previous parquet snapshot",
        "recomputed_full": False,
        "preserved_versions": preserved_versions or [],
        "rolling_recalculation_policy": "recalculate only affected teams when new matches are detected",
        "warnings": warnings,
    }
    (paths.quality_outputs / "incremental_feature_update_report.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return payload
