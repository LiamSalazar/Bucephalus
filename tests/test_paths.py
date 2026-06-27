from __future__ import annotations

from bucephalus.utils.paths import ProjectPaths


def test_project_paths_are_inside_repo(monkeypatch) -> None:
    monkeypatch.delenv("BUCEPHALUS_DATA_ROOT", raising=False)
    paths = ProjectPaths()
    assert paths.root.name == "Bucephalus"
    assert paths.raw == paths.root / "data" / "raw"


def test_project_paths_allow_env_override(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BUCEPHALUS_DATA_ROOT", str(tmp_path / "data"))
    paths = ProjectPaths()
    assert paths.raw == tmp_path / "data" / "raw"
