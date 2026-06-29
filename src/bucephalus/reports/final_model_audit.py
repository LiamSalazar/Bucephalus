from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bucephalus.utils.paths import ProjectPaths


ARTIFACTS = [
    "outputs/evaluation/phase8_model_scorecard.csv",
    "outputs/evaluation/phase8_model_scorecard.json",
    "outputs/evaluation/tabular_model_metrics.json",
    "outputs/evaluation/tabular_model_comparison.csv",
    "outputs/evaluation/xg_metrics.json",
    "outputs/evaluation/xg_calibration_summary.csv",
    "outputs/evaluation/hazard_metrics.json",
    "outputs/evaluation/hazard_calibration_summary.csv",
    "outputs/evaluation/epv_metrics.json",
    "outputs/evaluation/sequence_model_metrics.json",
    "outputs/evaluation/sequence_temporal_split.json",
    "outputs/evaluation/mc_dropout_summary.json",
    "outputs/evaluation/gnn_metrics.json",
    "outputs/evaluation/gnn_model_comparison.csv",
    "outputs/evaluation/gnn_validation_report.json",
    "outputs/evaluation/simulation_backtest_metrics.json",
    "outputs/evaluation/simulation_model_comparison.csv",
    "outputs/evaluation/leakage_audit.json",
    "outputs/evaluation/markov_validation_report.json",
    "outputs/evaluation/ablation_summary.json",
    "outputs/quality/vectorized_simulation_benchmark.json",
    "outputs/quality/performance_benchmark.json",
    "outputs/models/model_registry.json",
    "outputs/models/xg_model_registry.json",
    "outputs/models/hazard_model_registry.json",
    "outputs/models/sequence_model_registry.json",
    "outputs/models/gnn_model_registry.json",
    "outputs/explainability/tabular_feature_importance.csv",
    "outputs/explainability/xg_explanation_sample.json",
    "outputs/explainability/sequence_event_attribution_sample.json",
    "outputs/explainability/gnn_edge_importance_sample.json",
    "data/processed/data_manifest.json",
    "outputs/quality/research_dataset_summary.json",
]


def write_final_model_audit_report(paths: ProjectPaths) -> dict[str, Any]:
    paths.ensure()
    loaded = {artifact: _load(_artifact_path(paths, artifact)) for artifact in ARTIFACTS}
    missing = [artifact for artifact, value in loaded.items() if value is None]
    scorecard = loaded.get("outputs/evaluation/phase8_model_scorecard.json") or {}
    leakage = loaded.get("outputs/evaluation/leakage_audit.json") or {}
    xg = loaded.get("outputs/evaluation/xg_metrics.json") or {}
    hazard = loaded.get("outputs/evaluation/hazard_metrics.json") or {}
    epv = loaded.get("outputs/evaluation/epv_metrics.json") or {}
    sequence = loaded.get("outputs/evaluation/sequence_model_metrics.json") or {}
    gnn = loaded.get("outputs/evaluation/gnn_metrics.json") or {}
    gnn_validation = loaded.get("outputs/evaluation/gnn_validation_report.json") or {}
    backtest = loaded.get("outputs/evaluation/simulation_backtest_metrics.json") or {}
    vectorized = loaded.get("outputs/quality/vectorized_simulation_benchmark.json") or {}
    performance = loaded.get("outputs/quality/performance_benchmark.json") or {}
    registry = loaded.get("outputs/models/model_registry.json") or {}
    manifest = loaded.get("data/processed/data_manifest.json") or {}
    research = loaded.get("outputs/quality/research_dataset_summary.json") or {}

    statuses = {row.get("component"): row.get("status") for row in scorecard.get("rows", [])}
    hard_failures = [item for item in ["hazard", "EPV", "sequence", "GNN"] if statuses.get(item) in {"rejected", "insufficient_data"}]
    overall = "FAIL" if hard_failures else ("WARNING" if missing or any(v == "experimental" for v in statuses.values()) else "PASS")
    ready = "NO" if overall == "FAIL" else ("YES WITH WARNINGS" if overall == "WARNING" else "YES")
    overfitting = _overfitting_risk(sequence, gnn)
    calibration = _calibration_status(xg, hazard)
    gnn_value = gnn_validation.get("does_gnn_add_value_beyond_graph_metrics") or ("YES" if gnn.get("status") == "champion" else "NO")
    objective = "YES" if overall == "PASS" else "PARTIALLY"

    report = [
        "# Bucephalus Final Model Audit Report",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## 1. Executive Summary",
        f"Overall status: {overall}",
        f"Ready for Phase 9: {ready}",
        f"Objective compliance: {objective}",
        "",
        "## 2. Dataset & Coverage",
        _json_summary({"manifest": manifest, "research_dataset": research}),
        "",
        "## 3. Pipeline Health",
        _artifact_summary(loaded, missing),
        "",
        "## 4. Leakage Audit",
        _json_summary(leakage),
        "",
        "## 5. Model Scorecard",
        _scorecard_table(scorecard),
        "",
        "## 6. xG Model Results",
        _json_summary(xg),
        "",
        "## 7. Hazard / Survival Model Results",
        _json_summary(hazard),
        "",
        "## 8. EPV Results",
        _json_summary(epv),
        "",
        "## 9. Sequence Model Results",
        _json_summary(sequence),
        "",
        "## 10. Overfitting Analysis",
        f"Overfitting risk: {overfitting}",
        "Split-specific train/validation/test diagnostics are limited; temporal split metadata is used where available.",
        "",
        "## 11. Calibration Analysis",
        f"Calibration status: {calibration}",
        "",
        "## 12. Simulation Results",
        _json_summary(backtest),
        "",
        "## 13. Monte Carlo & Uncertainty",
        _json_summary({"vectorized": vectorized, "uncertainty_sources": vectorized.get("uncertainty_sources")}),
        "",
        "## 14. Vectorized Simulation Benchmark",
        _json_summary(vectorized),
        "",
        "## 15. Pass Network & GNN Results",
        f"Does the GNN add value beyond graph metrics? {gnn_value}",
        _json_summary({"gnn_metrics": gnn, "gnn_validation": gnn_validation}),
        "",
        "## 16. Explainability Results",
        _explainability_summary(loaded),
        "",
        "## 17. Model Registry & Reproducibility",
        _json_summary(registry),
        "",
        "## 18. Performance & Scalability",
        _json_summary(performance),
        "",
        "## 19. Objective Compliance",
        "Does the current system satisfy the objective of being a serious data-driven football simulation engine?",
        f"{objective}",
        "Can we move to Phase 9?",
        ready.replace("YES WITH WARNINGS", "YES, WITH WARNINGS"),
        "",
        "## 20. Action Items",
        "- Expand research dataset before promoting experimental Deep Learning components.",
        "- Keep hazard and xG baselines as benchmarks for every future advanced model.",
        "- Replace pass receiver proxy when provider data includes reliable recipient IDs.",
        "- Add richer split diagnostics for overfitting analysis in larger datasets.",
    ]
    if missing:
        report.extend(["", "## Missing Artifacts"])
        for artifact in missing:
            report.extend([f"Artifact missing: {artifact}", "Impact: associated section may be incomplete or marked unknown.", ""])
    out = paths.outputs / "reports" / "final_model_audit_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report).strip() + "\n", encoding="utf-8")
    payload = {"report": str(out), "overall_status": overall, "ready_for_phase_9": ready, "missing_artifacts": missing}
    return payload


