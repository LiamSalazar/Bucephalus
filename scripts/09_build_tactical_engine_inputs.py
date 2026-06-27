from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.tactics.style_profiles import build_tactical_engine_inputs
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    manifest = build_tactical_engine_inputs(ProjectPaths(data_root=args.data_root))
    print("Tactical engine inputs:", manifest)


if __name__ == "__main__":
    main()
