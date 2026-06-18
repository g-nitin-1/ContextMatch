# Idea 2 Proxy Scorer

This is a deterministic proxy ranker built on the candidate overlay. It does not claim to recover hidden labels; it reports stability across plausible scoring worlds.

## Coverage

- Scorer version: `0.2.0`
- Candidates scored: 100,000
- Full score CSV: `/mnt/e/contextmatch/artifacts/analysis/idea2_scores.csv`
- Top-100 CSV: `/mnt/e/contextmatch/artifacts/analysis/idea2_top100.csv`
- Validator-ready CSV: `/mnt/e/contextmatch/artifacts/analysis/idea2_submission.csv`

## Worlds

| World | Integrity policy | Title weight | Evidence weight | Skill weight | Behavior weight | Description |
| --- | --- | --- | --- | --- | --- | --- |
| conservative | hard | 1.0 | 0.95 | 0.65 | 0.25 | Prioritizes audited senior/applied evidence, keeps generic ML borderline, hard-excludes strongest honeypot proxies. |
| senior_heavy | hard | 1.0 | 1.05 | 0.55 | 0.2 | Gives the plain-language and explicit senior cohorts the strongest Tier-5 prior, matching the JD's senior-system-builder anchor. |
| applied_ml_friendly | hard | 1.0 | 1.05 | 0.75 | 0.25 | Raises applied-ML candidates when their career templates show ranking/evaluation depth, while keeping senior cohorts high. |
| generic_tail_friendly | hard | 1.0 | 1.05 | 1.1 | 0.25 | Stress-tests whether generic-ML or data/backend tail exceptions can enter the shortlist when skill overlays are useful. |
| behavior_medium | hard | 1.0 | 0.95 | 0.65 | 0.55 | Uses the same static structure as the conservative world but gives bounded behavior and availability the largest allowed influence. |
| mutation_uncertain | strong | 1.0 | 0.95 | 0.65 | 0.25 | Treats detected honeypot proxies as very strong penalties rather than absolute truth, to measure mutation-policy sensitivity. |

## Stability

| Top K | Intersection | Union | Intersection / Union |
| --- | --- | --- | --- |
| 10 | 6 | 15 | 0.4 |
| 50 | 44 | 56 | 0.785714 |
| 100 | 87 | 113 | 0.769912 |

## Top Candidates By Mean Score

| Rank | Candidate | Archetype | Atom | Mean score | Rank range | Integrity | Overlay rules |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | CAND_0088025 | senior_explicit_ai | fine_atom_01 | 7.897114 | 1 | none | - |
| 2 | CAND_0039754 | senior_explicit_ai | fine_atom_01 | 7.85395 | 1 | low | - |
| 3 | CAND_0006567 | senior_plain_language | fine_atom_05 | 7.800841 | 2 | none | - |
| 4 | CAND_0037980 | senior_plain_language | fine_atom_05 | 7.776792 | 1 | none | - |
| 5 | CAND_0081846 | senior_explicit_ai | fine_atom_04 | 7.714749 | 2 | none | - |
| 6 | CAND_0008425 | senior_explicit_ai | fine_atom_10 | 7.689447 | 2 | none | - |
| 7 | CAND_0086022 | senior_explicit_ai | fine_atom_04 | 7.682724 | 5 | low | - |
| 8 | CAND_0005538 | senior_plain_language | fine_atom_05 | 7.678483 | 9 | none | - |
| 9 | CAND_0068351 | senior_plain_language | fine_atom_05 | 7.668208 | 7 | none | - |
| 10 | CAND_0030468 | senior_plain_language | fine_atom_05 | 7.654521 | 3 | low | - |
| 11 | CAND_0005260 | senior_explicit_ai | fine_atom_08 | 7.651217 | 6 | low | - |
| 12 | CAND_0080766 | senior_plain_language | fine_atom_05 | 7.651044 | 3 | none | - |
| 13 | CAND_0046525 | senior_explicit_ai | fine_atom_11 | 7.648449 | 10 | none | - |
| 14 | CAND_0046064 | senior_explicit_ai | fine_atom_08 | 7.630743 | 5 | none | - |
| 15 | CAND_0094759 | senior_explicit_ai | fine_atom_01 | 7.593741 | 7 | none | - |
| 16 | CAND_0077337 | senior_explicit_ai | fine_atom_03 | 7.500962 | 1 | none | - |
| 17 | CAND_0041611 | senior_explicit_ai | fine_atom_04 | 7.3657 | 2 | low | - |
| 18 | CAND_0093193 | senior_plain_language | fine_atom_05 | 7.332233 | 2 | none | - |
| 19 | CAND_0061257 | senior_plain_language | fine_atom_05 | 7.272022 | 2 | none | - |
| 20 | CAND_0060072 | senior_explicit_ai | fine_atom_03 | 7.253973 | 2 | low | - |

