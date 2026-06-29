# Bucephalus Final Model Audit Report

Generated at: 2026-06-29T00:48:15.290625+00:00

## 1. Executive Summary
Overall status: WARNING
Ready for Phase 9: YES WITH WARNINGS
Objective compliance: PARTIALLY

## 2. Dataset & Coverage
```json
{
  "manifest": {
    "generated_at": "2026-06-27T18:23:09.166136+00:00",
    "source_name": "StatsBomb Open Data",
    "source_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data",
    "mode": "fallback",
    "competitions": [
      999
    ],
    "seasons": [
      2024
    ],
    "max_matches": 150,
    "actual_matches_downloaded": 2,
    "has_events": true,
    "has_lineups": true,
    "has_360": true,
    "raw_files_count": 80,
    "processed_tables": [
      "carries",
      "competitions",
      "data_manifest",
      "duels",
      "events",
      "external_entity_links",
      "goalkeeper_actions",
      "lineups",
      "master_competitions",
      "master_matches",
      "master_players",
      "master_teams",
      "matches",
      "passes",
      "players",
      "pressures",
      "shots",
      "teams",
      "three_sixty"
    ],
    "rows_by_table": {
      "carries": 32371,
      "competitions": 80,
      "data_manifest": 1,
      "duels": 2024,
      "events": 137785,
      "external_entity_links": 10,
      "goalkeeper_actions": 1104,
      "lineups": 1363,
      "master_competitions": 1,
      "master_matches": 2,
      "master_players": 5,
      "master_teams": 2,
      "matches": 36,
      "passes": 39218,
      "players": 1571,
      "pressures": 11423,
      "shots": 922,
      "teams": 20,
      "three_sixty": 2
    },
    "pipeline_version": "0.1.0",
    "git_commit": "423a45d27049cda945a1c6f900170c9c608c9419",
    "warnings": [
      "<urlopen error [Errno -2] Name or service not known>"
    ],
    "errors": [],
    "checksums": {
      "data/raw/.gitkeep": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
      "data/raw/_download_metadata.json": "99129eaff6bc080ca75859b3e1650e290ab540d55e43f78f94660745bfdcb196",
      "data/raw/competitions.json": "db01377fcbf26abe73a397f649fa03fe685ba7e1fd70b239c9aa2b88f37d1146",
      "data/raw/events/3895052.json": "d97f595e49f4200e657269ff48b3fa662f8932205cfdf94b2ea4428829820d92",
      "data/raw/events/3895060.json": "9f4dc7040495e69fd3d11300647d41f04847763d11c44a1dc37fbe2e8786e132",
      "data/raw/events/3895067.json": "ff06444f03abc6b4ebe06ed6cf758c5216950b96739a83902a404c9f274632d6",
      "data/raw/events/3895074.json": "c51d0459bb33d946fd00f85e9e97e798021262ae2a852a6468da102840e8b976",
      "data/raw/events/3895086.json": "7b43416589687a078d83e3f02e9af4f4d33b5d6af1ea3d1529dc083bb34950ec",
      "data/raw/events/3895095.json": "a413c21ce17041af8f492a45cf9cfe1b0ea6d95206f91fae0b48167bf1598221",
      "data/raw/events/3895107.json": "8339a54c21d03690a7bccfd4c0f13bcab26cf24706b6f18a222b34e76feb9fe3",
      "data/raw/events/3895113.json": "f5afe518c7e486b8e626bfde2ca6ade79a60c3ba9dd367c7bc2a0bf71cb27ea6",
      "data/raw/events/3895121.json": "f125fe6fbb3ca5ccd1fd296a7a5490c1aadcd812cfd82ead2e98fc7776c7a1d2",
      "data/raw/events/3895134.json": "994b6e9e5bf571b69f47f8bc6f23b69e274f48a61a887d857daf980bb01107b4",
      "data/raw/events/3895139.json": "076e0cf3cd729e4c863b45f57d5c88e2e5933c84e7887e46791e5dab11891c3d",
      "data/raw/events/3895153.json": "496e2ca34f077bab6dfa5fada24ba9d2b27841881e0868a2f1fb390e4da3a55f",
      "data/raw/events/3895158.json": "e93ddab0c5b7bd18b40fd1198084e4ba0f52f5ce190adb6e61a4d8884735968f",
      "data/raw/events/3895167.json": "36db2b68ca1cb4f3da4f0045db4a12f73d76227177ea30834780510ef82436c3",
      "data/raw/events/3895180.json": "bb67014178bac7ab2664bca7157466cc650590610a2a6d31d70672350ccca8cb",
      "data/raw/events/3895182.json": "429fc4aba603d6137c28ab3bc523d3219f08ac91726122f143b48d80ad2d091e",
      "data/raw/events/3895194.json": "ed786b0c2a9480e624c7cc70604f2d2c8608687ceee6c7e2fa6f8c6cf0f0d637",
      "data/raw/events/3895202.json": "f841dd44a0f16cbe6b1f437a510f20fd8192f00000542a457dcea36c440c7afb",
      "data/raw/events/3895210.json": "be8d674d1a11a27dd2ab4e1dc099ee1016e5b275c6282109f03d48bee8a45edb",
      "data/raw/events/3895220.json": "a6d7e7f31a78d43cc3669fb1c0923d73280a4a62c0ae89b78110f54ca4d3f615",
      "data/raw/events/3895232.json": "98c7e930439e77a06daad441039a1fd94966ecbe441ac2dba1cd133fde3d554f",
      "data/raw/events/3895244.json": "2b8c554e7a6bdfd0e874ee2a66e3811e259f31417feb9592b2ef7b8d1b9bd2a4",
      "data/raw/events/3895250.json": "16b3e4d5665c44843ef996ed9ab7cd7f5ec9f7783d8cf32813845451ebc92a0d",
      "data/raw/events/3895258.json": "90478290e60b947dfda516c109e1481685426b8da264c78c252a9624ad4908d9",
      "data/raw/events/3895266.json": "443720db758b021d44a86b4e8feaf07d30d34ea5dc5148401b382c55a92e053d",
      "data/raw/events/3895275.json": "a2aa935e952622e47a91af50fd0f868708801f7482f977a14ee299dfaf68fdb9",
      "data/raw/events/3895286.json": "49f8926be7d2769463a9758daee42356695e8418d78492385f5d8dd9c5e40005",
      "data/raw/events/3895292.json": "ed0ee4380af172fe008c3ceff8019b1dd0d9458c3c092028bb9d28a8b7c6f406",
      "data/raw/events/3895302.json": "24b696d55270b67cfe5b8c4e36075ec1632e9f83c3bd5c12f1d108c895814859",
      "data/raw/events/3895309.json": "59259675bb95621acc1d6770de7e5e9a0831ca63eb899bef9cc306e9d7c168fd",
      "data/raw/events/3895320.json": "9c36deb964f12e13099a4dbf59767e08fa7231b98fd072a6a7979b8e91870f6c",
      "data/raw/events/3895333.json": "7151edf9364887077c0c0e357f9b25603dc38c569468d3e6afe9c209a5ff519a",
      "data/raw/events/3895340.json": "aaec8808be161884e8d1c184497e6548b5de95c0adf64219c83c9665abc72e04",
      "data/raw/events/3895348.json": "8034f3699ad0bc0f69c2165bed612e81737e9d2b3126174a241882b98f43186d",
      "data/raw/events/900001.json": "c69f454f8ba5966c6b5149db27833dbee9d9cf998d6742ffb531c04bb8a15a15",
      "data/raw/events/900002.json": "79b11a9f5e919a699020aca9beff5d0f9bb339a3653ff7134aae47a580388834",
      "data/raw/lineups/3895052.json": "ca891fb98e4e5f6dae4cc049ea547315ac9b9ad17324287b3534590001a03524",
      "data/raw/lineups/3895060.json": "dac989cd87777fb89ac51c0192c2d7641aa5500d7fa004f291bff76d821b0bee",
      "data/raw/lineups/3895067.json": "86dcce121d3bdf0dad
```

