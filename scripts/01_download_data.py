from __future__ import annotations

import argparse

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Download a small controlled sample.")
    parser.add_argument("--force-fallback", action="store_true", help="Use bundled sample data without network.")
    parser.add_argument("--max-matches", type=int, default=3)
    parser.add_argument("--competitions", type=int, nargs="*")
    parser.add_argument("--seasons", type=int, nargs="*")
    args = parser.parse_args()
    configure_logging()
    if not args.sample and not args.competitions and not args.seasons:
        args.sample = True
    download_sample(
        competitions=args.competitions,
        seasons=args.seasons,
        max_matches=args.max_matches,
        force_fallback=args.force_fallback,
    )


if __name__ == "__main__":
    main()
