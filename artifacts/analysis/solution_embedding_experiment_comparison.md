# Solution Output Comparison

Local-only benchmark comparison. This is not part of the general ranker.

- Baseline: `/mnt/e/contextmatch/artifacts/analysis/solution_ranker_submission.csv`
- Experiment: `/mnt/e/contextmatch/artifacts/analysis/solution_embedding_experiment.csv`
- Top-100 common: 100
- Spearman on common top-100: 0.9901
- Mean absolute rank delta: 2.88
- Max absolute rank delta: 13

## Top-K Overlap

| K | Common |
| --- | --- |
| 10 | 8 |
| 20 | 18 |
| 30 | 28 |
| 50 | 47 |
| 100 | 100 |

## Experiment Archetypes

- Top 10: {'applied_ml': 4, 'senior_explicit_ai': 3, 'senior_plain_language': 3}
- Top 20: {'applied_ml': 10, 'senior_explicit_ai': 5, 'senior_plain_language': 5}
- Top 30: {'applied_ml': 19, 'senior_plain_language': 6, 'senior_explicit_ai': 5}
- Top 50: {'applied_ml': 38, 'senior_plain_language': 7, 'senior_explicit_ai': 5}
- Top 100: {'applied_ml': 79, 'senior_explicit_ai': 13, 'senior_plain_language': 8}

## Reference Overlaps

- reference_a: 71 common top-100 candidates
- reference_b: 84 common top-100 candidates