## 3. Pipeline Health
Artifacts checked: 33
Artifacts missing: 0

## 4. Leakage Audit
```json
{
  "generated_at": "2026-06-29T00:44:34.290979+00:00",
  "passed": true,
  "columns_audited": [
    "bucephalus_match_id",
    "statsbomb_match_id",
    "competition_id",
    "season_id",
    "match_date",
    "home_team_id",
    "away_team_id",
    "home_score",
    "away_score",
    "total_goals",
    "result_home_win",
    "result_draw",
    "result_away_win",
    "goal_difference",
    "available_event_rows",
    "has_xg",
    "has_pressure",
    "has_duels",
    "has_360",
    "bucephalus_team_id",
    "home_feature_cutoff_date",
    "home_historical_matches_available",
    "home_rolling_goals_for_3",
    "home_rolling_goals_for_5",
    "home_rolling_goals_for_10",
    "home_rolling_goals_against_3",
    "home_rolling_goals_against_5",
    "home_rolling_goals_against_10",
    "home_rolling_xg_for_3",
    "home_rolling_xg_for_5",
    "home_rolling_xg_for_10",
    "home_rolling_xg_against_3",
    "home_rolling_xg_against_5",
    "home_rolling_xg_against_10",
    "home_rolling_shots_for_3",
    "home_rolling_shots_for_5",
    "home_rolling_shots_for_10",
    "home_rolling_shots_against_3",
    "home_rolling_shots_against_5",
    "home_rolling_shots_against_10",
    "home_rolling_possession_proxy_3",
    "home_rolling_possession_proxy_5",
    "home_rolling_possession_proxy_10",
    "home_rolling_pressing_proxy_3",
    "home_rolling_pressing_proxy_5",
    "home_rolling_pressing_proxy_10",
    "home_rolling_directness_proxy_3",
    "home_rolling_directness_proxy_5",
    "home_rolling_directness_proxy_10",
    "home_rolling_transition_proxy_3",
    "home_rolling_transition_proxy_5",
    "home_rolling_transition_proxy_10",
    "home_rolling_goals_after_70_for_3",
    "home_rolling_goals_after_70_for_5",
    "home_rolling_goals_after_70_for_10",
    "home_rolling_goals_after_70_against_3",
    "home_rolling_goals_after_70_against_5",
    "home_rolling_goals_after_70_against_10",
    "team_goals_for_volatility",
    "team_goals_against_volatility",
    "team_xg_for_volatility",
    "team_xg_against_volatility",
    "team_shots_for_volatility",
    "team_shots_against_volatility",
    "team_possession_proxy_volatility",
    "team_pressing_proxy_volatility",
    "team_directness_proxy_volatility",
    "team_transition_proxy_volatility",
    "team_goals_after_70_for_volatility",
    "team_goals_after_70_against_volatility",
    "bucephalus_team_id_awayrow",
    "away_feature_cutoff_date",
    "away_historical_matches_available",
    "away_rolling_goals_for_3",
    "away_rolling_goals_for_5",
    "away_rolling_goals_for_10",
    "away_rolling_goals_against_3",
    "away_rolling_goals_against_5",
    "away_rolling_goals_against_10",
    "away_rolling_xg_for_3",
    "away_rolling_xg_for_5",
    "away_rolling_xg_for_10",
    "away_rolling_xg_against_3",
    "away_rolling_xg_against_5",
    "away_rolling_xg_against_10",
    "away_rolling_shots_for_3",
    "away_rolling_shots_for_5",
    "away_rolling_shots_for_10",
    "away_rolling_shots_against_3",
    "away_rolling_shots_against_5",
    "away_rolling_shots_against_10",
    "away_rolling_possession_proxy_3",
    "away_rolling_possession_proxy_5",
    "away_rolling_possession_proxy_10",
    "away_rolling_pressing_proxy_3",
    "away_rolling_pressing_proxy_5",
    "away_rolling_pressing_proxy_10",
    "away_rolling_directness_proxy_3",
    "away_rolling_directness_proxy_5",
    "away_rolling_directness_proxy_10",
    "away_rolling_transition_proxy_3",
    "away_rolling_transition_proxy_5",
    "away_rolling_transition_proxy_10",
    "away_rolling_goals_after_70_for_3",
    "away_rolling_goals_after_70_for_5",
    "away_rolling_goals_after_70_for_10",
    "away_rolling_goals_after_70_against_3",
    "away_rolling_goals_after_70_against_5",
    "away_rolling_goals_after_70_against_10",
    "team_goals_for_volatility_awayrow",
    "team_goals_against_volatility_awayrow",
    "team_xg_for_volatility_awayrow",
    "team_xg_against_volatility_awayrow",
    "team_shots_for_volatility_awayrow",
    "team_shots_against_volatility_awayrow",
    "team_possession_proxy_volatility_awayrow",
    "team_pressing_proxy_volatility_awayrow",
    "team_directness_proxy_volatility_awayrow",
    "team_transition_proxy_volatility_awayrow",
    "team_goals_after_70_for_volatility_awayrow",
    "team_goals_after_70_against_volatility_awayrow",
    "diff_rolling_goals_for_3",
    "diff_rolling_goals_for_5",
    "diff_rolling_goals_for_10",
    "diff_rolling_goals_against_3",
    "diff_rolling_goals_against_5",
    "diff_rolling_goals_against_10",
    "diff_rolling_xg_for_3",
    "diff_rolling_xg_for_5",
    "diff_rolling_xg_for_10",
    "diff_rolling_xg_against_3",
    "diff_rolling_xg_against_5",
    "diff_rolling_xg_against_10",
    "diff_rolling_shots_for_3",
    "diff_rolling_shots_for_5",
    "diff_rolling_shots_for_10",
    "diff_rolling_shots_against_3",
    "diff_rolling_shots_against_5",
    "diff_rolling_shots_against_10",
    "diff_rolling_possession_proxy_3",
    "diff_rolling_possession_proxy_5",
    "diff_rolling_possession_proxy_10",
    "diff_rolling_pressing_proxy_3",
    "diff_rolling_pressing_proxy_5",
    "diff_rolling_pressing_proxy_10",
    "diff_rolling_directness_proxy_3",
    "diff_rolling_directness_proxy_5",
    "diff_rolling_directness_proxy_10",
    "diff_rolling_transition_proxy_3",
    "diff_rolling_transition_proxy_5",
    "diff_rolling_transition_proxy_10",
    "diff_rolling_goals_after_70_for_3",
    "diff_rolling_goals_after_70_for_5",
    "diff_rolling_goals_after_70_for_10",
    "diff_rolling_goals_after_70_against_3",
    "diff_rolling_goals_after_70_against_5",
    "diff_rolling_goals_after_70_against_10",
    "target_match_date",
    "feature_cutoff_date",
    "feature_history_matches_available"
  ],
  "forbidden_columns_detected": [],
  "rolling_features_previous_only": true,
  "feature_timestamp_policy": "rolling features are generated before target match by construction",
  "split_dates": {
    "train": {
      "rows": 21,
      "mi
```

