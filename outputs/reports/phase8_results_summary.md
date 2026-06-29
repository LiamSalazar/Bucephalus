# Phase 8 Results Summary

Dataset: 52 matches, 191299 events, 1332 shots.

Models trained: xG v2 tabular, hazard, EPV, PyTorch GRU sequence, pass network GCN, MC Dropout, vectorized Monte Carlo.

Scorecard:
- xG: experimental (log_loss=0.383800111537472)
- hazard: champion (roc_auc=0.7222124199105082)
- EPV: experimental (mean_epv=0.056327305438857625)
- sequence: candidate (brier_score=0.21254341304302216)
- MC Dropout: experimental (mean_epistemic_uncertainty=0.04935392519459128)
- vectorized Monte Carlo: experimental (simulations_per_second=4810092.738867187)
- pass network: experimental (graphs=102)
- GNN: experimental (mae=0.7448492050170898)
- explainability: experimental (artifacts=1.0)

Limitations: small research dataset, pass receiver uses next-event proxy, no tracking-speed data, GNN remains experimental unless it improves baseline.

Recommendation for Phase 9: integrate these artifacts into Lab/Game Mode as calibrated candidates, not final champions.
