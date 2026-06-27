from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Use smoke-sample mode.")
    parser.add_argument("--research", action="store_true", help="Use controlled research mode.")
    parser.add_argument("--max-matches", type=int, default=3)
    parser.add_argument("--competition-id", type=int, action="append", dest="competition_ids")
    parser.add_argument("--season-id", type=int, action="append", dest="season_ids")
    parser.add_argument("--competitions", type=int, nargs="*", dest="competition_ids_legacy")
    parser.add_argument("--seasons", type=int, nargs="*", dest="season_ids_legacy")
    parser.add_argument("--force", action="store_true", help="Clear raw data before downloading.")
    parser.add_argument("--skip-360", action="store_true")
    parser.add_argument("--use-fallback", "--force-fallback", action="store_true", dest="use_fallback")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    if args.force and paths.raw.exists():
        shutil.rmtree(paths.raw)
    competition_ids = args.competition_ids or args.competition_ids_legacy
    season_ids = args.season_ids or args.season_ids_legacy
    if args.research:
        args.sample = False
    if not args.sample and not args.research and not competition_ids and not season_ids:
        args.sample = True
    download_sample(
        paths=paths,
        competitions=competition_ids,
        seasons=season_ids,
        max_matches=args.max_matches,
        force_fallback=args.use_fallback,
        skip_360=args.skip_360,
        mode="sample" if args.sample else "research",
    )


if __name__ == "__main__":
    main()
