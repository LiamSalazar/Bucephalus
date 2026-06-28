from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.utils.paths import ProjectPaths
from bucephalus.validation.leakage_audit import run_leakage_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    result = run_leakage_audit(ProjectPaths(data_root=args.data_root))
    print(f"Leakage audit passed: {result['passed']}")


if __name__ == "__main__":
    main()
