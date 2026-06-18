# Deterministic JD Evidence Catalog

This artifact maps the 44 career templates and 12 fine generator atoms to explicit, versioned JD evidence rules. It does not assign relevance tiers or a combined score.

## Method

- Rubric version: `1.0.5`
- Career templates: 44
- Fine atoms: 12
- Candidates aggregated for atom prevalence: 100,000
- Matching method: case-insensitive regular expressions with exact matched snippets retained in the JSON catalog.
- Candidate-weighted atom evidence is inherited from current and historical career templates.

A missing match means **not observed in the career text**, not that the candidate lacks the capability. Skills and candidate-specific overlays are intentionally deferred.

## Atomic Rubric

| signal | category | meaning |
|---|---|---|
| `embeddings` | direct_requirement | Direct work with embedding models, dense vectors, or sentence-transformer representations. |
| `retrieval_search` | direct_requirement | Direct work on information retrieval, semantic search, hybrid retrieval, search, discovery, or matching. |
| `vector_hybrid_infrastructure` | direct_requirement | Direct work with vector indexes, vector databases, nearest-neighbor retrieval, or sparse+dense infrastructure. |
| `python_engineering` | direct_requirement | Explicit Python or Python-ecosystem engineering evidence. |
| `ranking_evaluation` | direct_requirement | Hands-on design or use of relevance metrics, evaluation frameworks, judgments, or offline-to-online analysis. |
| `ranking_recommendation_matching` | core_role | Work on rankers, recommenders, personalization, matching, discovery relevance, or reranking. |
| `production_delivery` | core_role | Evidence that a technical system or model was shipped, deployed, rolled out, or served to real users. |
| `operational_ownership` | core_role | Ownership of monitoring, drift, index refresh, rollback, reliability, latency, retraining, or production operations. |
| `online_experimentation` | core_role | A/B tests, online metrics, feedback loops, or experiment infrastructure tied to product outcomes. |
| `product_context` | core_role | Work situated in a product, marketplace, SaaS, e-commerce, consumer, or user-facing environment. |
| `meaningful_scale` | core_role | Explicit evidence of large corpora, traffic, users, data volume, or low-latency operation. |
| `learning_to_rank` | preferred | Direct learning-to-rank or trained reranking-model experience. |
| `llm_finetuning` | preferred | Direct LoRA, QLoRA, PEFT, or domain-model fine-tuning experience. |
| `recruiting_marketplace` | preferred | Direct exposure to recruiter, candidate, matching, or marketplace workflows. |
| `distributed_inference` | preferred | Evidence of distributed infrastructure, serving optimization, batching, quantization, or reliability engineering. |
| `external_validation` | preferred | Open-source, papers, talks, or public technical validation. |
| `mentoring_leadership` | preferred | Evidence of mentoring engineers or leading a technical team through delivery. |
| `zero_to_one_ownership` | preferred | Evidence of building a new system, migration, or capability end to end. |
| `computer_vision_primary` | risk_context | The JD treats CV-primary candidates without significant NLP/IR exposure as a poor fit. |
| `consulting_services_context` | risk_context | Consulting/services evidence. The JD disqualifier applies only when the entire career is services-only. |
| `llm_application_context` | risk_context | LLM/RAG application evidence that requires candidate-level recency and depth checks before applying the JD's conditional negative. |
| `research_only_context` | risk_context | Explicit research-only or academic-only work without production evidence. |

## Skill Overlay Patterns

These patterns are used only for candidate skill overlays. They do not create career compounds.

| signal | meaning | pattern count |
|---|---|---:|
| `python_engineering` | Candidate-declared Python or Python ecosystem skills. Skill evidence is kept separate from career compounds. | 7 |
| `embeddings` | Candidate-declared embedding or sentence-transformer skills. | 4 |
| `retrieval_search` | Candidate-declared retrieval/search skills. Avoids bare search to prevent job-search style false positives. | 6 |
| `vector_hybrid_infrastructure` | Candidate-declared vector database, vector search, or search infrastructure skills. | 9 |
| `ranking_recommendation_matching` | Candidate-declared ranking, recommendation, or learning-to-rank skills. | 5 |
| `ranking_evaluation` | Candidate-declared ranking metric or evaluation skills. | 5 |
| `llm_finetuning` | Candidate-declared LoRA, QLoRA, PEFT, or fine-tuning skills. | 4 |
| `llm_application_context` | Candidate-declared LLM/RAG application or framework skills. | 5 |
| `computer_vision_primary` | Candidate-declared computer-vision-primary skill evidence. | 4 |
| `ml_depth` | Skill-only general ML depth signal. It has no career-side compound equivalent. | 7 |

