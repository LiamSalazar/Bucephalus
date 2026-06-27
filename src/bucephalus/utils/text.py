from __future__ import annotations

import re
import unicodedata


def strip_accents(value: str | None) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def clean_punctuation(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9\s.'-]", " ", str(value))


def clean_spaces(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_text(value: str | None) -> str:
    text = strip_accents(value).lower()
    text = clean_punctuation(text)
    return clean_spaces(text)
