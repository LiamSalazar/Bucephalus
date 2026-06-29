# Bucephalus Final Model Audit Report

Generated at: 2026-06-29T02:39:42.668970+00:00

## 1. Executive Summary
Overall status: WARNING
Ready for Phase 9: YES WITH WARNINGS
Objective compliance: PARTIALLY

## 2. Dataset & Coverage
```json
{
  "manifest": {
    "generated_at": "2026-06-29T02:31:43.682346+00:00",
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
    "raw_files_count": 112,
    "processed_tables": [
      "carries",
      "competitions",
      "data_manifest",
      "duels",
      "events",
      "external_entity_links",
      "goalkeeper_actions",
      "ingestion_manifest",
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
      "carries": 42489,
      "competitions": 80,
      "data_manifest": 1,
      "duels": 3519,
      "events": 191299,
      "external_entity_links": 601,
      "goalkeeper_actions": 1613,
      "ingestion_manifest": 36,
      "lineups": 1933,
      "master_competitions": 80,
      "master_matches": 36,
      "master_players": 465,
      "master_teams": 20,
      "matches": 52,
      "passes": 53643,
      "players": 2379,
      "pressures": 17088,
      "shots": 1332,
      "teams": 25,
      "three_sixty": 2
    },
    "pipeline_version": "0.1.0",
    "git_commit": "dad4c15b9755f814315865a5d29deb43bcffddb4",
    "warnings": [
      "<urlopen error [Errno -2] Name or service not known>"
    ],
    "errors": [],
    "checksums": {
      "data/raw/.gitkeep": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
      "data/raw/_download_metadata.json": "99129eaff6bc080ca75859b3e1650e290ab540d55e43f78f94660745bfdcb196",
      "data/raw/competitions.json": "db01377fcbf26abe73a397f649fa03fe685ba7e1fd70b239c9aa2b88f37d1146",
      "data/raw/events/3890427.json": "32deecd0d98196f9307861829844016d5fe34251784507ec25756c909b5b38d4",
      "data/raw/events/3890431.json": "24270905fa2dba5b358f7de35d7b731e914cf906dc19e64208c8b43c2d692ad2",
      "data/raw/events/3890444.json": "9a63d2c3161493feaef3183abf84af66a617b7933651ce71cb2d6bf14328c79e",
      "data/raw/events/3890456.json": "c3cc9c040c053f4b727f7c6df9272c67068d7b1909532858eae5d9618141911d",
      "data/raw/events/3890463.json": "7e6e4d3b48500acc8a26611779903310c59e942d0982b57e75124915efdbac1e",
      "data/raw/events/3890472.json": "1db9e9964aafa161578a148d977f5b36a44b6a4103e45271f8aa1452b7242861",
      "data/raw/events/3890477.json": "94c5fc23845a7c33e7f07964e2905d3f51d16658394d5b080cd74146cd8e06e7",
      "data/raw/events/3890492.json": "f9e3fa6fa98979c4e3f13b3d420dede297cae3e9d9f6a5780e4e751ba735976c",
      "data/raw/events/3890500.json": "224705695df91512ada5fc3d478ab966b8e90520f609a73357d2734a611a8212",
      "data/raw/events/3890502.json": "921104a5c2afd65b81a8ae9b6359989bd5b9719b1b5756d8b9a7dfbaab3c7596",
      "data/raw/events/3890519.json": "ef38f74cd9772b642fbac3d3d8d013c8bf66601937da0eeb669f98dde67d482b",
      "data/raw/events/3890521.json": "5d4cde57cb971be23c36f6088ab2f2afa16161467491147f54f29b4610223947",
      "data/raw/events/3890534.json": "ea941539967ba5730167fb618244c384a6606c712f09a7f04e860f196056822e",
      "data/raw/events/3890540.json": "709b257cf50e68d2a6bd8b4efde52706d589cb900709f358f966d4e99a1c0e1b",
      "data/raw/events/3890550.json": "7c28ffad2ec82158bc2cb5b08e1fe8a479d9f4bd990e88ed79aa567d49768347",
      "data/raw/events/3890563.json": "9d8ac226bd1d139f40f8b1ffcd356ce308070868e56afc079d08d9cd92912b8c",
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
      "data/raw/events/3895244.json": "2b8c554e7a6bdfd0e874ee2a66e3811e259f31417feb9592b2ef7b8d1
```

## 3. Pipeline Health
Artifacts checked: 33
Artifacts missing: 0

## 4. Leakage Audit
```json
{
  "generated_at": "2026-06-29T02:33:40.081737+00:00",
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
      "rows": 31,
      "mi
```

