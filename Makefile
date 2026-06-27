.PHONY: setup data-sample data-research process entities eda duckdb quality test phase-check all-phase-1-3

PYTHON ?= .venv/bin/python

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -e ".[dev]"

data-sample:
	$(PYTHON) scripts/01_download_data.py --sample --use-fallback

data-research:
	$(PYTHON) scripts/01_download_data.py --competition-id $(COMPETITION_ID) --season-id $(SEASON_ID) --max-matches $(MAX_MATCHES)

process:
	$(PYTHON) scripts/02_process_raw_to_parquet.py

entities:
	$(PYTHON) scripts/03_build_master_entities.py

eda:
	$(PYTHON) scripts/04_run_eda.py

duckdb:
	$(PYTHON) scripts/05_build_duckdb_catalog.py

quality:
	$(PYTHON) -c "from bucephalus.data.validation import validate_data_quality; validate_data_quality()"

test:
	$(PYTHON) -m pytest

phase-check:
	$(PYTHON) scripts/99_run_phase_1_3_check.py

all-phase-1-3: data-sample process entities eda duckdb quality test phase-check
