from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from bucephalus.config import settings
from bucephalus.data.sample_data import (
    FALLBACK_COMPETITIONS,
    FALLBACK_LINEUPS,
    FALLBACK_MATCHES,
    fallback_events,
    fallback_three_sixty,
)
from bucephalus.utils.paths import ProjectPaths

LOGGER = logging.getLogger(__name__)


def download_sample(
    paths: ProjectPaths | None = None,
    competitions: list[int] | None = None,
    seasons: list[int] | None = None,
    max_matches: int | None = None,
    force_fallback: bool = False,
) -> None:
    paths = paths or settings.paths
    paths.ensure()
    max_matches = max_matches or settings.default_max_matches
    if force_fallback:
        LOGGER.warning("Using bundled fallback sample by request.")
        write_fallback(paths, max_matches=max_matches)
        return

    try:
        competitions_data = _get_json(f"{settings.statsbomb_base_url}/competitions.json")
        _write_json(paths.raw / "competitions.json", competitions_data)
        selected = _select_competitions(competitions_data, competitions, seasons)
        if not selected:
            raise ValueError("No competitions matched filters.")

        downloaded_matches = 0
        for comp in selected:
            if downloaded_matches >= max_matches:
                break
            comp_id = int(comp["competition_id"])
            season_id = int(comp["season_id"])
            matches = _get_json(f"{settings.statsbomb_base_url}/matches/{comp_id}/{season_id}.json")
            match_path = paths.raw / "matches" / str(comp_id)
            _write_json(match_path / f"{season_id}.json", matches)
            for match in matches[: max_matches - downloaded_matches]:
                match_id = int(match["match_id"])
                _download_optional_json(f"events/{match_id}.json", paths.raw / "events" / f"{match_id}.json")
                _download_optional_json(f"lineups/{match_id}.json", paths.raw / "lineups" / f"{match_id}.json")
                _download_optional_json(
                    f"three-sixty/{match_id}.json", paths.raw / "three-sixty" / f"{match_id}.json"
                )
                downloaded_matches += 1
        LOGGER.info("Downloaded StatsBomb sample with %s matches.", downloaded_matches)
    except Exception as exc:
        LOGGER.warning("StatsBomb download failed; writing fallback sample. Error: %s", exc)
        write_fallback(paths, max_matches=max_matches)


def write_fallback(paths: ProjectPaths | None = None, max_matches: int = 2) -> None:
    paths = paths or settings.paths
    paths.ensure()
    _write_json(paths.raw / "competitions.json", FALLBACK_COMPETITIONS)
    _write_json(paths.raw / "matches" / "999" / "2024.json", FALLBACK_MATCHES[:max_matches])
    for match in FALLBACK_MATCHES[:max_matches]:
        match_id = int(match["match_id"])
        _write_json(paths.raw / "events" / f"{match_id}.json", fallback_events(match_id))
        _write_json(paths.raw / "lineups" / f"{match_id}.json", FALLBACK_LINEUPS)
        _write_json(paths.raw / "three-sixty" / f"{match_id}.json", fallback_three_sixty(match_id))
    LOGGER.info("Fallback sample written to %s.", paths.raw)


def _select_competitions(
    rows: list[dict], competitions: list[int] | None, seasons: list[int] | None
) -> list[dict]:
    selected = rows
    if competitions:
        selected = [r for r in selected if int(r["competition_id"]) in competitions]
    if seasons:
        selected = [r for r in selected if int(r["season_id"]) in seasons]
    if not competitions and not seasons:
        # Small default: pick one recent competition-season from the public index.
        selected = selected[:1]
    return selected


def _download_optional_json(relative_url: str, output_path: Path) -> None:
    try:
        data = _get_json(f"{settings.statsbomb_base_url}/{relative_url}")
    except (URLError, FileNotFoundError, ValueError) as exc:
        LOGGER.info("Optional file missing or unavailable: %s (%s)", relative_url, exc)
        return
    _write_json(output_path, data)


def _get_json(url: str) -> list[dict] | dict:
    with urlopen(url, timeout=30) as response:  # noqa: S310 - fixed public open-data URL.
        return json.loads(response.read().decode("utf-8"))


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