def _load(path: Path) -> Any | None:
    if not path.exists():
        return None
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".csv":
        with path.open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    return path.read_text(encoding="utf-8")


def _artifact_path(paths: ProjectPaths, artifact: str) -> Path:
    if artifact.startswith("outputs/"):
        return paths.outputs / artifact.removeprefix("outputs/")
    if artifact.startswith("data/processed/"):
        return paths.processed / artifact.removeprefix("data/processed/")
    if artifact.startswith("data/features/"):
        return paths.features / artifact.removeprefix("data/features/")
    return paths.root / artifact


def _json_summary(value: Any) -> str:
    if not value:
        return "No artifact data available."
    text = json.dumps(value, indent=2, default=str)
    return f"```json\n{text[:6000]}\n```"


def _artifact_summary(loaded: dict[str, Any], missing: list[str]) -> str:
    return f"Artifacts checked: {len(loaded)}\nArtifacts missing: {len(missing)}"


def _scorecard_table(scorecard: dict[str, Any]) -> str:
    rows = scorecard.get("rows", [])
    if not rows:
        return "No scorecard rows available."
    lines = ["| Component | Status | Metric | Baseline | Advanced | Improvement % |", "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row.get('component')} | {row.get('status')} | {row.get('primary_metric')} | {row.get('baseline_score')} | {row.get('advanced_score')} | {row.get('improvement_pct')} |")
    return "\n".join(lines)


def _overfitting_risk(sequence: dict[str, Any], gnn: dict[str, Any]) -> str:
    if not sequence or not gnn:
        return "UNKNOWN"
    if sequence.get("validation_brier_score") is None:
        return "UNKNOWN"
    if gnn.get("rows", 0) < 30:
        return "MEDIUM"
    return "LOW"


def _calibration_status(xg: dict[str, Any], hazard: dict[str, Any]) -> str:
    xg_brier = xg.get("brier_score")
    hazard_cal = hazard.get("calibration_error")
    if xg_brier is None and hazard_cal is None:
        return "UNKNOWN"
    if (xg_brier is not None and xg_brier < 0.12) and (hazard_cal is None or hazard_cal < 0.08):
        return "ACCEPTABLE"
    return "POOR"


def _explainability_summary(loaded: dict[str, Any]) -> str:
    keys = [key for key in loaded if key.startswith("outputs/explainability/")]
    present = [key for key in keys if loaded[key] is not None]
    return f"Explainability artifacts present: {len(present)}/{len(keys)}\nMethods include permutation importance and local occlusion where model artifacts exist."
