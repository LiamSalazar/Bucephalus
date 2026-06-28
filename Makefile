.PHONY: setup data-sample data-research process entities eda duckdb quality features train-baselines evaluate-baselines tactical-inputs tactical-scenario simulate-match sensitivity parameter-registry calibration-registry train-xg evaluate-xg calibrate-markov team-strength bootstrap-tactical validate-simulation ablation leakage-audit incremental-manifest incremental-features performance-benchmark model-registry pre-phase-8-audit test phase-check phase-4-5-check phase-6-7-check phase-7-5-check pre-phase-8-check all-phase-1-3 all-phase-4-5 all-phase-6-7 all-phase-7-5 all-phase-7-7 pre-phase-8 full-pipeline

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

tactical-inputs:
	$(PYTHON) scripts/09_build_tactical_engine_inputs.py

tactical-scenario:
	$(PYTHON) scripts/10_run_tactical_scenario.py --auto-pick-teams

simulate-match:
	$(PYTHON) scripts/11_run_match_simulation.py --auto-pick-teams --n-simulations 500 --seed 42

sensitivity:
	$(PYTHON) scripts/12_run_sensitivity_analysis.py --auto-pick-teams --slider pressing --values=-0.2,0,0.2 --n-simulations 300

calibration-registry:
	$(PYTHON) scripts/13_build_parameter_registry.py

parameter-registry: calibration-registry

train-xg:
	$(PYTHON) scripts/13_train_xg_model.py

evaluate-xg:
	$(PYTHON) scripts/14_evaluate_xg_model.py

calibrate-markov:
	$(PYTHON) scripts/15_calibrate_markov_matrix.py

team-strength:
	$(PYTHON) scripts/21_build_team_strength.py

bootstrap-tactical:
	$(PYTHON) scripts/19_bootstrap_tactical_parameters.py

validate-simulation:
	$(PYTHON) scripts/16_validate_simulation_backtest.py

ablation:
	$(PYTHON) scripts/17_run_ablation_study.py

leakage-audit:
	$(PYTHON) scripts/18_run_leakage_audit.py

incremental-manifest:
	$(PYTHON) scripts/22_build_ingestion_manifest.py

incremental-features:
	$(PYTHON) scripts/23_update_incremental_features.py

performance-benchmark:
	$(PYTHON) scripts/20_run_performance_benchmark.py

model-registry:
	$(PYTHON) scripts/24_build_model_registry.py

pre-phase-8-audit:
	$(PYTHON) scripts/25_write_pre_phase_8_gap_audit.py

test:
	$(PYTHON) -m pytest

phase-check:
	$(PYTHON) scripts/99_run_phase_1_3_check.py

phase-4-5-check:
	$(PYTHON) scripts/98_run_phase_4_5_check.py

phase-6-7-check:
	$(PYTHON) scripts/97_run_phase_6_7_check.py

phase-7-5-check:
	$(PYTHON) scripts/96_run_phase_7_5_check.py

pre-phase-8-check:
	$(PYTHON) scripts/95_run_pre_phase_8_check.py

all-phase-1-3: data-sample process entities eda duckdb quality test phase-check

all-phase-4-5: features train-baselines evaluate-baselines phase-4-5-check

all-phase-6-7: tactical-inputs tactical-scenario simulate-match sensitivity phase-6-7-check

all-phase-7-5: parameter-registry leakage-audit train-xg evaluate-xg calibrate-markov team-strength bootstrap-tactical validate-simulation ablation phase-7-5-check

all-phase-7-7: incremental-manifest incremental-features performance-benchmark model-registry

pre-phase-8: pre-phase-8-audit all-phase-7-5 all-phase-7-7 pre-phase-8-check

full-pipeline: all-phase-1-3 all-phase-4-5 all-phase-6-7 pre-phase-8