## 5. Model Scorecard
| Component | Status | Metric | Baseline | Advanced | Improvement % |
|---|---:|---:|---:|---:|---:|
| xG | experimental | log_loss | 0.3213323142669515 | 0.4061930560730603 | -26.40902829822756 |
| hazard | champion | roc_auc | 0.5 | 0.725123832413023 | 45.024766482604605 |
| EPV | candidate | mean_epv | None | 0.056780930018417115 | None |
| sequence | champion | brier_score | 0.213189872734494 | 0.20323404669761658 | 4.669933852475429 |
| MC Dropout | candidate | mean_epistemic_uncertainty | None | 0.05379996013827622 | None |
| vectorized Monte Carlo | candidate | simulations_per_second | None | 4594891.409108099 | None |
| pass network | candidate | graphs | None | 70 | None |
| GNN | experimental | mae | 0.6365463653262958 | 0.6758408546447754 | -6.173075750473743 |
| explainability | candidate | artifacts | None | 1.0 | None |

## 6. xG Model Results
```json
{
  "status": "trained",
  "rows": 922,
  "features": [
    "location_x",
    "location_y",
    "distance_to_goal",
    "angle_to_goal",
    "under_pressure_int",
    "shot_first_time_int",
    "shot_one_on_one_int",
    "shot_aerial_won_int",
    "set_piece_proxy",
    "shot_type_name__Free Kick",
    "shot_type_name__Open Play",
    "shot_type_name__Penalty",
    "play_pattern_name_clean__From Corner",
    "play_pattern_name_clean__From Counter",
    "play_pattern_name_clean__From Free Kick",
    "play_pattern_name_clean__From Goal Kick",
    "play_pattern_name_clean__From Keeper",
    "play_pattern_name_clean__From Kick Off",
    "play_pattern_name_clean__From Throw In",
    "play_pattern_name_clean__Other",
    "play_pattern_name_clean__Regular Play",
    "shot_body_part_name_clean__unknown"
  ],
  "log_loss": 0.3213323142669515,
  "brier_score": 0.0946199613261401,
  "roc_auc": 0.7696774193548387,
  "avg_predicted_xg": 0.1328276283925685,
  "actual_goal_rate": 0.1341991341991342,
  "baseline_global_log_loss": 0.39563023403469594
}
```

