.PHONY: setup data-sample data-research process entities eda duckdb quality features train-baselines evaluate-baselines test phase-check phase-4-5-check all-phase-1-3 all-phase-4-5 full-pipeline

PYTHON ?= .venv/bin/python
MAX_MATCHES ?= 150

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -e ".[dev]"

data-sample:
	$(PYTHON) scripts/01_download_data.py --sample --use-fallback

data-research:
	$(PYTHON) scripts/01_download_data.py --research --max-matches $(MAX_MATCHES) --skip-360

process:
	$(PYTHON) scripts/02_process_raw_to_parquet.py

entities:
	$(PYTHON) scripts/03_build_master_entities.py

eda:
	$(PYTHON) scripts/04_run_eda.py

duckdb:
	$(PYTHON) scripts/05_build_duckdb_catalog.py

quality:
	$(PYTHON) -c "from bucephalus.data.validation import validate_data_quality; from bucephalus.data.research_summary import write_research_dataset_summary; validate_data_quality(); write_research_dataset_summary()"

features:
	$(PYTHON) scripts/06_build_feature_store.py

train-baselines:
	$(PYTHON) scripts/07_train_baseline_models.py

evaluate-baselines:
	$(PYTHON) scripts/08_evaluate_baselines.py

test:
	$(PYTHON) -m pytest

phase-check:
	$(PYTHON) scripts/99_run_phase_1_3_check.py

phase-4-5-check:
	$(PYTHON) scripts/98_run_phase_4_5_check.py

all-phase-1-3: data-sample process entities eda duckdb quality test phase-check

all-phase-4-5: features train-baselines evaluate-baselines phase-4-5-check

full-pipeline: data-research process entities quality eda duckdb features train-baselines evaluate-baselines phase-4-5-check test
