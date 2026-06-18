# Consolidated Analysis: Archetypes, Integrity, Behavior, and Overlay

## Executive Findings

1. The dataset contains 44 exact career-description templates across 300,171 career entries. Generator structure is therefore strong and measurable.
2. The rarest summary cohorts contain 8 plain-language senior profiles, 21 explicit senior AI profiles, 150 applied-ML profiles, and 1,000 generic-ML profiles. These are structural cohorts, not proven official relevance tiers.
3. The integrity engine found 162 candidates with at least one strong contradiction. 108 (66.7%) are in ML-relevant-looking cohorts, so anomaly filtering matters most exactly where keyword and semantic rankers are likely to focus.
4. 104 candidates match a proxy rule based on one of the challenge's documented honeypot pattern families: employment before company founding or multiple expert skills with zero duration. This is not the hidden official set.
5. Career-matched analysis produced 9,935 groups covering 44,948 candidates, including 169 ML-relevant groups. Behavior varies substantially inside these groups.
6. The candidate overlay joins template evidence to skills, recency, logistics, behavior, and integrity for all 100,000 candidates. Current rule firings: services-only=5,345, recent-shallow-LLM=1,907, research-only=2, senior-not-coding=428.
7. The first Idea 2 scorer evaluates candidates across 6 plausible worlds. Top-10 consensus intersection/union is 6/15; top-100 is 87/113.

## Archetype Structure

| Archetype | Candidates | Share |
| --- | --- | --- |
| applied_ml | 150 | 0.15% |
| data_backend_adjacent | 5,000 | 5.00% |
| direct_occupation | 5,517 | 5.52% |
| general_professional | 63,304 | 63.30% |
| general_software | 25,000 | 25.00% |
| generic_ml | 1,000 | 1.00% |
| senior_explicit_ai | 21 | 0.02% |
| senior_plain_language | 8 | 0.01% |

The exact cohort sizes strongly suggest deliberate generator classes.
However, assigning them directly to hidden relevance tiers would be an
unsupported leap. They should become probabilistic prior features.

## Integrity Findings

| Evidence family | Unique candidates |
| --- | --- |
| Documented-pattern proxy | 104 |
| Additional technology chronology | 25 |
| Large duration contradictions | 37 |
| Union of strong contradiction rules | 162 |

| Archetype | High-risk candidates |
| --- | --- |
| generic_ml | 71 |
| general_professional | 35 |
| applied_ml | 29 |
| general_software | 16 |
| senior_explicit_ai | 8 |
| data_backend_adjacent | 3 |

The 24,895 behavioral data-quality records are intentionally kept separate.
Their frequency makes them unsuitable as automatic honeypot exclusions.

The company-founding rule alone flags 83 unique candidates, which is close
to the challenge's approximate honeypot count. This is notable but not
proof: technology and duration checks identify additional non-overlapping
contradictions.

## Behavioral Twin Findings

| Archetype | Career-matched groups |
| --- | --- |
| applied_ml | 5 |
| data_backend_adjacent | 864 |
| direct_occupation | 358 |
| general_professional | 5190 |
| general_software | 3354 |
| generic_ml | 164 |

Within the 169 ML-relevant matched groups:

| Signal contrast | Representative pairs |
| --- | --- |
| interview_completion | 41 |
| notice_period | 57 |
| open_to_work | 88 |
| recruiter_saves | 58 |
| relocation | 89 |
| response_rate | 46 |
| response_time | 13 |

No senior-profile twin groups were found under the career-matched
definition because the senior cohorts are small and structurally unique.
Behavioral weights for the top cohort therefore cannot be inferred from
twins alone.

Behavior is also conditioned on archetype. For example, ML-relevant groups
have narrower inactivity ranges and larger recruiter-save variation than
the broad population. A model should compute static relevance first and
apply a bounded behavioral modifier second.

## Implications for the Proxy Ranker

1. Use archetype as a prior, never as a final relevance label.
2. Give career templates and demonstrated work more weight than skills.
3. Treat company-founding and zero-duration-expert checks as the strongest
   honeypot signals; keep chronology and duration checks as strong but
   independently auditable evidence.
4. Do not let common salary/signup inconsistencies disqualify candidates.
5. Cap behavioral adjustments so they reorder similarly qualified
   candidates without promoting irrelevant but active candidates.
6. Use the 169 ML-relevant matched groups for behavioral sensitivity tests.
7. Cross-check rare senior candidates individually with the teacher system
   from Idea 1 because twin-based estimation has no coverage there.

## Candidate Overlay Findings

The overlay is the candidate-level feature table for Idea 2. It does
not assign tiers or scores.

| Overlay rule | Candidates |
| --- | --- |
| recent_shallow_llm_only | 1907 |
| research_only_without_production | 2 |
| senior_not_coding_recently | 428 |
| services_only_entire_career | 5345 |

Career compounds inherited by candidates:

| Compound | Candidates |
| --- | --- |
| end_to_end_intelligence_ownership | 25 |
| evaluated_ranking_system | 153 |
| production_embeddings_retrieval | 73 |
| production_vector_or_hybrid_search | 73 |
| shipper_with_evaluation_depth | 141 |

## Idea 2 Score Findings

The scorer is a multi-world proxy model, not a local leaderboard.
All current worlds preserve the senior-above-applied/generic tier ordering, so stability here tests weighting and boundary choices, not a fundamentally different JD-to-tier mapping.

| Top K | Intersection | Union | Intersection / Union |
| --- | --- | --- | --- |
| 10 | 6 | 15 | 0.4 |
| 50 | 44 | 56 | 0.785714 |
| 100 | 87 | 113 | 0.769912 |

Top candidates by mean score:

| Rank | Candidate | Archetype | Atom | Mean score |
| --- | --- | --- | --- | --- |
| 1 | CAND_0088025 | senior_explicit_ai | fine_atom_01 | 7.897114 |
| 2 | CAND_0039754 | senior_explicit_ai | fine_atom_01 | 7.85395 |
| 3 | CAND_0006567 | senior_plain_language | fine_atom_05 | 7.800841 |
| 4 | CAND_0037980 | senior_plain_language | fine_atom_05 | 7.776792 |
| 5 | CAND_0081846 | senior_explicit_ai | fine_atom_04 | 7.714749 |
| 6 | CAND_0008425 | senior_explicit_ai | fine_atom_10 | 7.689447 |
| 7 | CAND_0086022 | senior_explicit_ai | fine_atom_04 | 7.682724 |
| 8 | CAND_0005538 | senior_plain_language | fine_atom_05 | 7.678483 |
| 9 | CAND_0068351 | senior_plain_language | fine_atom_05 | 7.668208 |
| 10 | CAND_0030468 | senior_plain_language | fine_atom_05 | 7.654521 |

## What Remains Unknown

- The official relevance tier definitions and gains.
- Which detected contradictions are included in the hidden honeypot list.
- The exact behavioral modifier used in hidden labels.
- Whether hidden labels were generated entirely by rules or manually
  adjusted.
