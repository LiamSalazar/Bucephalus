from __future__ import annotations

from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.features.build_basic_features import build_basic_features
from bucephalus.utils.logging import configure_logging


def main() -> None:
    configure_logging()
    build_master_entities()
    build_basic_features()


if __name__ == "__main__":
    main()
