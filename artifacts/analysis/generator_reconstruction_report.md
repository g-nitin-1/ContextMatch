# Generator Reconstruction Report

This report reverse-engineers the synthetic data-generation structure. It does not assign relevance scores and does not use an LLM, embedding model, or teacher output.

## Method

- Candidates: 100,000
- Exact summary templates: 76
- Exact career-description templates: 44
- Exact headline templates: 179
- Coarse static classes: 7
- Fine static atoms: 12
- Mathematical behavior-cluster optimum: 2

Static classes are learned from what each summary template emits: title families, current and historical career templates, industries, skills, and role counts. Summary wording and hand-written archetype labels are not clustering inputs.

Largest positive silhouette gain over the previous k (the strongest structural elbow). The maximum-silhouette solution is retained as fine atoms.

## Static cluster selection

| k | cosine silhouette | gain | smallest templates | smallest candidates |
|---:|---:|---:|---:|---:|
| 4 | 0.5523 | - | 8 | 29 |
| 5 | 0.6060 | 0.053711 | 4 | 29 |
| 6 | 0.5623 | -0.04363 | 1 | 8 |
| 7 | 0.6737 | 0.111386 | 1 | 8 |
| 8 | 0.7055 | 0.031766 | 1 | 4 |
| 9 | 0.7353 | 0.029784 | 1 | 4 |
| 10 | 0.7706 | 0.035348 | 1 | 4 |
| 11 | 0.7997 | 0.029108 | 1 | 2 |
| 12 | 0.8006 | 0.000906 | 1 | 1 |

## Discovered static classes

| class | candidates | templates | interpretation | purity |
|---|---:|---:|---|---:|
| static_class_00 | 21 | 20 | senior_explicit_ai | 1.000 |
| static_class_01 | 150 | 20 | applied_ml | 1.000 |
| static_class_02 | 1,000 | 12 | generic_ml | 1.000 |
| static_class_03 | 5,000 | 4 | data_backend_adjacent | 1.000 |
| static_class_04 | 25,000 | 4 | general_software | 1.000 |
| static_class_05 | 8 | 1 | senior_plain_language | 1.000 |
| static_class_06 | 68,821 | 15 | general_professional | 0.920 |

Interpretations are attached after clustering. Agreement with the manual archetype map is NMI=0.894, AMI=0.894.

## Strongest dependencies

| source | target | NMI | AMI | modal target accuracy |
|---|---|---:|---:|---:|
| static_class | title_family | 0.933 | 0.933 | 0.983 |
| static_class | summary_archetype | 0.894 | 0.894 | 0.945 |
| fine_static_atom | summary_archetype | 0.894 | 0.894 | 0.945 |
| summary_template | summary_archetype | 0.611 | 0.611 | 1.000 |
| summary_template | title_family | 0.485 | 0.485 | 0.983 |
| static_class | current_career_template | 0.440 | 0.439 | 0.131 |
| current_career_template | summary_archetype | 0.418 | 0.417 | 0.945 |
| headline_template | summary_archetype | 0.366 | 0.365 | 1.000 |
| summary_template | headline_template | 0.339 | 0.333 | 0.053 |
| summary_template | current_career_template | 0.315 | 0.313 | 0.136 |
| static_class | current_industry | 0.159 | 0.159 | 0.300 |
| static_class | behavior_cluster | 0.020 | 0.020 | 0.611 |

## Behavior structure

The best k among 2-6 is shown below, but its silhouette is only 0.113. This is weak evidence for discrete behavioral classes. Treat behavior as mostly continuous plus missing-data patterns.

| cluster | candidates | dominant static class | inactive days | response rate |
|---|---:|---|---:|---:|
| behavior_cluster_00 | 40,446 | static_class_06 | 106.0 | 0.450 |
| behavior_cluster_01 | 59,554 | static_class_06 | 113.0 | 0.430 |

Strongest cluster separators:

- `offer_history_missing`: standardized mean range 2.038
- `offer_acceptance`: standardized mean range 1.834
- `recruiter_saves_log`: standardized mean range 0.120
- `search_appearances_log`: standardized mean range 0.113
- `interview_completion`: standardized mean range 0.093

Behavior variance explained by static class (eta-squared):

- `search_appearances_log`: 0.111
- `recruiter_saves_log`: 0.109
- `github_score`: 0.078
- `inactive_days`: 0.070
- `interview_completion`: 0.068
- `profile_views_log`: 0.060
- `response_time_hours`: 0.058
- `offer_acceptance`: 0.046

## Mutation reconstruction

| mutation | candidates | dominant class | interpreted archetype | concentrated evidence |
|---|---:|---|---|---|
| company_chronology | 83 | static_class_02 | generic_ml | Sarvam AI (44), Krutrim (38), Rephrase.ai (2) |
| duration_corruption | 37 | static_class_06 | general_professional | Hooli (5), Globex Inc (4), Initech (4) |
| technology_chronology | 25 | static_class_01 | applied_ml | Aganitha (6), Yellow.ai (3), Glance (3) |
| zero_duration_expert | 21 | static_class_06 | general_professional | - |

## Reconstructed generator graph

The evidence supports a generator with static profile families that emit summary, headline, title, career, industry, and skill atoms; a mostly continuous behavior generator whose distribution depends partly on profile family; and rare targeted contradiction mutations applied to selected records.

This is evidence about data production, not proof of an official relevance grade. The next Idea 2 stage is to infer and freeze an ordinal mapping from the job description to these reconstructed classes before any Idea 1 comparison.