## 7. Hazard / Survival Model Results
```json
{
  "status": "trained",
  "rows": 132288,
  "positive_rate": 0.03118952588292211,
  "roc_auc": 0.725123832413023,
  "pr_auc": 0.07399455107984786,
  "brier_score": 0.213189872734494,
  "log_loss": 0.6168554983550255,
  "calibration_error": 0.3945439350801861,
  "horizon": "next_5_events_proxy",
  "hazard_time_mode": "event_horizon_proxy",
  "targets": [
    "shot_in_next_5_events",
    "turnover_in_next_5_events",
    "box_entry_in_next_5_events",
    "final_third_entry_in_next_5_events"
  ]
}
```

## 8. EPV Results
```json
{
  "generated_at": "2026-06-29T00:39:06.500373+00:00",
  "rows": 33072,
  "mean_epv": 0.056780930018417115,
  "survival_bias_guard": true,
  "alignment_keys": [
    "match_id",
    "possession",
    "team_id",
    "event_id",
    "event_index",
    "minute",
    "second"
  ],
  "xg_sources": [
    "event_context_proxy",
    "tabular_xg_v2_hgb"
  ],
  "hazard_source": "hazard_logistic_next_5_events"
}
```

## 9. Sequence Model Results
```json
{
  "status": "trained",
  "model_type": "pytorch_gru_sequence_model",
  "rows": 132288,
  "train_rows": 84019,
  "validation_rows": 26293,
  "test_rows": 21976,
  "log_loss": 0.6034179329872131,
  "brier_score": 0.20323404669761658,
  "roc_auc": 0.771775810436978,
  "pr_auc": 0.09414704212253568,
  "validation_brier_score": 0.25031381845474243,
  "positive_rate": 0.03118952549993992,
  "survival_bias_guard": true,
  "target_type": "shot_probability_sequence",
  "horizon_type": "event_horizon_proxy",
  "temporal_split": true
}
```

