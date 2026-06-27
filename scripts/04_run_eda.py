from __future__ import annotations

from bucephalus.eda.distributions import run_eda
from bucephalus.utils.logging import configure_logging


def main() -> None:
    configure_logging()
    run_eda()


if __name__ == "__main__":
    main()
