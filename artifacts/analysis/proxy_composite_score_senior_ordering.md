# Proxy Composite Score

Local proxy-only estimate. This is not an official score.

- Submission: `/mnt/e/contextmatch/artifacts/analysis/solution_senior_ordering_experiment.csv`
- Formula: `0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP@100 + 0.05*P@10`

| Truth assumption | Gain | NDCG@10 | NDCG@50 | MAP@100 | P@10 | Composite |
| --- | --- | --- | --- | --- | --- | --- |
| idea1_top100_truth__graded_by_idea2_tiers | exp | 0.627 | 0.642 | 0.575 | 1.000 | 0.642 |
| idea1_top100_truth__graded_by_idea2_tiers | linear | 0.833 | 0.734 | 0.575 | 1.000 | 0.773 |
| idea2_full_tiers_truth | exp | 0.627 | 0.665 | 1.000 | 1.000 | 0.713 |
| idea2_full_tiers_truth | linear | 0.833 | 0.866 | 1.000 | 1.000 | 0.877 |
| idea2_top100_truth__graded_by_idea2_tiers | exp | 0.627 | 0.684 | 0.746 | 1.000 | 0.680 |
| idea2_top100_truth__graded_by_idea2_tiers | linear | 0.833 | 0.803 | 0.746 | 1.000 | 0.820 |
