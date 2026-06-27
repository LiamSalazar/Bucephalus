from __future__ import annotations

from bucephalus.utils.text import clean_spaces, normalize_text, strip_accents


def test_normalize_text_handles_accents_spaces_nulls_and_punctuation() -> None:
    assert normalize_text("  João   Félix!! ") == "joao felix"
    assert normalize_text(None) == ""
    assert clean_spaces("a   b") == "a b"
    assert strip_accents("Bellinghám") == "Bellingham"
