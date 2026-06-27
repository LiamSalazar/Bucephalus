from __future__ import annotations

from bucephalus.data.entity_resolution import normalize_name, stable_entity_id


def test_normalize_name_removes_accents_and_extra_spaces() -> None:
    assert normalize_name("  João   Félix!! ") == "joao felix"


def test_stable_entity_id_is_deterministic() -> None:
    assert stable_entity_id("ply", 1, "Test") == stable_entity_id("ply", 1, "Test")
    assert stable_entity_id("ply", 1, "Test").startswith("ply_")
