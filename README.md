# Bucephalus

Bucephalus es la base de un motor de simulación futbolística basado en datos reales. El objetivo final es soportar Game Mode y Lab Mode, pero este repositorio llega hasta Fase 7.5: datos, entity resolution, EDA, feature store, modelos baseline, motor táctico, simulación Monte Carlo/Markov y hardening científico/calibración. La prioridad actual es reproducibilidad, trazabilidad, Parquet/DuckDB eficiente, validación temporal sin leakage, calibración empírica y explicabilidad táctica. No hay frontend, backend API productivo, mercado, modelos avanzados ni Deep Learning.

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

## Scientific Hardening 7.5

```bash
make calibration-registry
make leakage-audit
make train-xg
make evaluate-xg
make calibrate-markov
make validate-simulation
make ablation
make phase-7-5-check
```

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
- `outputs/calibration/`: registry de parámetros y reportes de calibración.

## Siguiente etapa

La siguiente etapa es Fase 8: ML avanzado y Deep Learning. Algunos componentes siguen siendo proxy o heuristic fallback cuando no hay cobertura suficiente, pero el motor ya separa `heuristic` vs `calibrated` y registra sus fuentes.
