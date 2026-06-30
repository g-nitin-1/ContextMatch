# Proxy Composite Score

Local proxy-only estimate. This is not an official score.

- Submission: `/mnt/e/contextmatch/artifacts/analysis/solution_ranker_submission.csv`
- Formula: `0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP@100 + 0.05*P@10`

| Truth assumption | Gain | NDCG@10 | NDCG@50 | MAP@100 | P@10 | Composite |
| --- | --- | --- | --- | --- | --- | --- |
| idea1_top100_truth__graded_by_idea2_tiers | exp | 0.780 | 0.739 | 0.576 | 1.000 | 0.748 |
| idea1_top100_truth__graded_by_idea2_tiers | linear | 0.909 | 0.780 | 0.576 | 1.000 | 0.825 |
| idea2_full_tiers_truth | exp | 0.780 | 0.747 | 1.000 | 1.000 | 0.814 |
| idea2_full_tiers_truth | linear | 0.909 | 0.901 | 1.000 | 1.000 | 0.925 |
| idea2_top100_truth__graded_by_idea2_tiers | exp | 0.780 | 0.784 | 0.758 | 1.000 | 0.789 |
| idea2_top100_truth__graded_by_idea2_tiers | linear | 0.909 | 0.855 | 0.758 | 1.000 | 0.875 |
