# Bucephalus

Bucephalus es la base de un motor de simulación futbolística basado en datos reales. El objetivo final es soportar Game Mode y Lab Mode, pero este repositorio todavía está en Fases 1-3: fundación de datos, entity resolution y EDA inicial. La prioridad actual es reproducibilidad, trazabilidad, Parquet eficiente y validaciones ligeras. No hay frontend, backend API, simulador, mercado, modelos predictivos pesados ni Deep Learning.

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

## Research dataset

No es el default. Úsalo para traer más partidos de StatsBomb Open Data de forma controlada:

```bash
python scripts/01_download_data.py --competition-id <id> --season-id <id> --max-matches 100
```

Puedes sobreescribir la raíz de datos con:

```bash
BUCEPHALUS_DATA_ROOT=/tmp/bucephalus-data python scripts/01_download_data.py --sample
```

## Outputs

- `data/raw/`: JSON crudo o fallback.
- `data/processed/`: Parquet normalizado, `data_manifest`, entidades maestras y DuckDB catalog.
- `data/features/`: `team_profiles_baseline` y features básicas trazables.
- `outputs/eda/tables/`: tablas EDA reproducibles, incluido `fat_tail_summary`.
- `outputs/eda/figures/`: figuras ligeras.
- `outputs/quality/`: `data_quality_summary.json`.

## Siguiente etapa

Fase 4 debe construir un feature store más serio sobre esta base. Fase 5 debe agregar modelos baseline ligeros. El motor táctico, simulación Monte Carlo/Markov, ML/DL, Game Mode, Lab Mode e interfaz quedan fuera de esta etapa.
