from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.calibration.parameter_registry import build_parameter_registry
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    registry = build_parameter_registry(ProjectPaths(data_root=args.data_root))
    print(f"Parameter registry entries: {registry['parameters_count']}")


if __name__ == "__main__":
    main()
