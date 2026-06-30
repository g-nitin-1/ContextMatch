# Solution Output Comparison

Local-only benchmark comparison. This is not part of the general ranker.

- Baseline: `/mnt/e/contextmatch/artifacts/analysis/solution_ranker_submission.csv`
- Experiment: `/mnt/e/contextmatch/artifacts/analysis/solution_role_title_ordering_experiment.csv`
- Top-100 common: 100
- Spearman on common top-100: 0.9723
- Mean absolute rank delta: 4.24
- Max absolute rank delta: 33

## Top-K Overlap

| K | Common |
| --- | --- |
| 10 | 9 |
| 20 | 16 |
| 30 | 27 |
| 50 | 46 |
| 100 | 100 |

## Experiment Archetypes

- Top 10: {'senior_plain_language': 4, 'senior_explicit_ai': 3, 'applied_ml': 3}
- Top 20: {'applied_ml': 8, 'senior_plain_language': 7, 'senior_explicit_ai': 5}
- Top 30: {'applied_ml': 17, 'senior_plain_language': 7, 'senior_explicit_ai': 6}
- Top 50: {'applied_ml': 36, 'senior_explicit_ai': 7, 'senior_plain_language': 7}
- Top 100: {'applied_ml': 79, 'senior_explicit_ai': 13, 'senior_plain_language': 8}

## Reference Overlaps

- reference_a: 71 common top-100 candidates
- reference_b: 84 common top-100 candidates