## 10. Overfitting Analysis
Overfitting risk: MEDIUM
Split-specific train/validation/test diagnostics are limited; temporal split metadata is used where available.

## 11. Calibration Analysis
Calibration status: POOR

## 12. Simulation Results
```json
{
  "generated_at": "2026-06-29T00:46:27.657803+00:00",
  "status": "evaluated",
  "walk_forward": true,
  "models": [
    "naive_baseline",
    "poisson_rolling",
    "empirical_anchor",
    "empirical_anchor_tactical",
    "empirical_anchor_markov",
    "full_calibrated_team_strength"
  ],
  "metrics": {
    "model": "full_calibrated_team_strength",
    "rows": 11,
    "mae_home_goals": 1.1727272727272728,
    "mae_away_goals": 0.7181818181818183,
    "rmse": 1.2555105806729858,
    "accuracy": 0.6363636363636364,
    "log_loss": 0.952628457040485,
    "brier_score": 0.5821590909090909,
    "expected_calibration_error": 0.15909090909090906,
    "interval_coverage": 0.7272727272727273,
    "total_goals_distribution_error": 1.468181818181818,
    "scoreline_distribution_error": 1.5681818181818181,
    "jensen_shannon_divergence": null
  },
  "rows": 66
}
```

## 13. Monte Carlo & Uncertainty
```json
{
  "vectorized": {
    "generated_at": "2026-06-29T00:40:16.622817+00:00",
    "n_simulations": 10000,
    "seconds": 0.0021763299955637194,
    "simulations_per_second": 4594891.409108099,
    "home_win_probability": 0.3018,
    "draw_probability": 0.415,
    "away_win_probability": 0.2832,
    "expected_home_goals": 0.6002,
    "expected_away_goals": 0.5761,
    "loop_expected_home_goals": 0.586,
    "loop_expected_away_goals": 0.566,
    "expected_goals_difference": 0.02429999999999999,
    "home_probability_difference": 0.013800000000000034,
    "draw_probability_difference": 0.029000000000000026,
    "away_probability_difference": 0.015199999999999991,
    "speedup_proxy_vs_loop_500": 9189.782818216197,
    "memory_estimate_mb": 0.24,
    "uncertainty_sources": [
      "data_uncertainty",
      "model_uncertainty",
      "parameter_uncertainty",
      "simulation_uncertainty",
      "tactical_parameter_uncertainty",
      "team_strength_uncertainty"
    ],
    "model_uncertainty_std": 0.15875,
    "parameter_uncertainty_std": 0.05,
    "simulation_uncertainty_std": 0.011240636948144887,
    "data_uncertainty_flag": true,
    "combined_interval": {
      "p5": -0.16681700878207834,
      "p50": 1.0,
      "p95": 3.166817008782078
    },
    "mode": "numpy_vectorized_empirical_anchor_poisson"
  },
  "uncertainty_sources": [
    "data_uncertainty",
    "model_uncertainty",
    "parameter_uncertainty",
    "simulation_uncertainty",
    "tactical_parameter_uncertainty",
    "team_strength_uncertainty"
  ]
}
```

