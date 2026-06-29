# Phase 8 Results Summary

Dataset: 36 matches, 137785 events, 922 shots.

Models trained: xG v2 tabular, hazard, EPV, PyTorch GRU sequence, pass network GCN, MC Dropout, vectorized Monte Carlo.

Scorecard:
- xG: experimental (log_loss=0.4061930560730603)
- hazard: champion (roc_auc=0.725123832413023)
- EPV: candidate (mean_epv=0.056780930018417115)
- sequence: champion (brier_score=0.20323404669761658)
- MC Dropout: candidate (mean_epistemic_uncertainty=0.05379996013827622)
- vectorized Monte Carlo: candidate (simulations_per_second=4594891.409108099)
- pass network: candidate (graphs=70)
- GNN: experimental (mae=0.6758408546447754)
- explainability: candidate (artifacts=1.0)

Limitations: small research dataset, pass receiver uses next-event proxy, no tracking-speed data, GNN remains experimental unless it improves baseline.

Recommendation for Phase 9: integrate these artifacts into Lab/Game Mode as calibrated candidates, not final champions.
