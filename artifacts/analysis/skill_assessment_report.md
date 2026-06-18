# Skill Assessment Experiment

- Experiment: `assessment-exp-0.1.0`
- Baseline: `idea2-1.0.0`
- Frozen Idea 2 files and manifest were not modified.

## Policy

- Missing assessments are neutral.
- Only assessments mapping to existing JD skill signals affect scores.
- Scores of 80+ outweigh the maximum proficiency-and-duration bonus for one self-declared skill signal.
- Assessment influence is capped and cannot create production career signals or compounds.
- Assessments are class-conditional in this synthetic dataset. This experiment therefore tests an informative but potentially double-counted signal.

## Coverage

- Candidates: 100,000
- Candidates with any assessment: 24,244 (24.24%)
- Assessment entries: 35,895
- Candidates with at least one scored JD signal: 9,581

Assessment coverage is class-conditional, so this modifier can change relative positions even though missing values are individually neutral. Use the per-archetype coverage in the JSON summary when interpreting rank changes.

## Ranking Change

- Top 10: 8/10 retained; 2 entered and 2 exited.
- Top 50: 38/50 retained; 12 entered and 12 exited.
- Top 100: 91/100 retained; 9 entered and 9 exited.

## Safeguards

- Top-100 high-risk candidates: 0
- Top-100 honeypot proxies: 0
- New top-100 candidates without career compounds: 0

## Interpretation

This experiment tests whether platform assessments improve the skill-confidence layer. It does not alter the frozen Idea 2 result and does not establish hidden-label accuracy. Because assessment coverage rises sharply with the reconstructed profile family, the absolute modifier may partially reward class a second time. The result should be compared with Idea 1 and a class-normalized assessment variant before adoption.
