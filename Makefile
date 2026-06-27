.PHONY: setup data-sample process entities eda test

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"

data-sample:
	.venv/bin/python scripts/01_download_data.py --sample

process:
	.venv/bin/python scripts/02_process_raw_to_parquet.py

entities:
	.venv/bin/python scripts/03_build_master_entities.py

eda:
	.venv/bin/python scripts/04_run_eda.py

test:
	.venv/bin/python -m pytest
