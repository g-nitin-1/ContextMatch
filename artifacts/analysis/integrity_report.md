# Integrity and Honeypot-Oriented Analysis

These rules identify factual inconsistencies and suspicious profiles. They
do not prove that every flagged candidate is an official honeypot.

## Coverage

- Candidates checked: 100,000
- Candidates with at least one issue: 27,234
- Candidates with at least one high-confidence contradiction rule: 162
- Analysis reference date: 2026-06-01

## Risk Levels

| Risk level | Candidates | Share |
| --- | --- | --- |
| none | 72,766 | 72.77% |
| low | 27,040 | 27.04% |
| high | 162 | 0.16% |
| medium | 32 | 0.03% |

## Most Frequent Rules

| Rule | Candidates | Occurrences |
| --- | --- | --- |
| salary_range_order | 18,865 | 18,865 |
| activity_before_signup | 7,496 | 7,496 |
| skill_duration_exceeds_experience | 2,821 | 2,821 |
| company_pre_founding | 83 | 84 |
| technology_before_release | 25 | 38 |
| role_duration_large_mismatch | 33 | 33 |
| career_history_incomplete | 25 | 25 |
| career_duration_exceeds_experience | 23 | 23 |
| expert_zero_duration_3plus | 21 | 21 |
| role_duration_mismatch | 2 | 2 |

## Interpretation

- Frequent signal anomalies are retained as low-severity data-quality
  diagnostics; they are not treated as honeypot evidence.
- `critical` is reserved for internal profile/schema contradictions.
- `high` includes externally checkable chronology contradictions and the
  challenge's explicit zero-duration expert-skill pattern.
- Company and technology chronology checks retain source URLs in the JSONL.
- Medium and low findings should normally be model features, not automatic
  exclusions.
- The official honeypot set remains hidden, so report counts are an upper
  bound on suspicious records rather than recovered ground truth.