## 5. Model Scorecard
| Component | Status | Metric | Baseline | Advanced | Improvement % |
|---|---:|---:|---:|---:|---:|
| xG | experimental | log_loss | 0.30948087165085747 | 0.383800111537472 | -24.014162649269707 |
| hazard | champion | roc_auc | 0.5 | 0.7222124199105082 | 44.44248398210164 |
| EPV | experimental | mean_epv | None | 0.056327305438857625 | None |
| sequence | candidate | brier_score | 0.21881605251218805 | 0.21254341304302216 | 2.866626738372639 |
| MC Dropout | experimental | mean_epistemic_uncertainty | None | 0.04935392519459128 | None |
| vectorized Monte Carlo | experimental | simulations_per_second | None | 4810092.738867187 | None |
| pass network | experimental | graphs | None | 102 | None |
| GNN | experimental | mae | 0.6386937499046326 | 0.7448492050170898 | -16.62071299872717 |
| explainability | experimental | artifacts | None | 1.0 | None |

## 6. xG Model Results
```json
{
  "status": "trained",
  "rows": 1332,
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
    "shot_type_name__Corner",
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
  "log_loss": 0.30948087165085747,
  "brier_score": 0.0885208865216806,
  "roc_auc": 0.755429335115269,
  "avg_predicted_xg": 0.12212291418853818,
  "actual_goal_rate": 0.12312312312312312,
  "baseline_global_log_loss": 0.3733368915262795
}
```

## 7. Hazard / Survival Model Results
```json
{
  "status": "trained",
  "rows": 182560,
  "positive_rate": 0.03214833479404031,
  "roc_auc": 0.7222124199105082,
  "pr_auc": 0.07111621174491091,
  "brier_score": 0.21881605251218805,
  "log_loss": 0.6282061289495213,
  "calibration_error": 0.40709273168708404,
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
  "generated_at": "2026-06-29T02:36:34.459075+00:00",
  "rows": 45640,
  "mean_epv": 0.056327305438857625,
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
  "rows": 182560,
  "train_rows": 109893,
  "validation_rows": 39520,
  "test_rows": 33147,
  "log_loss": 0.6266864538192749,
  "brier_score": 0.21254341304302216,
  "roc_auc": 0.7555339039390919,
  "pr_auc": 0.08307581624962895,
  "validation_brier_score": 0.2310958057641983,
  "positive_rate": 0.0321483351290226,
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
  "generated_at": "2026-06-29T02:35:42.746609+00:00",
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
    "rows": 13,
    "mae_home_goals": 1.271153846153846,
    "mae_away_goals": 0.7865384615384616,
    "rmse": 1.3564837178982565,
    "accuracy": 0.6923076923076923,
    "log_loss": 0.8188152932634699,
    "brier_score": 0.48576923076923073,
    "expected_calibration_error": 0.22115384615384615,
    "interval_coverage": 0.8461538461538461,
    "total_goals_distribution_error": 1.2076923076923078,
    "scoreline_distribution_error": 1.6000000000000003,
    "jensen_shannon_divergence": null
  },
  "rows": 78
}
```

## 13. Monte Carlo & Uncertainty
```json
{
  "vectorized": {
    "generated_at": "2026-06-29T02:38:01.723315+00:00",
    "n_simulations": 10000,
    "seconds": 0.002078961995721329,
    "simulations_per_second": 4810092.738867187,
    "home_win_probability": 0.2804,
    "draw_probability": 0.4149,
    "away_win_probability": 0.3047,
    "expected_home_goals": 0.5739,
    "expected_away_goals": 0.6204,
    "loop_expected_home_goals": 0.556,
    "loop_expected_away_goals": 0.608,
    "expected_goals_difference": 0.030299999999999883,
    "home_probability_difference": 0.02839999999999998,
    "draw_probability_difference": 0.027100000000000013,
    "away_probability_difference": 0.0012999999999999678,
    "speedup_proxy_vs_loop_500": 9620.185477734374,
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
    "simulation_uncertainty_std": 0.011339037657579234,
    "data_uncertainty_flag": true,
    "combined_interval": {
      "p5": -0.16682366820987962,
      "p50": 1.0,
      "p95": 3.16682366820988
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
  "generated_at": "2026-06-29T02:38:01.723315+00:00",
  "n_simulations": 10000,
  "seconds": 0.002078961995721329,
  "simulations_per_second": 4810092.738867187,
  "home_win_probability": 0.2804,
  "draw_probability": 0.4149,
  "away_win_probability": 0.3047,
  "expected_home_goals": 0.5739,
  "expected_away_goals": 0.6204,
  "loop_expected_home_goals": 0.556,
  "loop_expected_away_goals": 0.608,
  "expected_goals_difference": 0.030299999999999883,
  "home_probability_difference": 0.02839999999999998,
  "draw_probability_difference": 0.027100000000000013,
  "away_probability_difference": 0.0012999999999999678,
  "speedup_proxy_vs_loop_500": 9620.185477734374,
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
  "simulation_uncertainty_std": 0.011339037657579234,
  "data_uncertainty_flag": true,
  "combined_interval": {
    "p5": -0.16682366820987962,
    "p50": 1.0,
    "p95": 3.16682366820988
  },
  "mode": "numpy_vectorized_empirical_anchor_poisson"
}
```

