# Profile Archetype Analysis

This report describes deterministic generator patterns. It does not assign
or claim to recover official relevance tiers.

## Dataset

- Candidate records: 100,000
- Career entries: 300,171
- Unique normalized summary templates: 76
- Unique normalized headline templates: 179
- Unique exact career-description templates: 44
- Unique ordered career-template sequences: 25,912

## Summary Archetypes

| Archetype | Candidates | Share |
| --- | --- | --- |
| general_professional | 63,304 | 63.30% |
| general_software | 25,000 | 25.00% |
| direct_occupation | 5,517 | 5.52% |
| data_backend_adjacent | 5,000 | 5.00% |
| generic_ml | 1,000 | 1.00% |
| applied_ml | 150 | 0.15% |
| senior_explicit_ai | 21 | 0.02% |
| senior_plain_language | 8 | 0.01% |

## Title Families

| Title family | Candidates | Share |
| --- | --- | --- |
| other | 68,953 | 68.95% |
| software | 26,373 | 26.37% |
| data_backend | 3,627 | 3.63% |
| ai_ml | 857 | 0.86% |
| senior_ai_ml | 190 | 0.19% |

## Interpretation

- The small number of career-description templates confirms that career
  evidence was generated from a compact library.
- Summary archetypes are useful structural hypotheses, not hidden labels.
- Candidate-level assignments are available in `archetype_assignments.csv`.
- Any relevance mapping must be validated against independent semantic and
  factual evidence to avoid overfitting generator artifacts.