## 14. Vectorized Simulation Benchmark
```json
{
  "generated_at": "2026-06-29T00:40:16.622817+00:00",
  "n_simulations": 10000,
  "seconds": 0.0021763299955637194,
  "simulations_per_second": 4594891.409108099,
  "home_win_probability": 0.3018,
  "draw_probability": 0.415,
  "away_win_probability": 0.2832,
  "expected_home_goals": 0.6002,
  "expected_away_goals": 0.5761,
  "loop_expected_home_goals": 0.586,
  "loop_expected_away_goals": 0.566,
  "expected_goals_difference": 0.02429999999999999,
  "home_probability_difference": 0.013800000000000034,
  "draw_probability_difference": 0.029000000000000026,
  "away_probability_difference": 0.015199999999999991,
  "speedup_proxy_vs_loop_500": 9189.782818216197,
  "memory_estimate_mb": 0.24,
  "uncertainty_sources": [
    "data_uncertainty",
    "model_uncertainty",
    "parameter_uncertainty",
    "simulation_uncertainty",
    "tactical_parameter_uncertainty",
    "team_strength_uncertainty"
  ],
  "model_uncertainty_std": 0.15875,
  "parameter_uncertainty_std": 0.05,
  "simulation_uncertainty_std": 0.011240636948144887,
  "data_uncertainty_flag": true,
  "combined_interval": {
    "p5": -0.16681700878207834,
    "p50": 1.0,
    "p95": 3.166817008782078
  },
  "mode": "numpy_vectorized_empirical_anchor_poisson"
}
```

