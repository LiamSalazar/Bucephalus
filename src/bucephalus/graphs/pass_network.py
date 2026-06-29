from __future__ import annotations

import json
import math
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_pass_networks(paths: ProjectPaths) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    team_match_path = paths.features / "team_match_features.parquet"
    if not events_path.exists():
        return _write_empty(paths, "events.parquet missing")
    events = pl.read_parquet(events_path).sort(["match_id", "possession", "event_index"])
    passes = events.filter(pl.col("type_name") == "Pass")
    rows = events.to_dicts()
    next_player = {}
    for idx, row in enumerate(rows[:-1]):
        nxt = rows[idx + 1]
        if row["match_id"] == nxt["match_id"] and row["possession"] == nxt["possession"] and row["team_id"] == nxt["team_id"]:
            next_player[row["event_id"]] = (nxt.get("player_id"), nxt.get("player_name"))
    edge_rows = []
    for row in passes.to_dicts():
        receiver_id, receiver_name = next_player.get(row["event_id"], (None, None))
        if row.get("player_id") is None or receiver_id is None or row.get("player_id") == receiver_id:
            continue
        length = math.dist([row.get("location_x") or 0, row.get("location_y") or 0], [row.get("pass_end_x") or row.get("location_x") or 0, row.get("pass_end_y") or row.get("location_y") or 0])
        edge_rows.append({
            "match_id": row["match_id"], "team_id": row["team_id"], "team_name": row["team_name"],
            "passer_id": row["player_id"], "passer_name": row["player_name"],
            "receiver_id": receiver_id, "receiver_name": receiver_name,
            "pass_count": 1, "completed_count": 1, "progressive_pass_count": int((row.get("pass_end_x") or 0) - (row.get("location_x") or 0) > 10),
            "final_third_entry_count": int((row.get("location_x") or 0) < 80 <= (row.get("pass_end_x") or 0)),
            "pass_length": length, "start_x": row.get("location_x"), "start_y": row.get("location_y"),
            "end_x": row.get("pass_end_x"), "end_y": row.get("pass_end_y"), "under_pressure_count": int(bool(row.get("under_pressure"))),
        })
    edges = pl.DataFrame(edge_rows)
    if edges.is_empty():
        return _write_empty(paths, "no proxy pass edges")
    edges = edges.group_by(["match_id", "team_id", "team_name", "passer_id", "passer_name", "receiver_id", "receiver_name"]).agg(
        pl.col("pass_count").sum(),
        pl.col("completed_count").sum(),
        pl.col("progressive_pass_count").sum(),
        pl.col("final_third_entry_count").sum(),
        pl.col("pass_length").mean().alias("average_pass_length"),
        pl.col("start_x").mean().alias("average_start_x"),
        pl.col("start_y").mean().alias("average_start_y"),
        pl.col("end_x").mean().alias("average_end_x"),
        pl.col("end_y").mean().alias("average_end_y"),
        pl.col("under_pressure_count").sum(),
    ).with_columns(
        (pl.col("completed_count") / pl.col("pass_count")).alias("completion_rate"),
        ((pl.col("average_end_x") - pl.col("average_start_x")).clip(0, 120) / 120).alias("expected_threat_proxy"),
    )
    node_base = events.group_by(["match_id", "team_id", "team_name", "player_id", "player_name", "position_name"]).agg(
        pl.len().alias("touches"),
        (pl.col("type_name") == "Pass").sum().alias("passes_attempted"),
        (pl.col("type_name") == "Pressure").sum().alias("pressures_received"),
        pl.col("location_x").mean().alias("average_x"),
        pl.col("location_y").mean().alias("average_y"),
    ).filter(pl.col("player_id").is_not_null())
    degree = edges.group_by(["match_id", "team_id", "passer_id"]).agg(pl.col("pass_count").sum().alias("centrality_weighted_degree"), pl.len().alias("centrality_degree")).rename({"passer_id": "player_id"})
    nodes = node_base.join(degree, on=["match_id", "team_id", "player_id"], how="left").fill_null(0).with_columns(
        pl.col("passes_attempted").alias("passes_completed"),
        pl.lit(0).alias("turnovers"),
        pl.lit("pass_network_proxy").alias("role_proxy"),
    )
    metrics = _graph_metrics(edges)
    graphs = metrics.select(["match_id", "team_id", "team_name"]).with_columns(pl.lit("directed_weighted_pass_network_proxy").alias("graph_type"))
    nodes.write_parquet(paths.features / "pass_network_nodes.parquet")
    edges.write_parquet(paths.features / "pass_network_edges.parquet")
    graphs.write_parquet(paths.features / "pass_network_graphs.parquet")
    metrics.write_parquet(paths.features / "pass_network_metrics.parquet")
    if team_match_path.exists():
        metrics.join(pl.read_parquet(team_match_path).select(["statsbomb_match_id", "team_id", "xg_for", "shots_for", "possession_proxy"]), left_on=["match_id", "team_id"], right_on=["statsbomb_match_id", "team_id"], how="left").write_parquet(paths.features / "graph_model_dataset.parquet")
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "completed", "nodes": nodes.height, "edges": edges.height, "graphs": graphs.height, "receiver_policy": "next_same_team_event_proxy"}
    (paths.quality_outputs / "pass_network_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _graph_metrics(edges: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (match_id, team_id, team_name), group in edges.group_by(["match_id", "team_id", "team_name"], maintain_order=True):
        players = set(group["passer_id"].to_list()) | set(group["receiver_id"].to_list())
        n = max(1, len(players))
        total = float(group["pass_count"].sum())
        weights = group["pass_count"].to_numpy()
        probs = weights / max(1, weights.sum())
        rows.append({
            "match_id": match_id, "team_id": team_id, "team_name": team_name, "players_count": n,
            "density": group.height / max(1, n * (n - 1)), "average_degree": group.height / n,
            "weighted_degree": total / n, "clustering_coefficient": None,
            "centralization": float(weights.max() / max(1, weights.sum())),
            "pass_entropy": float(-(probs * __import__("numpy").log(probs + 1e-12)).sum()),
            "top_hub_dependency": float(weights.max() / max(1, weights.sum())),
            "left_progression_share": float(group.filter(pl.col("average_start_y") < 26.7)["progressive_pass_count"].sum() / max(1, group["progressive_pass_count"].sum())),
            "right_progression_share": float(group.filter(pl.col("average_start_y") > 53.3)["progressive_pass_count"].sum() / max(1, group["progressive_pass_count"].sum())),
            "central_progression_share": float(group.filter((pl.col("average_start_y") >= 26.7) & (pl.col("average_start_y") <= 53.3))["progressive_pass_count"].sum() / max(1, group["progressive_pass_count"].sum())),
            "build_up_concentration": float(group.filter(pl.col("average_start_x") < 60)["pass_count"].sum() / max(1, total)),
            "directness_graph_proxy": float(group["average_pass_length"].mean() / 120),
            "circulation_proxy": float(1 - weights.max() / max(1, weights.sum())),
        })
    return pl.DataFrame(rows)


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "skipped", "reason": reason}
    (paths.quality_outputs / "pass_network_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for name in ["pass_network_nodes", "pass_network_edges", "pass_network_graphs", "pass_network_metrics", "graph_model_dataset"]:
        pl.DataFrame().write_parquet(paths.features / f"{name}.parquet")
    return payload
