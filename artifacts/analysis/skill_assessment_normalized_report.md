# Class-Normalized Skill Assessment Experiment

- Experiment: `assessment-normalized-exp-0.2.0`
- Frozen Idea 2 and the absolute assessment experiment remain unchanged.

## Policy

- Each relevant numeric assessment score is centered and scaled within peer archetype before signal-weighted aggregation.
- The two senior archetypes share one pooled baseline; general professional and direct occupations share a tail baseline.
- Candidates without a relevant assessment remain exactly neutral.
- A one-standard-deviation result contributes the signal's frozen skill weight times `1.75` before world scaling.
- The raw normalized modifier is capped at `[-0.15, 0.3]`.

## Ranking Comparison

- Top 10: 9/10 overlap with frozen; 9/10 overlap with absolute assessment.
- Top 50: 43/50 overlap with frozen; 41/50 overlap with absolute assessment.
- Top 100: 94/100 overlap with frozen; 93/100 overlap with absolute assessment.

## Safeguards

- Top-100 high-risk candidates: 0
- Top-100 honeypot proxies: 0
- New candidates versus frozen without career compounds: 0

## Interpretation

This variant removes the average assessment-score advantage associated with each reconstructed profile family. It normalizes numeric scores rather than the aggregate modifier, so one excellent assessment is not penalized merely because the candidate completed fewer assessments. It remains a post-freeze proxy experiment rather than hidden-label validation.
