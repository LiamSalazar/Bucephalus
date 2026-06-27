from __future__ import annotations

from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.data.validation import validate_processed_dataset
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    configure_logging()
    paths = ProjectPaths()
    process_raw_to_parquet(paths)
    validate_processed_dataset(paths.processed)


if __name__ == "__main__":
    main()
