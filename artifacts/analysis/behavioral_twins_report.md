# Behavioral Twin Analysis

A career-matched twin group shares summary archetype, normalized current
title, one-year experience bucket, and ordered career-description
templates. Behavioral fields, skills, and education are excluded from
the primary signature. A stricter education-matched subset is also counted.

This analysis demonstrates controlled behavioral variation. Without hidden
relevance labels, it cannot estimate the official causal weight of a signal.

## Coverage

- Candidates scanned: 100,000
- Career-matched groups: 9,935
- Candidates represented in career-matched groups: 44,948
- Strict education-matched subgroups: 296
- Candidates in strict education-matched subgroups: 597
- ML-relevant career-matched groups: 169
- Representative maximum-distance pairs: 9,935
- Pairs with at least one large contrast: 9,685

## Large Contrast Counts

| Contrast | Representative pairs |
| --- | --- |
| open_to_work | 6254 |
| relocation | 5840 |
| notice_period | 4519 |
| response_time | 4450 |
| interview_completion | 3735 |
| response_rate | 3498 |
| recent_vs_inactive | 2921 |
| recruiter_saves | 234 |

## Behavioral Distribution by Archetype

| Archetype | Candidates | Median inactive days | Median response rate | Median notice days | Open-to-work rate | Median recruiter saves |
| --- | --- | --- | --- | --- | --- | --- |
| general_professional | 63304 | 124.0 | 0.42 | 90 | 32.2% | 6.0 |
| general_software | 25000 | 95.0 | 0.47 | 90 | 39.5% | 10.0 |
| direct_occupation | 5517 | 124.0 | 0.43 | 90 | 31.8% | 6.0 |
| data_backend_adjacent | 5000 | 71.0 | 0.49 | 90 | 50.5% | 15.0 |
| generic_ml | 1000 | 50.0 | 0.58 | 60 | 64.4% | 25.0 |
| applied_ml | 150 | 45.5 | 0.66 | 60 | 73.3% | 33.5 |
| senior_explicit_ai | 21 | 36.0 | 0.75 | 30 | 61.9% | 22.0 |
| senior_plain_language | 8 | 45.0 | 0.79 | 38 | 75.0% | 54.0 |

Behavioral signals are not identically distributed across static profile
archetypes. This means a model can accidentally use behavior as a proxy for
the generator's candidate class unless static relevance and behavior are
modeled separately.

## Highest-Distance Pairs

| Candidate A | Candidate B | Archetype | Title | Distance | Contrasts |
| --- | --- | --- | --- | --- | --- |
| CAND_0020403 | CAND_0071146 | general_professional | Project Manager | 0.651 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0000039 | CAND_0074594 | general_professional | Marketing Manager | 0.640 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0016845 | CAND_0056670 | general_professional | Marketing Manager | 0.639 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation |
| CAND_0038902 | CAND_0080108 | general_professional | Content Writer | 0.631 | recent_vs_inactive;open_to_work;response_time;notice_period;relocation;interview_completion |
| CAND_0023920 | CAND_0032420 | general_professional | Business Analyst | 0.628 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0051235 | CAND_0052365 | general_professional | Operations Manager | 0.625 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0014057 | CAND_0026317 | general_professional | Sales Executive | 0.623 | recent_vs_inactive;open_to_work;response_rate;response_time;relocation;interview_completion |
| CAND_0057985 | CAND_0067575 | general_professional | Accountant | 0.620 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0008078 | CAND_0014422 | general_professional | Operations Manager | 0.619 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0036392 | CAND_0039563 | general_professional | Operations Manager | 0.619 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0063229 | CAND_0065431 | general_professional | Project Manager | 0.616 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0042205 | CAND_0096885 | general_professional | Accountant | 0.614 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0033541 | CAND_0049692 | general_professional | Project Manager | 0.614 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0000416 | CAND_0043650 | general_professional | Customer Support | 0.614 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation;interview_completion |
| CAND_0061051 | CAND_0068744 | general_professional | Civil Engineer | 0.613 | recent_vs_inactive;open_to_work;response_rate;response_time;notice_period;relocation |

## Highest-Distance ML-Relevant Pairs

| Candidate A | Candidate B | Archetype | Title | Distance | Contrasts |
| --- | --- | --- | --- | --- | --- |
| CAND_0052360 | CAND_0060715 | generic_ml | ML Engineer | 0.497 | open_to_work;response_rate;notice_period;relocation;interview_completion |
| CAND_0019210 | CAND_0065430 | generic_ml | ML Engineer | 0.476 | open_to_work;response_rate;notice_period;relocation;interview_completion |
| CAND_0037290 | CAND_0058783 | generic_ml | Computer Vision Engineer | 0.457 | open_to_work;notice_period;relocation;recruiter_saves |
| CAND_0008456 | CAND_0014237 | generic_ml | Data Scientist | 0.449 | open_to_work;notice_period;relocation;recruiter_saves;interview_completion |
| CAND_0002426 | CAND_0085557 | generic_ml | Data Scientist | 0.435 | open_to_work;notice_period;relocation;interview_completion |
| CAND_0007008 | CAND_0089829 | generic_ml | Senior Software Engineer (ML) | 0.426 | open_to_work;response_rate;relocation;recruiter_saves |
| CAND_0070242 | CAND_0089495 | generic_ml | Senior Software Engineer (ML) | 0.421 | open_to_work;notice_period;relocation |
| CAND_0001608 | CAND_0040092 | generic_ml | Senior Software Engineer (ML) | 0.420 | open_to_work;response_rate;relocation;recruiter_saves |
| CAND_0063736 | CAND_0084963 | generic_ml | Data Scientist | 0.419 | open_to_work;response_time;relocation;recruiter_saves |
| CAND_0015065 | CAND_0074325 | generic_ml | AI Research Engineer | 0.419 | open_to_work;response_rate;relocation |
| CAND_0053605 | CAND_0088438 | generic_ml | Senior Software Engineer (ML) | 0.419 | open_to_work;response_rate;response_time;notice_period;recruiter_saves;interview_completion |
| CAND_0052027 | CAND_0075481 | generic_ml | AI Research Engineer | 0.414 | open_to_work;notice_period;relocation |
| CAND_0010000 | CAND_0051545 | generic_ml | AI Research Engineer | 0.413 | open_to_work;response_rate;relocation;interview_completion |
| CAND_0014909 | CAND_0062462 | generic_ml | Computer Vision Engineer | 0.412 | open_to_work;relocation;recruiter_saves;interview_completion |
| CAND_0017164 | CAND_0070524 | generic_ml | Junior ML Engineer | 0.409 | open_to_work;notice_period;relocation |

## Interpretation

- The matched set is useful for counterfactual and sensitivity tests.
- Large behavioral variation among otherwise matched profiles supports
  modeling behavior separately from static relevance.
- The direction of desirable changes comes from the JD and signal
  documentation; their exact hidden-label weights remain unknown.
- `behavioral_twins.csv` contains one maximum-distance pair per group.
