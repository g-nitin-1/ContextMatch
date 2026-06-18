# Candidate Evidence Overlay

This stage joins frozen template evidence to candidate-specific facts. It does not assign relevance tiers or a score.

## Coverage

- Candidates processed: 100,000
- Rubric version: `1.0.5`
- JSONL output: `/mnt/e/contextmatch/artifacts/analysis/candidate_overlay.jsonl`

## Overlay Rule Firings

| Rule | Candidates | Share |
| --- | --- | --- |
| services_only_entire_career | 5,345 | 5.34% |
| recent_shallow_llm_only | 1,907 | 1.91% |
| senior_not_coding_recently | 428 | 0.43% |
| research_only_without_production | 2 | 0.00% |

## Overlay Rule Firings By Archetype

### `recent_shallow_llm_only`

| Archetype | Candidates |
| --- | --- |
| direct_occupation | 1549 |
| general_software | 245 |
| data_backend_adjacent | 106 |
| generic_ml | 7 |

### `research_only_without_production`

| Archetype | Candidates |
| --- | --- |
| generic_ml | 2 |

### `senior_not_coding_recently`

| Archetype | Candidates |
| --- | --- |
| data_backend_adjacent | 428 |

### `services_only_entire_career`

| Archetype | Candidates |
| --- | --- |
| general_professional | 3178 |
| general_software | 1590 |
| direct_occupation | 295 |
| data_backend_adjacent | 265 |
| generic_ml | 17 |

## Integrity Join

| Risk level | Candidates | Share |
| --- | --- | --- |
| none | 72,766 | 72.77% |
| low | 27,040 | 27.04% |
| high | 162 | 0.16% |
| medium | 32 | 0.03% |

High-confidence integrity rules:

| Rule | Candidates |
| --- | --- |
| company_pre_founding | 83 |
| role_duration_large_mismatch | 33 |
| technology_before_release | 25 |
| career_duration_exceeds_experience | 23 |
| expert_zero_duration_3plus | 21 |

## Skill Evidence

| Skill signal | Candidates | Share |
| --- | --- | --- |
| python_engineering | 24,623 | 24.62% |
| ml_depth | 21,530 | 21.53% |
| vector_hybrid_infrastructure | 14,158 | 14.16% |
| computer_vision_primary | 12,989 | 12.99% |
| retrieval_search | 11,448 | 11.45% |
| llm_application_context | 10,359 | 10.36% |
| llm_finetuning | 8,599 | 8.60% |
| embeddings | 7,551 | 7.55% |
| ranking_recommendation_matching | 6,393 | 6.39% |

## Career Compounds

| Career compound | Candidates | Share |
| --- | --- | --- |
| evaluated_ranking_system | 153 | 0.15% |
| shipper_with_evaluation_depth | 141 | 0.14% |
| production_embeddings_retrieval | 73 | 0.07% |
| production_vector_or_hybrid_search | 73 | 0.07% |
| end_to_end_intelligence_ownership | 25 | 0.03% |

## Interpretation Boundary

This overlay creates the candidate-level feature table needed for Idea 2 tier hypotheses. Template evidence is inherited from the versioned rubric; its manual audit and freeze status are recorded separately. Behavior remains a bounded modifier rather than a base relevance signal.
