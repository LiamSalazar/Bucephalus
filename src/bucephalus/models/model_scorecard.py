from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_phase8_scorecard(paths: ProjectPaths) -> dict:
    rows = []
    xg = _read_json(paths.evaluation_outputs / "xg_metrics.json")
    tab = _read_json(paths.evaluation_outputs / "tabular_model_metrics.json")
    hazard = _read_json(paths.evaluation_outputs / "hazard_metrics.json")
    epv = _read_json(paths.evaluation_outputs / "epv_metrics.json")
    seq = _read_json(paths.evaluation_outputs / "sequence_model_metrics.json")
    gnn = _read_json(paths.evaluation_outputs / "gnn_metrics.json")
    mc = _read_json(paths.evaluation_outputs / "mc_dropout_summary.json")
    vec = _read_json(paths.quality_outputs / "vectorized_simulation_benchmark.json")
    rows.append(_row("xG", "logistic_xg_v1", "hist_gradient_boosting_xg_v2", "log_loss", xg.get("log_loss"), tab.get("log_loss"), paths.evaluation_outputs / "tabular_model_metrics.json"))
    rows.append(_row("hazard", "global_prevalence", "logistic_event_hazard", "roc_auc", 0.5, hazard.get("roc_auc"), paths.evaluation_outputs / "hazard_metrics.json", higher=True))
    rows.append(_row("EPV", "none", "hazard_xg_epv", "mean_epv", None, epv.get("mean_epv"), paths.evaluation_outputs / "epv_metrics.json"))
    rows.append(_row("sequence", "hazard_tabular", "pytorch_gru", "brier_score", hazard.get("brier_score"), seq.get("brier_score"), paths.evaluation_outputs / "sequence_model_metrics.json"))
    rows.append(_row("MC Dropout", "point_prediction", "mc_dropout", "mean_epistemic_uncertainty", None, mc.get("mean_epistemic_uncertainty"), paths.evaluation_outputs / "mc_dropout_summary.json"))
    rows.append(_row("vectorized Monte Carlo", "loop", "numpy_vectorized", "simulations_per_second", None, vec.get("simulations_per_second"), paths.quality_outputs / "vectorized_simulation_benchmark.json", higher=True))
    rows.append(_row("pass network", "none", "pass_network_proxy", "graphs", None, _read_json(paths.quality_outputs / "pass_network_report.json").get("graphs"), paths.quality_outputs / "pass_network_report.json", higher=True))
    gnn_baselines = [gnn.get("baseline_mae"), gnn.get("no_edge_mae"), gnn.get("permuted_edge_mae")]
    gnn_valid_baselines = [value for value in gnn_baselines if value is not None]
    best_gnn_baseline = min(gnn_valid_baselines) if gnn_valid_baselines else None
    rows.append(_row("GNN", "best_non_graph_baseline", "manual_gcn", "mae", best_gnn_baseline, gnn.get("gnn_mae"), paths.evaluation_outputs / "gnn_metrics.json"))
    rows.append(_row("explainability", "none", "tabular_sequence_gnn", "artifacts", None, 1.0, paths.outputs / "explainability" / "prediction_explanation_sample.json", higher=True))
    df = pl.DataFrame(rows)
    df.write_csv(paths.evaluation_outputs / "phase8_model_scorecard.csv")
    payload = {"generated_at": datetime.now(UTC).isoformat(), "rows": rows}
    (paths.evaluation_outputs / "phase8_model_scorecard.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _row(component, baseline, advanced, metric, base_score, adv_score, artifact, higher=False):
    if base_score is None or adv_score is None:
        status = "candidate" if adv_score is not None else "insufficient_data"
        improvement = None
    else:
        improvement = ((adv_score - base_score) / max(abs(base_score), 1e-9) * 100) if higher else ((base_score - adv_score) / max(abs(base_score), 1e-9) * 100)
        status = "champion" if improvement > 0 else "experimental"
    return {"component": component, "baseline_model": baseline, "advanced_model": advanced, "primary_metric": metric, "baseline_score": base_score, "advanced_score": adv_score, "improvement_pct": improvement, "validation_method": "temporal_or_holdout", "status": status, "reason": "improves baseline" if status == "champion" else "does not clearly improve or baseline unavailable", "artifact_path": str(artifact)}


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