## Required Candidate-Overlay Rules

| rule | JD strength | scope | required interpretation |
|---|---|---|---|
| `services_only_entire_career` | explicit_negative | entire_career | Apply only when every substantive employer/role is consulting or services and there is no product-company history. |
| `research_only_without_production` | hard_disqualifier | entire_career | Apply only when the career is confined to academic/research-only work and no role has production deployment or delivery evidence. |
| `recent_shallow_llm_only` | conditional_negative | career_timeline | Apply only when AI experience is primarily under 12 months of shallow LLM application work and there is no substantial earlier production ML, retrieval, ranking, or recommendation evidence. |
| `senior_not_coding_recently` | conditional_negative | recent_18_months | Apply only to senior candidates whose recent 18-month evidence shows architecture/leadership without hands-on production coding. |

## Fine Atom Evidence

| atom | candidates | interpretation | prod. embedding retrieval | prod. vector/hybrid | evaluated ranking | Python observed | risk contexts |
|---|---:|---|---:|---:|---:|---:|---|
| `fine_atom_00` | 150 | applied_ml | 35.3% | 35.3% | 82.7% | 0.0% | llm_application_context=35.3% |
| `fine_atom_01` | 7 | senior_explicit_ai | 100.0% | 100.0% | 100.0% | 0.0% | llm_application_context=28.6% |
| `fine_atom_02` | 1,000 | generic_ml | 0.0% | 0.0% | 0.0% | 75.1% | computer_vision_primary=32.0% |
| `fine_atom_03` | 4 | senior_explicit_ai | 50.0% | 50.0% | 100.0% | 0.0% | llm_application_context=25.0% |
| `fine_atom_04` | 4 | senior_explicit_ai | 100.0% | 100.0% | 100.0% | 0.0% | llm_application_context=100.0% |
| `fine_atom_05` | 8 | senior_plain_language | 12.5% | 12.5% | 100.0% | 0.0% | - |
| `fine_atom_06` | 68,821 | general_professional | 0.0% | 0.0% | 0.0% | 0.0% | consulting_services_context=31.0% |
| `fine_atom_07` | 5,000 | data_backend_adjacent | 0.0% | 0.0% | 0.0% | 74.2% | - |
| `fine_atom_08` | 3 | senior_explicit_ai | 100.0% | 100.0% | 100.0% | 0.0% | llm_application_context=66.7% |
| `fine_atom_09` | 25,000 | general_software | 0.0% | 0.0% | 0.0% | 33.4% | - |
| `fine_atom_10` | 2 | senior_explicit_ai | 100.0% | 100.0% | 100.0% | 0.0% | llm_application_context=50.0% |
| `fine_atom_11` | 1 | senior_explicit_ai | 100.0% | 100.0% | 100.0% | 0.0% | llm_application_context=100.0% |

## Career Template Evidence

