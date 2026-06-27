from __future__ import annotations

from dataclasses import dataclass

from bucephalus.utils.paths import ProjectPaths


@dataclass(frozen=True)
class Settings:
    paths: ProjectPaths = ProjectPaths()
    statsbomb_base_url: str = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
    default_max_matches: int = 3


settings = Settings()