## Top-100 Safeguards

| World | High-risk | Honeypot proxy | Overlay rules |
| --- | --- | --- | --- |
| conservative | 0 | 0 | - |
| senior_heavy | 0 | 0 | - |
| applied_ml_friendly | 0 | 0 | - |
| generic_tail_friendly | 0 | 0 | - |
| behavior_medium | 0 | 0 | - |
| mutation_uncertain | 0 | 0 | - |

## Fragile Top-50 Union

These candidates appear in at least one world's top 50 and have the largest rank range across worlds.

| Candidate | Archetype | Atom | Mean score | Best rank | Worst rank | Rank range |
| --- | --- | --- | --- | --- | --- | --- |
| CAND_0009691 | applied_ml | fine_atom_00 | 6.226405 | 43 | 70 | 27 |
| CAND_0041669 | applied_ml | fine_atom_00 | 6.311019 | 25 | 48 | 23 |
| CAND_0012957 | applied_ml | fine_atom_00 | 6.249837 | 38 | 60 | 22 |
| CAND_0065195 | applied_ml | fine_atom_00 | 6.296763 | 28 | 46 | 18 |
| CAND_0096172 | applied_ml | fine_atom_00 | 6.257012 | 36 | 54 | 18 |
| CAND_0099806 | applied_ml | fine_atom_00 | 6.267869 | 34 | 50 | 16 |
| CAND_0096142 | applied_ml | fine_atom_00 | 6.257137 | 37 | 53 | 16 |
| CAND_0093912 | applied_ml | fine_atom_00 | 6.279279 | 31 | 45 | 14 |
| CAND_0054123 | applied_ml | fine_atom_00 | 6.252546 | 40 | 54 | 14 |
| CAND_0095528 | applied_ml | fine_atom_00 | 6.211333 | 50 | 64 | 14 |
| CAND_0075249 | applied_ml | fine_atom_00 | 6.278263 | 34 | 46 | 12 |
| CAND_0030031 | applied_ml | fine_atom_00 | 6.23599 | 44 | 56 | 12 |
| CAND_0037944 | applied_ml | fine_atom_00 | 6.326058 | 25 | 36 | 11 |
| CAND_0044855 | applied_ml | fine_atom_00 | 6.233158 | 44 | 55 | 11 |
| CAND_0069905 | applied_ml | fine_atom_00 | 6.230355 | 47 | 58 | 11 |
| CAND_0043228 | applied_ml | fine_atom_00 | 6.219931 | 49 | 60 | 11 |
| CAND_0046525 | senior_explicit_ai | fine_atom_11 | 7.648449 | 5 | 15 | 10 |
| CAND_0005538 | senior_plain_language | fine_atom_05 | 7.678483 | 5 | 14 | 9 |
| CAND_0052328 | applied_ml | fine_atom_00 | 6.323898 | 26 | 35 | 9 |
| CAND_0027691 | applied_ml | fine_atom_00 | 6.304117 | 29 | 38 | 9 |

## Interpretation Boundary

Use this output to inspect shortlist stability and obvious failure modes. It is still an Idea 2 proxy, not a validated local score.

All current worlds keep two fixed points: senior system-builder cohorts remain above applied/generic cohorts, and high-confidence honeypot proxies are suppressed. That is defensible from the JD and challenge documentation, but it means stability here tests weighting, behavior, mutation policy, and boundary sensitivity rather than a fundamentally different tier ordering.

`BASE_TIER_BY_ATOM` is therefore the core unvalidated hypothesis in this scorer. It needs deliberate sign-off before Idea 2 is frozen; stable rankings across these worlds do not prove the tier mapping is officially correct.
