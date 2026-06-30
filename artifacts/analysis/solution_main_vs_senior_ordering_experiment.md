# Solution Output Comparison

Local-only benchmark comparison. This is not part of the general ranker.

- Baseline: `/mnt/e/contextmatch/artifacts/analysis/solution_ranker_submission.csv`
- Experiment: `/mnt/e/contextmatch/artifacts/analysis/solution_senior_ordering_experiment.csv`
- Top-100 common: 100
- Spearman on common top-100: 1.0
- Mean absolute rank delta: 0.0
- Max absolute rank delta: 0

## Top-K Overlap

| K | Common |
| --- | --- |
| 10 | 10 |
| 20 | 20 |
| 30 | 30 |
| 50 | 50 |
| 100 | 100 |

## Experiment Archetypes

- Top 10: {'applied_ml': 4, 'senior_plain_language': 4, 'senior_explicit_ai': 2}
- Top 20: {'applied_ml': 11, 'senior_explicit_ai': 5, 'senior_plain_language': 4}
- Top 30: {'applied_ml': 18, 'senior_plain_language': 7, 'senior_explicit_ai': 5}
- Top 50: {'applied_ml': 38, 'senior_plain_language': 7, 'senior_explicit_ai': 5}
- Top 100: {'applied_ml': 79, 'senior_explicit_ai': 13, 'senior_plain_language': 8}

## Reference Overlaps

- reference_a: 71 common top-100 candidates
- reference_b: 84 common top-100 candidates
