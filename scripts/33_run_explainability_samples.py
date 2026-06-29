from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.explainability.sequence_explain import build_sequence_explanation
from bucephalus.explainability.tabular_explain import build_tabular_explanations
from bucephalus.explainability.gnn_explain import build_gnn_explanations
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    print(build_tabular_explanations(paths))
    print(build_sequence_explanation(paths))
    print(build_gnn_explanations(paths))


if __name__ == "__main__":
    main()