## 15. Pass Network & GNN Results
Does the GNN add value beyond graph metrics? NO
```json
{
  "gnn_metrics": {
    "rows": 18,
    "target": "xg_for",
    "baseline_mae": 0.9771673679351807,
    "tabular_graph_mae": 0.6365463653262958,
    "gnn_mae": 0.6758408546447754,
    "no_edge_mae": 0.674917459487915,
    "permuted_edge_mae": 0.6846455335617065,
    "gnn_rmse": 0.945137795942766,
    "permuted_edges_sanity": "passed",
    "status": "candidate"
  },
  "gnn_validation": {
    "generated_at": "2026-06-29T00:40:27.719996+00:00",
    "target": "xg_for",
    "real_adjacency_mae": 0.6758408546447754,
    "no_edge_mae": 0.674917459487915,
    "permuted_edge_mae": 0.6846455335617065,
    "tabular_graph_mae": 0.6365463653262958,
    "within_graph_edge_shuffle": "approximated_by_permuted_edges",
    "random_labels_mae": 1.0970515012741089,
    "random_labels_test": "passed",
    "overfit_small_batch_test": "passed",
    "does_gnn_add_value_beyond_graph_metrics": "NO",
    "warnings": [
      "small graph validation set; status should be interpreted cautiously"
    ]
  }
}
```

## 16. Explainability Results
Explainability artifacts present: 4/4
Methods include permutation importance and local occlusion where model artifacts exist.

