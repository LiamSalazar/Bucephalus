# Bucephalus

Motor de simulación futbolística basado en datos reales. Esta etapa implementa solo fundación de datos, entity resolution y EDA inicial.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Pipeline sample

```bash
python scripts/01_download_data.py --sample
python scripts/02_process_raw_to_parquet.py
python scripts/03_build_master_entities.py
python scripts/04_run_eda.py
pytest
```

## Estructura

- `src/bucephalus/data`: descarga, carga, procesamiento, entidades y validación.
- `src/bucephalus/features`: features básicas trazables.
- `src/bucephalus/eda`: distribuciones, estabilidad y colas.
- `data/raw`: JSON crudo StatsBomb o fallback.
- `data/processed`: Parquet normalizado y entidades maestras.
- `data/features`: tablas exploratorias para fases futuras.
- `outputs/eda`: tablas y figuras de EDA.

## Alcance actual

Incluye pipeline idempotente con sample pequeño y fallback sin internet. No incluye frontend, backend, juego, simulador avanzado ni modelos pesados.