| career template | occurrences | interpretation | direct evidence | compounds | risks |
|---|---:|---|---|---|---|
| `career_035626b6b33e` | 25,290 | general_professional | - | - | - |
| `career_03ab1210df1d` | 359 | generic_ml | python_engineering | - | - |
| `career_0e7ae654f5d1` | 366 | generic_ml | - | - | computer_vision_primary |
| `career_12b13980ad1d` | 25,515 | general_professional | - | - | - |
| `career_1b5ff6cb1b66` | 25,078 | general_professional | - | - | - |
| `career_1d67f17f78c5` | 9,785 | general_software | python_engineering | - | - |
| `career_25f609f7c6ec` | 8 | senior_explicit_ai | embeddings, ranking_evaluation, retrieval_search | end_to_end_intelligence_ownership, evaluated_ranking_system, production_embeddings_retrieval, shipper_with_evaluation_depth | - |
| `career_2c072faa556a` | 5 | senior_plain_language | ranking_evaluation | evaluated_ranking_system | - |
| `career_2d475ce2e723` | 25,029 | general_professional | - | - | - |
| `career_2e516f229493` | 1,823 | data_backend_adjacent | - | - | - |
| `career_3d9f31f6db0e` | 25,164 | general_professional | - | - | - |
| `career_428ce48ac36c` | 8 | senior_explicit_ai | embeddings, ranking_evaluation, retrieval_search, vector_hybrid_infrastructure | production_embeddings_retrieval, production_vector_or_hybrid_search, shipper_with_evaluation_depth | - |
| `career_46cac11f03b0` | 369 | generic_ml | - | - | - |
| `career_551a0361dd79` | 328 | generic_ml | python_engineering | - | - |
| `career_55e5e0725eda` | 10,055 | general_software | - | - | - |
| `career_5a9f2eac4d01` | 25,207 | general_professional | - | - | consulting_services_context |
| `career_5be35db595d9` | 363 | generic_ml | - | - | - |
| `career_71f8d5722d94` | 78 | applied_ml | ranking_evaluation, retrieval_search | evaluated_ranking_system | - |
| `career_73ccc253c91b` | 1,836 | data_backend_adjacent | python_engineering | - | - |
| `career_773c6b592e7d` | 58 | applied_ml | embeddings, ranking_evaluation | evaluated_ranking_system, shipper_with_evaluation_depth | - |
| `career_776a6ac087b2` | 9 | senior_explicit_ai | embeddings, ranking_evaluation, retrieval_search, vector_hybrid_infrastructure | evaluated_ranking_system, production_embeddings_retrieval, production_vector_or_hybrid_search, shipper_with_evaluation_depth | - |
| `career_7916db772044` | 64 | applied_ml | embeddings, ranking_evaluation, retrieval_search, vector_hybrid_infrastructure | - | - |
| `career_7a9b4a7d5a75` | 10,025 | general_software | - | - | - |
| `career_7d9e0102760d` | 60 | applied_ml | embeddings, ranking_evaluation, retrieval_search, vector_hybrid_infrastructure | production_embeddings_retrieval, production_vector_or_hybrid_search, shipper_with_evaluation_depth | llm_application_context |
| `career_87a46a63aede` | 10,125 | general_software | - | - | - |
| `career_8ad07b17b8cf` | 12 | senior_explicit_ai | embeddings, ranking_evaluation, retrieval_search, vector_hybrid_infrastructure | end_to_end_intelligence_ownership, evaluated_ranking_system, production_embeddings_retrieval, production_vector_or_hybrid_search, shipper_with_evaluation_depth | llm_application_context |
| `career_8f5eedb01688` | 9,911 | general_software | - | - | - |
| `career_91d9a2d3c529` | 25,104 | general_professional | - | - | - |
| `career_9ab513003702` | 1,790 | data_backend_adjacent | python_engineering | - | - |
| `career_a0675da68d85` | 1,854 | data_backend_adjacent | - | - | - |
| `career_a30d47e9c3d8` | 5 | senior_plain_language | ranking_evaluation | end_to_end_intelligence_ownership, evaluated_ranking_system, shipper_with_evaluation_depth | - |
| `career_a4f0fbc7e63b` | 25,237 | general_professional | - | - | - |
| `career_a95b2e71340a` | 1,814 | data_backend_adjacent | - | - | - |
| `career_af0ab8d8a342` | 10,015 | general_software | - | - | - |
| `career_bee5dcfedacd` | 4 | senior_plain_language | ranking_evaluation, retrieval_search | evaluated_ranking_system | - |
| `career_c27299c429d2` | 389 | generic_ml | python_engineering | - | - |
| `career_c99d19052bf7` | 12 | senior_explicit_ai | ranking_evaluation, retrieval_search | end_to_end_intelligence_ownership, evaluated_ranking_system, shipper_with_evaluation_depth | - |
| `career_ca4723327469` | 57 | applied_ml | - | - | - |
| `career_d6ac6a7f230c` | 1,807 | data_backend_adjacent | python_engineering | - | - |
| `career_e8f80c98b493` | 2 | senior_plain_language | ranking_evaluation, retrieval_search | end_to_end_intelligence_ownership, evaluated_ranking_system, shipper_with_evaluation_depth | - |
| `career_f14c6d623f93` | 6 | senior_plain_language | ranking_evaluation, retrieval_search | evaluated_ranking_system | - |
| `career_f526a9742420` | 9 | senior_explicit_ai | embeddings, ranking_evaluation | evaluated_ranking_system, shipper_with_evaluation_depth | - |
| `career_fa678c2bc44f` | 25,071 | general_professional | - | - | - |
| `career_fe1930819d75` | 65 | applied_ml | ranking_evaluation | evaluated_ranking_system, shipper_with_evaluation_depth | - |

## Interpretation Boundary

This catalog establishes which JD evidence is explicitly present in the compact generator library. It does not establish official tier assignments. The next stage should add candidate-specific overlays (skills, recency, companies, location, behavior, and integrity) and then formulate probabilistic tier hypotheses.
