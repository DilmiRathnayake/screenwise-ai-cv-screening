# Model 2 — IT Candidate Ranking Evaluation Report

**Generated:** 2026-09-16T14:19:48Z (UTC)
**Eval split:** test only (1416 job–candidate pairs, 101 jobs)

## Methodology

- Features engineered from **raw** job/candidate fields (not pre-computed match components).
- LightGBM **LambdaMART** ranker grouped by `job_id`.
- Baseline: **required skill overlap** ratio only (no ML).
- Test jobs were never seen during training or hyperparameter tuning.

## Test-set metrics

| Metric | ML model | Skill-overlap baseline |
|--------|----------|------------------------|
| top1_accuracy | 1.0 | 0.4455 |
| ndcg_at_5 | 1.0 | 0.9761 |
| ndcg_at_10 | 1.0 | 0.9832 |
| mrr | 1.0 | 1.0 |
| precision_at_5 | 0.8653 | 0.8376 |
| recall_at_5 | 0.8023 | 0.7755 |
| spearman | 0.9138 | 0.9032 |
| kendall_tau | 0.7923 | 0.7973 |

**NDCG@5 delta (ML − baseline):** +0.0239

## Selected hyperparameters

```json
{
  "num_leaves": 63,
  "learning_rate": 0.15,
  "n_estimators": 200,
  "min_child_samples": 20,
  "best_iteration": 142
}
```

## Interpretation

The ML ranker recovers most of the synthetic rubric on held-out jobs. This validates pipeline integrity; real recruiter alignment is still unknown.

## Limitations

- Ground truth is a fixed synthetic rubric, not observed hiring decisions.
- Template-generated text may limit embedding utility.
- Metrics measure agreement with the dataset scoring formula, not real-world hiring accuracy.