## 15. Pass Network & GNN Results
Does the GNN add value beyond graph metrics? NO
```json
{
  "gnn_metrics": {
    "rows": 26,
    "target": "xg_for",
    "baseline_mae": 0.7910627126693726,
    "tabular_graph_mae": 0.7290857168785101,
    "gnn_mae": 0.7448492050170898,
    "no_edge_mae": 0.733526349067688,
    "permuted_edge_mae": 0.6386937499046326,
    "gnn_rmse": 0.9097253327805886,
    "permuted_edges_sanity": "passed",
    "status": "experimental"
  },
  "gnn_validation": {
    "generated_at": "2026-06-29T02:39:35.379297+00:00",
    "target": "xg_for",
    "real_adjacency_mae": 0.7448492050170898,
    "no_edge_mae": 0.733526349067688,
    "permuted_edge_mae": 0.6386937499046326,
    "tabular_graph_mae": 0.7290857168785101,
    "within_graph_edge_shuffle": "approximated_by_permuted_edges",
    "random_labels_mae": 1.0813417434692383,
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
  "generated_at": "2026-06-29T02:39:01.036246+00:00",
  "models": [
    {
      "model_id": "baseline_models_v0",
      "model_type": "baseline_models",
      "created_at": "2026-06-29T02:39:01.033134+00:00",
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
      "created_at": "2026-06-29T02:39:01.034048+00:00",
      "training_data_hash": "1c011160a33e3a4febb93c42987a34d9c7eef446612a5c2af56247e7afd9c912",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "status": "trained",
        "rows": 1332,
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
          "shot_type_name__Corner",
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
        "log_loss": 0.30948087165085747,
        "brier_score": 0.0885208865216806,
        "roc_auc": 0.755429335115269,
        "avg_predicted_xg": 0.12212291418853818,
        "actual_goal_rate": 0.12312312312312312,
        "baseline_global_log_loss": 0.3733368915262795
      },
      "artifact_path": "/home/liam/Bucephalus/outputs/models/xg_model_registry.json",
      "status": "candidate",
      "rollback_from": null,
      "notes": "local lightweight registry; no external tracking server"
    },
    {
      "model_id": "team_strength_v0",
      "model_type": "team_strength",
      "created_at": "2026-06-29T02:39:01.034689+00:00",
      "training_data_hash": "606b31af46d1cacd4f5bc3d24c1f5467671835c557dcaf97e6a1a4aab298e588",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "generated_at": "2026-06-29T02:35:28.015114+00:00",
        "rows": 104,
        "mean_absolute_goal_error_per_team_match": 2.1235423990949824,
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
      "created_at": "2026-06-29T02:39:01.035184+00:00",
      "training_data_hash": "587ff184c4884acb0317e93ff343e65f81be8812ae9076b71a935c8210accf7d",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "validation_period": null,
      "metrics": {
        "generated_at": "2026-06-29T02:35:28.003939+00:00",
        "status": "calibrated",
        "events": 191299,
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
        "transition_counts": 191299,
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
      "created_at": "2026-06-29T02:39:01.035718+00:00",
      "training_data_hash": "7069fdb70b878cfe74bda56333250b5ad4257d5436556bb29d3ee6d2d3737c08",
      "feature_set_version": "feature_store_v0",
      "train_period": null,
      "
```

## 18. Performance & Scalability
```json
{
  "generated_at": "2026-06-29T02:35:42.756911+00:00",
  "timings": [
    {
      "step": "feature_build",
      "seconds": 0.5367
    },
    {
      "step": "xg_training",
      "seconds": 0.4155
    },
    {
      "step": "markov_calibration",
      "seconds": 5.1559
    },
    {
      "step": "team_strength",
      "seconds": 0.0098
    },
    {
      "step": "bootstrap_tactical",
      "seconds": 0.0215
    },
    {
      "step": "simulation_backtest",
      "seconds": 14.7153
    }
  ],
  "row_counts": {
    "events": 191299,
    "team_match_features": 104,
    "model_dataset_matches": 52
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