## 17. Model Registry & Reproducibility
```json
{
  "generated_at": "2026-06-29T00:47:13.040804+00:00",
  "models": [
    {
      "model_id": "baseline_models_v0",
      "model_type": "baseline_models",
      "created_at": "2026-06-29T00:47:13.036063+00:00",
      "training_data_hash": "83ef0e18e59d6aae5bd5e160a913e0902cff03e488b18508638bdc1c35d40efe",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "models": [
          {
            "model_name": "poisson_rolling",
            "rows": 8,
            "mae_home_goals": 0.8869047619047619,
            "mae_away_goals": 1.2476190476190476,
            "rmse_goals": 1.4125374997530566,
            "mean_predicted_home_goals": 1.500595238095238,
            "mean_actual_home_goals": 1.625,
            "mean_predicted_away_goals": 1.5101190476190476,
            "mean_actual_away_goals": 2.0,
            "accuracy": 0.75,
            "log_loss": 0.6449779705458937,
            "brier_score": 0.3866650292946047
          },
          {
            "model_name": "naive_prior",
            "rows": 8,
            "mae_home_goals": 1.125,
            "mae_away_goals": 1.3452380952380953,
            "rmse_goals": 1.7242189069263414,
            "mean_predicted_home_goals": 1.9047619047619047,
            "mean_actual_home_goals": 1.625,
            "mean_predicted_away_goals": 1.380952380952381,
            "mean_actual_away_goals": 2.0,
            "accuracy": 0.375,
            "log_loss": 1.1152297167566836,
            "brier_score": 0.6812857031386241
          }
        ]
      },
      "artifact_path": "/home/liam/Bucephalus/outputs/models/baseline_registry.json",
      "status": "candidate",
      "rollback_from": null,
      "notes": "local lightweight registry; no external tracking server"
    },
    {
      "model_id": "xg_model_v0",
      "model_type": "xg_model",
      "created_at": "2026-06-29T00:47:13.037517+00:00",
      "training_data_hash": "ba3043ec6ef6f94530771ef1da03f73f932c64bee2cb6352bcdd40355deabcab",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "status": "trained",
        "rows": 922,
        "features": [
          "location_x",
          "location_y",
          "distance_to_goal",
          "angle_to_goal",
          "under_pressure_int",
          "shot_first_time_int",
          "shot_one_on_one_int",
          "shot_aerial_won_int",
          "set_piece_proxy",
          "shot_type_name__Free Kick",
          "shot_type_name__Open Play",
          "shot_type_name__Penalty",
          "play_pattern_name_clean__From Corner",
          "play_pattern_name_clean__From Counter",
          "play_pattern_name_clean__From Free Kick",
          "play_pattern_name_clean__From Goal Kick",
          "play_pattern_name_clean__From Keeper",
          "play_pattern_name_clean__From Kick Off",
          "play_pattern_name_clean__From Throw In",
          "play_pattern_name_clean__Other",
          "play_pattern_name_clean__Regular Play",
          "shot_body_part_name_clean__unknown"
        ],
        "log_loss": 0.3213323142669515,
        "brier_score": 0.0946199613261401,
        "roc_auc": 0.7696774193548387,
        "avg_predicted_xg": 0.1328276283925685,
        "actual_goal_rate": 0.1341991341991342,
        "baseline_global_log_loss": 0.39563023403469594
      },
      "artifact_path": "/home/liam/Bucephalus/outputs/models/xg_model_registry.json",
      "status": "candidate",
      "rollback_from": null,
      "notes": "local lightweight registry; no external tracking server"
    },
    {
      "model_id": "team_strength_v0",
      "model_type": "team_strength",
      "created_at": "2026-06-29T00:47:13.038504+00:00",
      "training_data_hash": "7aa75305b0ca79c3f399bf30c6016583129fd2cd6ff127ce5cb7692db6502677",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "generated_at": "2026-06-29T00:46:14.765538+00:00",
        "rows": 72,
        "mean_absolute_goal_error_per_team_match": 2.0880590164849266,
        "uses_pre_match_state": true
      },
      "artifact_path": "/home/liam/Bucephalus/outputs/models/team_strength_registry.json",
      "status": "candidate",
      "rollback_from": null,
      "notes": "local lightweight registry; no external tracking server"
    },
    {
      "model_id": "markov_matrix_v0",
      "model_type": "markov_matrix",
      "created_at": "2026-06-29T00:47:13.039354+00:00",
      "training_data_hash": "b9af648b971f7aa2a8368786e9ab44c6785270bb1a8a7ced6615b6a7fe996d47",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "generated_at": "2026-06-29T00:46:14.756121+00:00",
        "status": "calibrated",
        "events": 137785,
        "states": [
          "OWN_THIRD",
          "BUILD_UP",
          "MIDDLE_THIRD",
          "FINAL_THIRD",
          "BOX",
          "SHOT",
          "GOAL",
          "TURNOVER",
          "COUNTER_ATTACK",
          "SET_PIECE",
          "END_POSSESSION"
        ],
        "rows_sum_to_one": true,
        "transition_counts": 137785,
        "warnings": [
          "by-style matrix omitted unless style coverage is sufficient"
        ]
      },
      "artifact_path": "/home/liam/Bucephalus/data/features/markov_transition_matrix_global.parquet",
      "status": "candidate",
      "rollback_from": null,
      "notes": "local lightweight registry; no external tracking server"
    },
    {
      "model_id": "calibrated_simulation_config_v0",
      "model_type": "calibrated_simulation_config",
      "created_at": "2026-06-29T00:47:13.040055+00:00",
      "training_data_hash": "c2ebe3d1ede44f0fa453e0030049aa1556d8b9dca23c4c363fa48ea5dc23a2cb",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metric
```

## 18. Performance & Scalability
```json
{
  "generated_at": "2026-06-29T00:46:27.668909+00:00",
  "timings": [
    {
      "step": "feature_build",
      "seconds": 0.5144
    },
    {
      "step": "xg_training",
      "seconds": 0.418
    },
    {
      "step": "markov_calibration",
      "seconds": 3.7394
    },
    {
      "step": "team_strength",
      "seconds": 0.0079
    },
    {
      "step": "bootstrap_tactical",
      "seconds": 0.0238
    },
    {
      "step": "simulation_backtest",
      "seconds": 12.8742
    }
  ],
  "row_counts": {
    "events": 137785,
    "team_match_features": 72,
    "model_dataset_matches": 36
  },
  "memory_note": "memory is not sampled in this lightweight benchmark"
}
```

## 19. Objective Compliance
Does the current system satisfy the objective of being a serious data-driven football simulation engine?
PARTIALLY
Can we move to Phase 9?
YES, WITH WARNINGS

## 20. Action Items
- Expand research dataset before promoting experimental Deep Learning components.
- Keep hazard and xG baselines as benchmarks for every future advanced model.
- Replace pass receiver proxy when provider data includes reliable recipient IDs.
- Add richer split diagnostics for overfitting analysis in larger datasets.
