from __future__ import annotations

from bucephalus.utils.paths import ProjectPaths


def test_project_paths_are_inside_repo() -> None:
    paths = ProjectPaths()
    assert paths.root.name == "Bucephalus"
    assert paths.raw == paths.root / "data" / "raw"
