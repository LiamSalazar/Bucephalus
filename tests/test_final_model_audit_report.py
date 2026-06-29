from __future__ import annotations

from bucephalus.reports.final_model_audit import write_final_model_audit_report
from bucephalus.utils.paths import ProjectPaths


def test_final_model_audit_report_generates_with_missing_artifacts(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    payload = write_final_model_audit_report(paths)
    report = (paths.outputs / "reports" / "final_model_audit_report.md").read_text(encoding="utf-8")
    assert payload["report"].endswith("final_model_audit_report.md")
    for section in [
        "Executive Summary",
        "Dataset & Coverage",
        "Leakage Audit",
        "Model Scorecard",
        "Overfitting Analysis",
        "Objective Compliance",
        "Action Items",
    ]:
        assert section in report
    assert "Artifact missing:" in report
    assert "Ready for Phase 9:" in report
    assert "Overfitting risk:" in report
