# Bucephalus

Bucephalus es la base de un motor de simulación futbolística basado en datos reales. El objetivo final es soportar Game Mode y Lab Mode, pero este repositorio llega hasta Fase 8: Advanced ML, Deep Learning, Graph Learning, Uncertainty, Explainability & Final Audit. La prioridad actual es reproducibilidad, trazabilidad, validación temporal sin leakage, calibración empírica, incertidumbre, explicabilidad y auditoría centralizada. No hay frontend, backend API productivo, mercado, Game Mode completo ni chatbot/LLM.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Pipeline smoke sample

El smoke sample es pequeño, rápido y tolerante a falta de internet mediante fallback local.

```bash
make data-sample
make process
make entities
make eda
make duckdb
make quality
make test
make phase-check
```

Equivalente por scripts:

```bash
python scripts/01_download_data.py --sample --use-fallback
python scripts/02_process_raw_to_parquet.py
python scripts/03_build_master_entities.py
python scripts/04_run_eda.py
python scripts/05_build_duckdb_catalog.py
python scripts/99_run_phase_1_3_check.py
```

## Feature store y baselines

```bash
make features
make train-baselines
make evaluate-baselines
make phase-4-5-check
```

## Tactical Engine y simulación

```bash
make tactical-inputs
make tactical-scenario
make simulate-match
make sensitivity
make phase-6-7-check
```

## Scientific Hardening 7.5-7.7

```bash
make parameter-registry
make leakage-audit
make train-xg
make evaluate-xg
make calibrate-markov
make team-strength
make bootstrap-tactical
make validate-simulation
make ablation
make phase-7-5-check
make incremental-manifest
make incremental-features
make performance-benchmark
make model-registry
make pre-phase-8-check
make pre-phase-8
```

## Fase 8 ML Avanzado

```bash
make train-tabular
make evaluate-tabular
make train-hazard
make evaluate-hazard
make train-sequence
make evaluate-sequence
make mc-dropout
make vectorized-simulation
make pass-network
make train-gnn
make evaluate-gnn
make explainability
make phase8-scorecard
make phase8-summary
make final-model-report
make phase-8-check
make all-phase-8
```

Fase 8 incluye modelos tabulares avanzados, hazard model para controlar survival/look-ahead bias, EPV alineado por claves reales usando `P(shot) x conditional_xG`, PyTorch GRU sequence model con split temporal, MC Dropout real, Monte Carlo vectorizado, pass networks, GCN manual en PyTorch y reporte final centralizado. Los modelos deep/GNN son iniciales y pueden quedar `experimental`, `candidate`, `champion` o `insufficient_data` según scorecard.

## Research dataset

No es el default. Úsalo para traer más partidos de StatsBomb Open Data de forma controlada:

```bash
python scripts/01_download_data.py --competition-id <id> --season-id <id> --max-matches 100
python scripts/01_download_data.py --research --max-matches 150 --skip-360
```

Puedes sobreescribir la raíz de datos con:

```bash
BUCEPHALUS_DATA_ROOT=/tmp/bucephalus-data python scripts/01_download_data.py --sample
```

## Outputs

- `data/raw/`: JSON crudo o fallback.
- `data/processed/`: Parquet normalizado, `data_manifest`, entidades maestras y DuckDB catalog.
- `data/features/`: `team_profiles_baseline` y features básicas trazables.
- `data/features/`: feature store Fase 4, rolling priors sin leakage y datasets de modelado.
- `outputs/eda/tables/`: tablas EDA reproducibles, incluido `fat_tail_summary`.
- `outputs/eda/figures/`: figuras ligeras.
- `outputs/quality/`: `data_quality_summary.json`.
- `outputs/models/`: registry de modelos baseline.
- `outputs/evaluation/`: métricas, predicciones, splits walk-forward y leakage check.
- `outputs/simulations/`: escenarios tácticos, simulaciones Monte Carlo y sensibilidad de sliders.
- `outputs/calibration/`: registry de parámetros, bootstrap uncertainty y reportes de calibración.
- `outputs/models/model_registry.json`: registry local de modelos/configuraciones.
- `outputs/models/*_model_registry.json`: registries de modelos Fase 8.
- `outputs/evaluation/hazard_metrics.json`, `sequence_model_metrics.json`, `possession_value_metrics.json`: métricas ML Fase 8.
- `outputs/evaluation/mc_dropout_summary.json`: incertidumbre por MC Dropout.
- `outputs/quality/vectorized_simulation_benchmark.json`: benchmark Monte Carlo vectorizado.
- `data/features/pass_network_*.parquet`: redes de pase por equipo-partido.
- `outputs/evaluation/gnn_metrics.json`: evaluación de GNN manual PyTorch.
- `outputs/evaluation/phase8_model_scorecard.*`: scorecard de modelos.
- `outputs/reports/phase8_results_summary.md`: resumen humano de Fase 8.
- `outputs/reports/final_model_audit_report.md`: auditoría final central con leakage, calibración, overfitting, scorecard y dictamen para Fase 9.
- `outputs/explainability/`: muestras de explicabilidad.
- `data/processed/ingestion_manifest.parquet`: manifest incremental por partido.
- `outputs/quality/incremental_feature_update_report.json`: reporte de actualización incremental.
- `outputs/quality/performance_benchmark.json`: benchmark ligero de pipeline.

## Siguiente etapa

La siguiente etapa son Fases 9-11: Game Mode, Lab Mode operativo, interfaz, reportes y asistente IA. Algunos componentes siguen siendo proxy o `heuristic_fallback` cuando no hay cobertura suficiente, pero el motor separa `heuristic` vs `calibrated`, usa anclas empíricas, Markov calibrado, incertidumbre vía bootstrap, team strength temporal, registry local y ML inicial trazable.
