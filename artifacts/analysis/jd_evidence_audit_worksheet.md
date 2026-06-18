# JD Evidence Catalog — Manual Audit Worksheet

Rubric version: `1.0.5` | Career templates: 44 | Source: `India_runs_data_and_ai_challenge/job_description.docx`

Purpose: verify every assigned signal and look for missing evidence in the complete, finite career-template library before the rubric is version-locked. Because all 300k career entries are copies of these 44 templates, a clean audit makes extraction errors enumerable and correctable across the visible career-template library. It is still subject to human and rubric judgment. This tool changes nothing; edit `jd_evidence_rubric.json` and re-run the catalog if a fix is needed.

How to review each template:

1. Read the full text.
2. False positives — does any listed signal NOT actually hold in the text? (e.g. "SaaS product" firing product context for a support lead.)
3. False negatives — is there JD-relevant evidence the rubric missed?
4. Mark the verdict line.

Audit priority (by share of composite score a template can move):

- **Tier A — highest scrutiny (17 templates):** senior and applied-ML templates. These can decide NDCG@10/@50. Verify every signal AND every absence; one error can materially change a top-cohort candidate.
- **Tier C — check both directions (6 templates):** generic-ML, the borderline Tier-3 region (MAP / P@10).
- **Tier B — confirm no false positives (21 templates):** high-population non-ML templates. False negatives are lower priority but should still be noted for tail-exception audits; a false direct-requirement match injects noise into the top 100.

---

## Tier A

### `career_e8f80c98b493` — senior_plain_language (Tier A)

- Occurrences: 2 (current role: 2) | archetype purity: 1.000
- Compounds: `end_to_end_intelligence_ownership`, `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Led the engineering team building infrastructure to surface relevant content to users at scale. The system processed billions of documents and served millions of queries with low latency. Most of the technical effort went into the boring-but-essential parts: index refresh, query understanding, ranking calibration, and the dashboards that made the system's behavior legible to product and business teams. I had a small team of 4 across this work.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `ranking calibration`
    - snippet: "...o the boring-but-essential parts: index refresh, query understanding, ranking calibration, and the dashboards that made the system's behavior legible to produc..."
  - `retrieval_search` (Retrieval or search systems) — matched: `query understanding`
    - snippet: "...nical effort went into the boring-but-essential parts: index refresh, query understanding, ranking calibration, and the dashboards that made the system's behav..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `millions of queries`, `billions of documents`, `low latency`
    - snippet: "...users at scale. The system processed billions of documents and served millions of queries with low latency. Most of the technical effort went into the boring-b..."
  - `operational_ownership` (Operational ownership) — matched: `index refresh`, `latency`
    - snippet: "...ost of the technical effort went into the boring-but-essential parts: index refresh, query understanding, ranking calibration, and the dashboards that ma..."
  - `product_context` (Product context) — matched: `product`
    - snippet: "...ration, and the dashboards that made the system's behavior legible to product and business teams. I had a small team of 4 across this work."
  - `production_delivery` (Production delivery) — matched: `served millions`
    - snippet: "...ent to users at scale. The system processed billions of documents and served millions of queries with low latency. Most of the technical effort went into t..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `relevant content`
    - snippet: "...o the boring-but-essential parts: index refresh, query understanding, ranking calibration, and the dashboards that made the system's behavior legib..."
- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `low latency`
    - snippet: "...m processed billions of documents and served millions of queries with low latency. Most of the technical effort went into the boring-but-essential part..."
  - `mentoring_leadership` (Mentoring or technical leadership) — matched: `Led the engineering team`
    - snippet: "Led the engineering team building infrastructure to surface relevant content to users at scale..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_bee5dcfedacd` — senior_plain_language (Tier A)

- Occurrences: 4 (current role: 1) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`

Text:

> Owned the search and discovery experience end-to-end at a consumer product, from how content is represented internally through to how the most relevant results appear for each user's intent. The work spanned data infrastructure, ranking algorithms, evaluation methodology, and direct collaboration with product/PM on what 'relevance' actually means for our users. Spent a fair amount of time on the eval side — building offline metrics that actually correlated with online engagement, which turned out to be the hardest part.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `evaluation methodology`, `offline metrics`
    - snippet: "...r's intent. The work spanned data infrastructure, ranking algorithms, evaluation methodology, and direct collaboration with product/PM on what 'relevance' actuall..."
  - `retrieval_search` (Retrieval or search systems) — matched: `search and discovery`
    - snippet: "Owned the search and discovery experience end-to-end at a consumer product, from how content is repr..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `online engagement`
    - snippet: "...he eval side — building offline metrics that actually correlated with online engagement, which turned out to be the hardest part."
  - `product_context` (Product context) — matched: `product`, `consumer product`
    - snippet: "Owned the search and discovery experience end-to-end at a consumer product, from how content is represented internally through to how the most r..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `most relevant results`
    - snippet: "...appear for each user's intent. The work spanned data infrastructure, ranking algorithms, evaluation methodology, and direct collaboration with pro..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_2c072faa556a` — senior_plain_language (Tier A)

- Occurrences: 5 (current role: 2) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`

Text:

> Designed the ranking layer for the company's flagship product: how do we surface the right thing at the right time, across millions of items, for millions of users. The hard problem was rarely the modeling — it was the data pipeline that fed the models, the evaluation framework that told us whether they worked, and the operational discipline of keeping all of it healthy in production. I owned all three across roughly 14 months.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `evaluation framework`
    - snippet: "...rely the modeling — it was the data pipeline that fed the models, the evaluation framework that told us whether they worked, and the operational discipline of k..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `millions of items`
    - snippet: "...product: how do we surface the right thing at the right time, across millions of items, for millions of users. The hard problem was rarely the modeling — it..."
  - `operational_ownership` (Operational ownership) — matched: `operational discipline`, `keeping all of it healthy in production`
    - snippet: "...s, the evaluation framework that told us whether they worked, and the operational discipline of keeping all of it healthy in production. I owned all three across..."
  - `product_context` (Product context) — matched: `product`
    - snippet: "Designed the ranking layer for the company's flagship product: how do we surface the right thing at the right time, across millions..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`
    - snippet: "Designed the ranking layer for the company's flagship product: how do we surface the right..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_a30d47e9c3d8` — senior_plain_language (Tier A)

- Occurrences: 5 (current role: 1) | archetype purity: 1.000
- Compounds: `end_to_end_intelligence_ownership`, `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Shipped the personalization infrastructure: the system that learns from user behavior and improves relevance over time. Designed the offline experimentation environment, the online A/B testing framework, and the feature-engineering pipeline that connected them. Most of my time went into the boring-but-critical operational layer — feature monitoring, drift detection, retraining cadence — rather than the modeling itself. Worked closely with the product and growth teams.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `offline experimentation environment`
    - snippet: "...rns from user behavior and improves relevance over time. Designed the offline experimentation environment, the online A/B testing framework, and the feature-engineering pipeli..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `A/B testing`, `offline experimentation environment`
    - snippet: "...er time. Designed the offline experimentation environment, the online A/B testing framework, and the feature-engineering pipeline that connected them...."
  - `operational_ownership` (Operational ownership) — matched: `drift detection`, `feature monitoring`, `retraining cadence`
    - snippet: "...into the boring-but-critical operational layer — feature monitoring, drift detection, retraining cadence — rather than the modeling itself. Worked closely..."
  - `product_context` (Product context) — matched: `product`
    - snippet: "...ng cadence — rather than the modeling itself. Worked closely with the product and growth teams."
  - `production_delivery` (Production delivery) — matched: `Shipped`
    - snippet: "Shipped the personalization infrastructure: the system that learns from user..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `personalization`, `relevance over time`
    - snippet: "Shipped the personalization infrastructure: the system that learns from user behavior and improve..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_f14c6d623f93` — senior_plain_language (Tier A)

- Occurrences: 6 (current role: 2) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`

Text:

> Built systems that understand what users are looking for and connect them to the most relevant matches across a large dataset. Worked at the intersection of infrastructure, algorithms, and product judgment — none of the three were optional. Recent project was a complete overhaul of the matching layer; took it from a hand-tuned heuristic system to one with explicit modeling and evaluation. The team grew from just me to 6 engineers over the course of that work.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `modeling and evaluation`
    - snippet: "...ayer; took it from a hand-tuned heuristic system to one with explicit modeling and evaluation. The team grew from just me to 6 engineers over the course of that wo..."
  - `retrieval_search` (Retrieval or search systems) — matched: `matching layer`
    - snippet: "...he three were optional. Recent project was a complete overhaul of the matching layer; took it from a hand-tuned heuristic system to one with explicit mode..."
- **Core role**
  - `product_context` (Product context) — matched: `product`
    - snippet: "...ataset. Worked at the intersection of infrastructure, algorithms, and product judgment — none of the three were optional. Recent project was a comp..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `matching layer`, `relevant matches`
    - snippet: "...he three were optional. Recent project was a complete overhaul of the matching layer; took it from a hand-tuned heuristic system to one with explicit mode..."
- **Preferred**
  - `mentoring_leadership` (Mentoring or technical leadership) — matched: `team grew from`
    - snippet: "...ed heuristic system to one with explicit modeling and evaluation. The team grew from just me to 6 engineers over the course of that work."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `complete overhaul`
    - snippet: "...duct judgment — none of the three were optional. Recent project was a complete overhaul of the matching layer; took it from a hand-tuned heuristic system to..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_25f609f7c6ec` — senior_explicit_ai (Tier A)

- Occurrences: 8 (current role: 2) | archetype purity: 1.000
- Compounds: `end_to_end_intelligence_ownership`, `evaluated_ranking_system`, `production_embeddings_retrieval`, `shipper_with_evaluation_depth`

Text:

> Led the migration from keyword-based to embedding-based search across a 30M+ candidate corpus over 8 months. Designed three successive ranker variants and ran them in A/B testing alongside the legacy keyword system. The final embedding ranker improved recruiter engagement metrics by 24% and reduced the average time-to-shortlist by 38%. Most of the engineering effort went into the boring infrastructure: index versioning, embedding versioning, rollback paths, and the dashboards that let recruiters trust the new system. Mentored two junior engineers through this rollout.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embedding`
    - snippet: "Led the migration from keyword-based to embedding-based search across a 30M+ candidate corpus over 8 months. Designed t..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `recruiter engagement metrics`, `A/B testing alongside`
    - snippet: "...ngside the legacy keyword system. The final embedding ranker improved recruiter engagement metrics by 24% and reduced the average time-to-shortlist by 38%. Most of the..."
  - `retrieval_search` (Retrieval or search systems) — matched: `embedding-based search`
    - snippet: "Led the migration from keyword-based to embedding-based search across a 30M+ candidate corpus over 8 months. Designed three successi..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `30M+ candidate corpus`
    - snippet: "...d the migration from keyword-based to embedding-based search across a 30M+ candidate corpus over 8 months. Designed three successive ranker variants and ran them..."
  - `online_experimentation` (Online experimentation) — matched: `A/B testing`
    - snippet: "...r 8 months. Designed three successive ranker variants and ran them in A/B testing alongside the legacy keyword system. The final embedding ranker impro..."
  - `operational_ownership` (Operational ownership) — matched: `index versioning`, `embedding versioning`, `rollback paths`
    - snippet: ".... Most of the engineering effort went into the boring infrastructure: index versioning, embedding versioning, rollback paths, and the dashboards that let re..."
  - `production_delivery` (Production delivery) — matched: `rollout`
    - snippet: "...ters trust the new system. Mentored two junior engineers through this rollout."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranker`
    - snippet: "...ross a 30M+ candidate corpus over 8 months. Designed three successive ranker variants and ran them in A/B testing alongside the legacy keyword sys..."
- **Preferred**
  - `mentoring_leadership` (Mentoring or technical leadership) — matched: `Mentored`
    - snippet: "...k paths, and the dashboards that let recruiters trust the new system. Mentored two junior engineers through this rollout."
  - `recruiting_marketplace` (Recruiting, HR-tech, or marketplace context) — matched: `recruiter`, `candidate corpus`, `time-to-shortlist`
    - snippet: "...ngside the legacy keyword system. The final embedding ranker improved recruiter engagement metrics by 24% and reduced the average time-to-shortlist b..."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `Led the migration`
    - snippet: "Led the migration from keyword-based to embedding-based search across a 30M+ candidate..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_428ce48ac36c` — senior_explicit_ai (Tier A)

- Occurrences: 8 (current role: 2) | archetype purity: 0.875
- Compounds: `production_embeddings_retrieval`, `production_vector_or_hybrid_search`, `shipper_with_evaluation_depth`

Text:

> Owned the design and rollout of a large-scale semantic search system serving an internal corpus of 35M+ items. Migrated the existing BM25-only retrieval to a hybrid setup combining sparse and dense vectors (sentence-transformers, MPNet-base initially, later fine-tuned BGE-large for our domain). The new system reduced p95 retrieval latency by 60% while improving NDCG@10 by 18% on our held-out eval set. Spent substantial time on the boring-but-critical parts: incremental index refresh, embedding drift monitoring, online/offline metric correlation. Led a team of 4 engineers across the rollout.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embedding`, `dense vectors`, `sentence-transformers`, `BGE-large`, `MPNet-base`
    - snippet: "...ial time on the boring-but-critical parts: incremental index refresh, embedding drift monitoring, online/offline metric correlation. Led a team of 4..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `NDCG@10`, `eval set`, `offline metric`
    - snippet: ".... The new system reduced p95 retrieval latency by 60% while improving NDCG@10 by 18% on our held-out eval set. Spent substantial time on the boring..."
  - `retrieval_search` (Retrieval or search systems) — matched: `retrieval`, `semantic search`, `search system`, `BM25`
    - snippet: "...ing an internal corpus of 35M+ items. Migrated the existing BM25-only retrieval to a hybrid setup combining sparse and dense vectors (sentence-transf..."
  - `vector_hybrid_infrastructure` (Vector or hybrid-search infrastructure) — matched: `sparse and dense`
    - snippet: "...Migrated the existing BM25-only retrieval to a hybrid setup combining sparse and dense vectors (sentence-transformers, MPNet-base initially, later fine-tune..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `35M+ items`
    - snippet: "...of a large-scale semantic search system serving an internal corpus of 35M+ items. Migrated the existing BM25-only retrieval to a hybrid setup combinin..."
  - `operational_ownership` (Operational ownership) — matched: `index refresh`, `embedding drift`, `drift monitoring`, `p95`, `latency`
    - snippet: "...Spent substantial time on the boring-but-critical parts: incremental index refresh, embedding drift monitoring, online/offline metric correlation. Led a..."
  - `production_delivery` (Production delivery) — matched: `rollout`
    - snippet: "Owned the design and rollout of a large-scale semantic search system serving an internal corpus of..."
- **Preferred**
  - `mentoring_leadership` (Mentoring or technical leadership) — matched: `Led a team`
    - snippet: "...fresh, embedding drift monitoring, online/offline metric correlation. Led a team of 4 engineers across the rollout."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `Owned the design and rollout`
    - snippet: "Owned the design and rollout of a large-scale semantic search system serving an internal corpus of..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_776a6ac087b2` — senior_explicit_ai (Tier A)

- Occurrences: 9 (current role: 6) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`, `production_embeddings_retrieval`, `production_vector_or_hybrid_search`, `shipper_with_evaluation_depth`

Text:

> Owned the end-to-end ranking pipeline at a recommendations-heavy consumer product: candidate sourcing → embedding generation (using a fine-tuned BGE-large) → Pinecone retrieval → learning-to-rank re-scoring (XGBoost) → behavioral-signal integration. The hardest part wasn't the ML — it was the evaluation: building offline metrics that actually predicted what the recommendation would do to live engagement. After three iterations we landed on a calibration approach using simulated A/B tests that has held up over the last 18 months.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embedding`, `BGE-large`
    - snippet: "...ine at a recommendations-heavy consumer product: candidate sourcing → embedding generation (using a fine-tuned BGE-large) → Pinecone retrieval → lear..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `offline metrics`
    - snippet: "...ion. The hardest part wasn't the ML — it was the evaluation: building offline metrics that actually predicted what the recommendation would do to live enga..."
  - `retrieval_search` (Retrieval or search systems) — matched: `retrieval`
    - snippet: "...cing → embedding generation (using a fine-tuned BGE-large) → Pinecone retrieval → learning-to-rank re-scoring (XGBoost) → behavioral-signal integrati..."
  - `vector_hybrid_infrastructure` (Vector or hybrid-search infrastructure) — matched: `Pinecone`
    - snippet: "...date sourcing → embedding generation (using a fine-tuned BGE-large) → Pinecone retrieval → learning-to-rank re-scoring (XGBoost) → behavioral-signal..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `A/B tests`, `simulated A/B tests`
    - snippet: "...three iterations we landed on a calibration approach using simulated A/B tests that has held up over the last 18 months."
  - `product_context` (Product context) — matched: `product`, `consumer product`
    - snippet: "...d the end-to-end ranking pipeline at a recommendations-heavy consumer product: candidate sourcing → embedding generation (using a fine-tuned BGE-la..."
  - `production_delivery` (Production delivery) — matched: `live engagement`
    - snippet: "...e metrics that actually predicted what the recommendation would do to live engagement. After three iterations we landed on a calibration approach using sim..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `recommendations`
    - snippet: "Owned the end-to-end ranking pipeline at a recommendations-heavy consumer product: candidate sourc..."
- **Preferred**
  - `learning_to_rank` (Learning to rank) — matched: `learning-to-rank`
    - snippet: "...ding generation (using a fine-tuned BGE-large) → Pinecone retrieval → learning-to-rank re-scoring (XGBoost) → behavioral-signal integration. The hardest par..."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `Owned the end-to-end`
    - snippet: "Owned the end-to-end ranking pipeline at a recommendations-heavy consumer product: candida..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_f526a9742420` — senior_explicit_ai (Tier A)

- Occurrences: 9 (current role: 4) | archetype purity: 0.889
- Compounds: `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Built and shipped a production recommendation system at a marketplace product, going from offline experimentation to live A/B test in 5 months. The system combined collaborative filtering (matrix factorization), content-based features (TF-IDF + sentence-transformer embeddings), and a behavioral re-ranking layer. The most interesting technical challenge was the cold-start problem for new users; I designed an exploration-exploitation policy using Thompson sampling that improved new-user retention by 11% in the first month.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embeddings`, `sentence-transformer`
    - snippet: "...factorization), content-based features (TF-IDF + sentence-transformer embeddings), and a behavioral re-ranking layer. The most interesting technical c..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `live A/B test`
    - snippet: "...ystem at a marketplace product, going from offline experimentation to live A/B test in 5 months. The system combined collaborative filtering (matrix fact..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `A/B test`
    - snippet: "...at a marketplace product, going from offline experimentation to live A/B test in 5 months. The system combined collaborative filtering (matrix fact..."
  - `product_context` (Product context) — matched: `product`, `marketplace`
    - snippet: "Built and shipped a production recommendation system at a marketplace product, going from offline experimentation to live A/B test in 5 months. The..."
  - `production_delivery` (Production delivery) — matched: `production recommendation`, `shipped`, `live A/B test`
    - snippet: "Built and shipped a production recommendation system at a marketplace product, going from offline experimentation t..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `re-ranking`, `recommendation system`
    - snippet: "...tures (TF-IDF + sentence-transformer embeddings), and a behavioral re-ranking layer. The most interesting technical challenge was the cold-start pr..."
- **Preferred**
  - `recruiting_marketplace` (Recruiting, HR-tech, or marketplace context) — matched: `marketplace`
    - snippet: "Built and shipped a production recommendation system at a marketplace product, going from offline experimentation to live A/B test in 5 mon..."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `going from offline experimentation to live`
    - snippet: "...shipped a production recommendation system at a marketplace product, going from offline experimentation to live A/B test in 5 months. The system combined collaborative filtering (ma..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_8ad07b17b8cf` — senior_explicit_ai (Tier A)

- Occurrences: 12 (current role: 4) | archetype purity: 1.000
- Compounds: `end_to_end_intelligence_ownership`, `evaluated_ranking_system`, `production_embeddings_retrieval`, `production_vector_or_hybrid_search`, `shipper_with_evaluation_depth`

Text:

> Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product. The architecture combined BM25 + dense retrieval (BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on the top-50, falling back to a learning-to-rank model when latency budget was tight. Designed the offline evaluation framework from scratch — NDCG, MRR, recall@K calibrated against online A/B engagement metrics. Drove the migration over 4 months including the recruiter-feedback loop that surfaced reranking edge cases.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embeddings`, `BGE embeddings`
    - snippet: "...search product. The architecture combined BM25 + dense retrieval (BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on the top-50, falling back..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `NDCG`, `MRR`, `recall@K`, `evaluation framework`, `online A/B engagement metrics`
    - snippet: "...t was tight. Designed the offline evaluation framework from scratch — NDCG, MRR, recall@K calibrated against online A/B engagement metrics. Drov..."
  - `retrieval_search` (Retrieval or search systems) — matched: `retrieval`, `search product`, `RAG-based`, `BM25`
    - snippet: "...cruiter-facing search product. The architecture combined BM25 + dense retrieval (BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on the top-5..."
  - `vector_hybrid_infrastructure` (Vector or hybrid-search infrastructure) — matched: `FAISS`, `BM25 + dense`
    - snippet: "...ct. The architecture combined BM25 + dense retrieval (BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on the top-50, falling back to a le..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `50M+ queries`
    - snippet: "Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product. The archit..."
  - `online_experimentation` (Online experimentation) — matched: `recruiter-feedback loop`
    - snippet: "...B engagement metrics. Drove the migration over 4 months including the recruiter-feedback loop that surfaced reranking edge cases."
  - `operational_ownership` (Operational ownership) — matched: `latency`
    - snippet: "...e-ranker on the top-50, falling back to a learning-to-rank model when latency budget was tight. Designed the offline evaluation framework from scra..."
  - `product_context` (Product context) — matched: `product`, `recruiter-facing`
    - snippet: "...erving 50M+ queries per month for an internal recruiter-facing search product. The architecture combined BM25 + dense retrieval (BGE embeddings, FA..."
  - `production_delivery` (Production delivery) — matched: `serving 50M+ queries`
    - snippet: "Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product. The archit..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `ranker`, `reranking`
    - snippet: "Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-fac..."
- **Preferred**
  - `learning_to_rank` (Learning to rank) — matched: `learning-to-rank`
    - snippet: "...SS HNSW) with an LLM-based re-ranker on the top-50, falling back to a learning-to-rank model when latency budget was tight. Designed the offline evaluation..."
  - `recruiting_marketplace` (Recruiting, HR-tech, or marketplace context) — matched: `recruiter`
    - snippet: "...based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product. The architecture combined BM25 + dense retriev..."
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `from scratch`
    - snippet: "...n latency budget was tight. Designed the offline evaluation framework from scratch — NDCG, MRR, recall@K calibrated against online A/B engagement metric..."
- **Risk context**
  - `llm_application_context` (LLM application or RAG context) — matched: `RAG-based`, `LLM-based re-ranker`
    - snippet: "Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recru..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_c99d19052bf7` — senior_explicit_ai (Tier A)

- Occurrences: 12 (current role: 3) | archetype purity: 1.000
- Compounds: `end_to_end_intelligence_ownership`, `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Fine-tuned LLaMA-2-7B and Mistral-7B variants using LoRA and QLoRA for domain-specific candidate-JD matching. Built the data curation pipeline that generated 200K high-quality preference pairs from recruiter labels, plus the eval harness using both ranking metrics and human-quality scores. Deployed the model via BentoML on Kubernetes with sub-200ms p95 latency by quantizing to INT8 and batching at the request level. Cost per inference dropped from $0.04 with GPT-3.5-fallback to under $0.001.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `eval harness`
    - snippet: "...ed 200K high-quality preference pairs from recruiter labels, plus the eval harness using both ranking metrics and human-quality scores. Deployed the mod..."
  - `retrieval_search` (Retrieval or search systems) — matched: `candidate-JD matching`
    - snippet: "...2-7B and Mistral-7B variants using LoRA and QLoRA for domain-specific candidate-JD matching. Built the data curation pipeline that generated 200K high-quality pr..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `sub-200ms`
    - snippet: "...man-quality scores. Deployed the model via BentoML on Kubernetes with sub-200ms p95 latency by quantizing to INT8 and batching at the request level...."
  - `operational_ownership` (Operational ownership) — matched: `p95`, `latency`
    - snippet: "...y scores. Deployed the model via BentoML on Kubernetes with sub-200ms p95 latency by quantizing to INT8 and batching at the request level. Cost..."
  - `production_delivery` (Production delivery) — matched: `Deployed`
    - snippet: "...the eval harness using both ranking metrics and human-quality scores. Deployed the model via BentoML on Kubernetes with sub-200ms p95 latency by qua..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`
    - snippet: "...ference pairs from recruiter labels, plus the eval harness using both ranking metrics and human-quality scores. Deployed the model via BentoML on K..."
- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `Kubernetes`, `quantizing`, `batching`, `request level`, `sub-200ms`
    - snippet: "...g metrics and human-quality scores. Deployed the model via BentoML on Kubernetes with sub-200ms p95 latency by quantizing to INT8 and batching at the..."
  - `llm_finetuning` (LLM fine-tuning) — matched: `LoRA`, `QLoRA`, `Fine-tuned LLaMA`
    - snippet: "Fine-tuned LLaMA-2-7B and Mistral-7B variants using LoRA and QLoRA for domain-specific candidate-JD matching. Built the data c..."
  - `recruiting_marketplace` (Recruiting, HR-tech, or marketplace context) — matched: `recruiter`, `candidate-JD`
    - snippet: "...ation pipeline that generated 200K high-quality preference pairs from recruiter labels, plus the eval harness using both ranking metrics and human-qu..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_ca4723327469` — applied_ml (Tier A)

- Occurrences: 57 (current role: 17) | archetype purity: 1.000
- Compounds: none

Text:

> Built and operated production ML pipelines using MLflow for experiment tracking, Kubeflow for orchestration, and our internal feature store. My main project was a churn prediction model that's now used by the customer success team to prioritize outreach. Designed the model monitoring stack: data drift detection, prediction distribution checks, and alerting. Mentored a junior engineer through their first end-to-end ML project last year.

Assigned evidence:

- **Core role**
  - `operational_ownership` (Operational ownership) — matched: `drift detection`, `monitoring stack`
    - snippet: "...eam to prioritize outreach. Designed the model monitoring stack: data drift detection, prediction distribution checks, and alerting. Mentored a junior engi..."
  - `production_delivery` (Production delivery) — matched: `production ML`, `now used by`
    - snippet: "Built and operated production ML pipelines using MLflow for experiment tracking, Kubeflow for orchestr..."
- **Preferred**
  - `mentoring_leadership` (Mentoring or technical leadership) — matched: `Mentored`
    - snippet: "...: data drift detection, prediction distribution checks, and alerting. Mentored a junior engineer through their first end-to-end ML project last year..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_773c6b592e7d` — applied_ml (Tier A)

- Occurrences: 58 (current role: 17) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Built a content recommendation system serving 10M+ users that combined collaborative filtering with content-based ranking. The system uses item-item similarity (via sentence-transformer embeddings) for cold starts and a gradient-boosted model trained on engagement signals for warm users. Most of my time went into the feature pipeline (~200 features) and the A/B testing infrastructure. The launch improved 7-day retention by 6% and time spent per session by 14%.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embeddings`, `sentence-transformer`
    - snippet: "...nking. The system uses item-item similarity (via sentence-transformer embeddings) for cold starts and a gradient-boosted model trained on engagement s..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `A/B testing infrastructure`
    - snippet: "...ost of my time went into the feature pipeline (~200 features) and the A/B testing infrastructure. The launch improved 7-day retention by 6% and time spent per session..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `10M+ users`
    - snippet: "Built a content recommendation system serving 10M+ users that combined collaborative filtering with content-based ranking. The..."
  - `online_experimentation` (Online experimentation) — matched: `A/B testing`
    - snippet: "...ost of my time went into the feature pipeline (~200 features) and the A/B testing infrastructure. The launch improved 7-day retention by 6% and time sp..."
  - `production_delivery` (Production delivery) — matched: `serving 10M+ users`, `launch improved`
    - snippet: "Built a content recommendation system serving 10M+ users that combined collaborative filtering with content-based ranking. The..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `recommendation system`
    - snippet: "...g 10M+ users that combined collaborative filtering with content-based ranking. The system uses item-item similarity (via sentence-transformer embed..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_7d9e0102760d` — applied_ml (Tier A)

- Occurrences: 60 (current role: 20) | archetype purity: 1.000
- Compounds: `production_embeddings_retrieval`, `production_vector_or_hybrid_search`, `shipper_with_evaluation_depth`

Text:

> Implemented a RAG-based customer support chatbot integrated with our existing ticketing system. Built the document ingestion pipeline (chunking, embedding via OpenAI embeddings, storing in Pinecone) and the answer-generation layer (initially GPT-4, then a fine-tuned smaller model for cost control). Designed the evaluation framework with both automatic metrics (BLEU, ROUGE) and human-in-the-loop quality scores. Deployment cut average ticket resolution time by 31% for the supported categories.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `embedding`
    - snippet: "...ng ticketing system. Built the document ingestion pipeline (chunking, embedding via OpenAI embeddings, storing in Pinecone) and the answer-generation..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `evaluation framework`
    - snippet: "...PT-4, then a fine-tuned smaller model for cost control). Designed the evaluation framework with both automatic metrics (BLEU, ROUGE) and human-in-the-loop quali..."
  - `retrieval_search` (Retrieval or search systems) — matched: `RAG-based`
    - snippet: "Implemented a RAG-based customer support chatbot integrated with our existing ticketing syste..."
  - `vector_hybrid_infrastructure` (Vector or hybrid-search infrastructure) — matched: `Pinecone`
    - snippet: "...stion pipeline (chunking, embedding via OpenAI embeddings, storing in Pinecone) and the answer-generation layer (initially GPT-4, then a fine-tuned..."
- **Core role**
  - `production_delivery` (Production delivery) — matched: `Deployment`
    - snippet: "...automatic metrics (BLEU, ROUGE) and human-in-the-loop quality scores. Deployment cut average ticket resolution time by 31% for the supported categorie..."
- **Preferred**
  - `llm_finetuning` (LLM fine-tuning) — matched: `fine-tuned smaller model`
    - snippet: "...in Pinecone) and the answer-generation layer (initially GPT-4, then a fine-tuned smaller model for cost control). Designed the evaluation framework with both automa..."
- **Risk context**
  - `llm_application_context` (LLM application or RAG context) — matched: `RAG-based`, `OpenAI embeddings`, `GPT-4`, `answer-generation layer`
    - snippet: "Implemented a RAG-based customer support chatbot integrated with our existing ticketing syste..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_7916db772044` — applied_ml (Tier A)

- Occurrences: 64 (current role: 27) | archetype purity: 1.000
- Compounds: none

Text:

> Developed a semantic search feature for an internal knowledge base of ~500K documents. Used sentence-transformers (all-MiniLM-L6-v2 initially, later upgraded to bge-base) with FAISS for fast nearest-neighbor retrieval. Designed the query expansion module that handles vocabulary mismatch between user queries and document terms. Reported search-relevance improvement of 35% over the prior Elasticsearch BM25 setup, validated through human relevance judgments.

Assigned evidence:

- **Direct requirement**
  - `embeddings` (Embeddings experience) — matched: `sentence-transformers`, `bge-base`
    - snippet: "...earch feature for an internal knowledge base of ~500K documents. Used sentence-transformers (all-MiniLM-L6-v2 initially, later upgraded to bge-base) with FAISS f..."
  - `ranking_evaluation` (Ranking evaluation) — matched: `human relevance judgments`
    - snippet: "...ent of 35% over the prior Elasticsearch BM25 setup, validated through human relevance judgments."
  - `retrieval_search` (Retrieval or search systems) — matched: `retrieval`, `semantic search`, `search feature`, `BM25`
    - snippet: "...lly, later upgraded to bge-base) with FAISS for fast nearest-neighbor retrieval. Designed the query expansion module that handles vocabulary mismatch..."
  - `vector_hybrid_infrastructure` (Vector or hybrid-search infrastructure) — matched: `FAISS`, `Elasticsearch`, `nearest-neighbor`
    - snippet: "...formers (all-MiniLM-L6-v2 initially, later upgraded to bge-base) with FAISS for fast nearest-neighbor retrieval. Designed the query expansion mod..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_fe1930819d75` — applied_ml (Tier A)

- Occurrences: 65 (current role: 28) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`, `shipper_with_evaluation_depth`

Text:

> Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed features across three families: content metadata, user behavior signals, and item engagement history. Owned the offline-online correlation analysis that determined which offline metrics actually predicted A/B test outcomes. Worked closely with PMs to define the optimization target (click-through vs. dwell time vs. downstream conversion) — that work was as important as the modeling itself.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `offline-online correlation`, `offline metrics`, `A/B test outcomes`
    - snippet: "...tadata, user behavior signals, and item engagement history. Owned the offline-online correlation analysis that determined which offline metrics actually predicted A/B..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `A/B test`
    - snippet: "...ion analysis that determined which offline metrics actually predicted A/B test outcomes. Worked closely with PMs to define the optimization target (..."
  - `product_context` (Product context) — matched: `product`
    - snippet: "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed features across..."
  - `production_delivery` (Production delivery) — matched: `shipped`
    - snippet: "Trained and shipped multiple ranking models for our product's discovery feed using XGBoos..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `discovery feed`
    - snippet: "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. D..."
- **Preferred**
  - `learning_to_rank` (Learning to rank) — matched: `ranking models`
    - snippet: "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_71f8d5722d94` — applied_ml (Tier A)

- Occurrences: 78 (current role: 41) | archetype purity: 1.000
- Compounds: `evaluated_ranking_system`

Text:

> Owned the ranking layer for an e-commerce search product, evolving it from a hand-tuned scoring function to a learning-to-rank model over 9 months. Designed the relevance labeling pipeline (mix of click-through data and explicit human judgments), the feature pipeline, and the training/eval workflow. Most of the work was infrastructure and data quality — the modeling part was almost the easy bit. Final model improved revenue-per-search by 12%.

Assigned evidence:

- **Direct requirement**
  - `ranking_evaluation` (Ranking evaluation) — matched: `eval workflow`, `relevance labeling`
    - snippet: "...and explicit human judgments), the feature pipeline, and the training/eval workflow. Most of the work was infrastructure and data quality — the modeling..."
  - `retrieval_search` (Retrieval or search systems) — matched: `search product`
    - snippet: "Owned the ranking layer for an e-commerce search product, evolving it from a hand-tuned scoring function to a learning-to-rank..."
- **Core role**
  - `product_context` (Product context) — matched: `product`, `e-commerce`
    - snippet: "Owned the ranking layer for an e-commerce search product, evolving it from a hand-tuned scoring function to a learning-to-rank..."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`
    - snippet: "Owned the ranking layer for an e-commerce search product, evolving it from a hand-tuned..."
- **Preferred**
  - `learning_to_rank` (Learning to rank) — matched: `learning-to-rank`
    - snippet: "...e search product, evolving it from a hand-tuned scoring function to a learning-to-rank model over 9 months. Designed the relevance labeling pipeline (mix of..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

## Tier C

### `career_c27299c429d2` — generic_ml (Tier C)

- Occurrences: 389 (current role: 187) | archetype purity: 1.000
- Compounds: none

Text:

> Contributed to ML feature engineering and model deployment for a fraud-detection product. My main role was engineering: building the Flask-based prediction API, integrating with the feature store, and writing the model-serving observability layer. I worked closely with senior data scientists but my own modeling work was secondary — I was the production-side engineer.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `Flask`
    - snippet: "...a fraud-detection product. My main role was engineering: building the Flask-based prediction API, integrating with the feature store, and writing..."
- **Core role**
  - `operational_ownership` (Operational ownership) — matched: `observability layer`, `observability`
    - snippet: "...PI, integrating with the feature store, and writing the model-serving observability layer. I worked closely with senior data scientists but my own modeling wor..."
  - `product_context` (Product context) — matched: `product`
    - snippet: "...to ML feature engineering and model deployment for a fraud-detection product. My main role was engineering: building the Flask-based prediction AP..."
  - `production_delivery` (Production delivery) — matched: `deployment`
    - snippet: "Contributed to ML feature engineering and model deployment for a fraud-detection product. My main role was engineering: building..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_46cac11f03b0` — generic_ml (Tier C)

- Occurrences: 369 (current role: 166) | archetype purity: 1.000
- Compounds: none

Text:

> Built recommendation-style features at a mid-stage startup — lighter weight than ranking systems at FAANG, but production. Used a combination of collaborative filtering (matrix factorization in implicit-feedback library) and gradient-boosted re-ranking over engagement signals. Pure ML side of the work; production deployment was handled by the platform team.

Assigned evidence:

- **Core role**
  - `production_delivery` (Production delivery) — matched: `production deployment`, `deployment`
    - snippet: "...boosted re-ranking over engagement signals. Pure ML side of the work; production deployment was handled by the platform team."
  - `ranking_recommendation_matching` (Ranking, recommendation, or matching) — matched: `ranking`, `re-ranking`, `recommendation`
    - snippet: "...mendation-style features at a mid-stage startup — lighter weight than ranking systems at FAANG, but production. Used a combination of collaborative..."
- **Preferred**
  - `learning_to_rank` (Learning to rank) — matched: `gradient-boosted re-ranking`
    - snippet: "...ive filtering (matrix factorization in implicit-feedback library) and gradient-boosted re-ranking over engagement signals. Pure ML side of the work; production deploym..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_0e7ae654f5d1` — generic_ml (Tier C)

- Occurrences: 366 (current role: 163) | archetype purity: 1.000
- Compounds: none

Text:

> Built computer vision models for our product's image moderation feature using PyTorch — fine-tuned ResNet variants on a labeled dataset of ~200K images. Set up the training pipeline (data loading, augmentation, evaluation) and the inference service. Most of my project work has been in CV; I'm now interested in transitioning toward NLP/LLM work but my professional experience there is limited.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `product`
    - snippet: "Built computer vision models for our product's image moderation feature using PyTorch — fine-tuned ResNet variants..."
  - `production_delivery` (Production delivery) — matched: `inference service`
    - snippet: "...he training pipeline (data loading, augmentation, evaluation) and the inference service. Most of my project work has been in CV; I'm now interested in transi..."
- **Risk context**
  - `computer_vision_primary` (Computer-vision-primary background) — matched: `computer vision`, `Most of my project work has been in CV`, `ResNet`, `image moderation`
    - snippet: "Built computer vision models for our product's image moderation feature using PyTorch — fin..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_5be35db595d9` — generic_ml (Tier C)

- Occurrences: 363 (current role: 166) | archetype purity: 1.000
- Compounds: none

Text:

> Worked on time-series forecasting models for supply-chain demand prediction at a logistics company. Built models in Prophet, LightGBM, and (for one project) a small LSTM — the LightGBM model ended up shipping. Also ran some reinforcement learning experiments for dynamic pricing but those didn't make it to production. The work was a mix of modeling, analysis, and stakeholder communication with the operations team.

Assigned evidence:

- **Core role**
  - `production_delivery` (Production delivery) — matched: `ended up shipping`
    - snippet: "...et, LightGBM, and (for one project) a small LSTM — the LightGBM model ended up shipping. Also ran some reinforcement learning experiments for dynamic pricing..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_03ab1210df1d` — generic_ml (Tier C)

- Occurrences: 359 (current role: 156) | archetype purity: 1.000
- Compounds: none

Text:

> Worked on customer-facing predictive modeling for an e-commerce platform — churn prediction, conversion likelihood, lifetime value estimation. Used scikit-learn and XGBoost; main models were gradient-boosted trees with ~80 hand-engineered features. The work was split roughly 60/40 between modeling and data prep / SQL. The churn model is now used by the retention team, though my role was more on the modeling side than the productionization.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `scikit-learn`
    - snippet: "...rn prediction, conversion likelihood, lifetime value estimation. Used scikit-learn and XGBoost; main models were gradient-boosted trees with ~80 hand-en..."
- **Core role**
  - `product_context` (Product context) — matched: `e-commerce`, `customer-facing`
    - snippet: "Worked on customer-facing predictive modeling for an e-commerce platform — churn prediction, conversion likelihood, lifetime value es..."
  - `production_delivery` (Production delivery) — matched: `now used by`
    - snippet: "...oughly 60/40 between modeling and data prep / SQL. The churn model is now used by the retention team, though my role was more on the modeling side than..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_551a0361dd79` — generic_ml (Tier C)

- Occurrences: 328 (current role: 162) | archetype purity: 1.000
- Compounds: none

Text:

> Built NLP pipelines for sentiment analysis and document classification — primarily for an internal feedback-analytics dashboard. Started with sklearn-based bag-of-words models, then moved to transformer-based classifiers (DistilBERT) for the harder classes. Comfortable with PyTorch and Hugging Face but most of my training experience has been on small datasets and pre-trained model fine-tuning, not from-scratch model design.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `sklearn`
    - snippet: "...primarily for an internal feedback-analytics dashboard. Started with sklearn-based bag-of-words models, then moved to transformer-based classifier..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

## Tier B

### `career_a0675da68d85` — data_backend_adjacent (Tier B)

- Occurrences: 1,854 (current role: 863) | archetype purity: 1.000
- Compounds: none

Text:

> Designed and maintained the analytical data warehouse on Snowflake supporting the BI team's ~50 dashboards. Wrote complex SQL — heavy on window functions, CTEs, and incremental modeling patterns via dbt. Worked on the data modeling side (dimensional modeling, slowly changing dimensions) as well as performance optimization (query tuning, cluster sizing, materialized views). Also built the lineage and documentation framework now in use across the data org.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_73ccc253c91b` — data_backend_adjacent (Tier B)

- Occurrences: 1,836 (current role: 816) | archetype purity: 1.000
- Compounds: none

Text:

> Built and maintained data pipelines on Apache Airflow processing ~500GB of daily transactional data across 12 source systems. Worked extensively with Spark (PySpark) for batch processing and dbt for the transformation/modeling layer in our Snowflake warehouse. Owned the on-call rotation for data quality issues — wrote most of the data quality checks that detect schema drift and unusual volume changes. The pipeline supports the analytics team and a few internal ML models.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `PySpark`
    - snippet: "...ctional data across 12 source systems. Worked extensively with Spark (PySpark) for batch processing and dbt for the transformation/modeling layer i..."
- **Core role**
  - `meaningful_scale` (Meaningful operating scale) — matched: `500GB of daily`
    - snippet: "Built and maintained data pipelines on Apache Airflow processing ~500GB of daily transactional data across 12 source systems. Worked extensively with..."
  - `operational_ownership` (Operational ownership) — matched: `on-call`, `data quality checks`
    - snippet: "...e transformation/modeling layer in our Snowflake warehouse. Owned the on-call rotation for data quality issues — wrote most of the data quality che..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_2e516f229493` — data_backend_adjacent (Tier B)

- Occurrences: 1,823 (current role: 867) | archetype purity: 1.000
- Compounds: none

Text:

> Backend + data hybrid role at a growth-stage startup. Built the company's first proper data warehouse (migrating from a tangled set of Postgres replicas to a clean Snowflake setup with dbt), the orchestration layer (Airflow), and the BI integration (Looker). Shipped a couple of small predictive features but the bulk of the role was data infrastructure.

Assigned evidence:

- **Core role**
  - `production_delivery` (Production delivery) — matched: `Shipped`
    - snippet: "..., the orchestration layer (Airflow), and the BI integration (Looker). Shipped a couple of small predictive features but the bulk of the role was da..."
- **Preferred**
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `company's first`
    - snippet: "Backend + data hybrid role at a growth-stage startup. Built the company's first proper data warehouse (migrating from a tangled set of Postgres repli..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_a95b2e71340a` — data_backend_adjacent (Tier B)

- Occurrences: 1,814 (current role: 811) | archetype purity: 1.000
- Compounds: none

Text:

> Implemented streaming data pipelines on Kafka and Spark Streaming for a real-time user-activity processing platform. Designed the schema-registry integration, the watermark/state management approach, and the deduplication logic for late-arriving events. Worked closely with the data science team to make sure feature pipelines aligned with what their models needed. Most of my career has been data engineering, with some adjacent ML exposure.

Assigned evidence:

- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `Kafka`, `Spark Streaming`
    - snippet: "Implemented streaming data pipelines on Kafka and Spark Streaming for a real-time user-activity processing platform..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_d6ac6a7f230c` — data_backend_adjacent (Tier B)

- Occurrences: 1,807 (current role: 816) | archetype purity: 1.000
- Compounds: none

Text:

> Mixed data science and analytics-engineering role at a marketing-analytics startup. Spent maybe 30% of my time on lightweight ML (clustering, classification, churn prediction in sklearn/XGBoost) and 70% on data infrastructure and dashboards. Comfortable with the modeling work but I wouldn't call myself an ML specialist. Built our experimentation framework that supports the product team's A/B tests.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `sklearn`
    - snippet: "...me on lightweight ML (clustering, classification, churn prediction in sklearn/XGBoost) and 70% on data infrastructure and dashboards. Comfortable w..."
- **Core role**
  - `online_experimentation` (Online experimentation) — matched: `A/B tests`
    - snippet: "...Built our experimentation framework that supports the product team's A/B tests."
  - `product_context` (Product context) — matched: `product`
    - snippet: "...ML specialist. Built our experimentation framework that supports the product team's A/B tests."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_9ab513003702` — data_backend_adjacent (Tier B)

- Occurrences: 1,790 (current role: 827) | archetype purity: 1.000
- Compounds: none

Text:

> Backend development with Python (FastAPI), PostgreSQL, and Redis at a B2B SaaS product. Owned the analytics-and-reporting service which serves dashboards to ~3K paying customers. Recent work includes integrating a model-serving service (built by another team) into our API layer; my work was the integration and observability, not the model itself. Strong on API design, database performance, and reliability engineering.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `Python`, `FastAPI`
    - snippet: "Backend development with Python (FastAPI), PostgreSQL, and Redis at a B2B SaaS product. Owned the ana..."
- **Core role**
  - `operational_ownership` (Operational ownership) — matched: `observability`
    - snippet: "...by another team) into our API layer; my work was the integration and observability, not the model itself. Strong on API design, database performance, an..."
  - `product_context` (Product context) — matched: `product`, `SaaS`, `paying customers`
    - snippet: "...evelopment with Python (FastAPI), PostgreSQL, and Redis at a B2B SaaS product. Owned the analytics-and-reporting service which serves dashboards to..."
- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `reliability engineering`
    - snippet: "...not the model itself. Strong on API design, database performance, and reliability engineering."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_87a46a63aede` — general_software (Tier B)

- Occurrences: 10,125 (current role: 4,230) | archetype purity: 1.000
- Compounds: none

Text:

> Cloud infrastructure and DevOps work at an enterprise SaaS company. Owned the AWS account architecture (VPC, IAM, networking), the Terraform modules for our service deployments, and the Kubernetes cluster operations. Designed the CI/CD pipelines (GitLab CI + ArgoCD) and the monitoring stack (Prometheus, Grafana, Loki). Strong on the infra and ops side; haven't done much application development.

Assigned evidence:

- **Core role**
  - `operational_ownership` (Operational ownership) — matched: `monitoring stack`
    - snippet: "...operations. Designed the CI/CD pipelines (GitLab CI + ArgoCD) and the monitoring stack (Prometheus, Grafana, Loki). Strong on the infra and ops side; haven'..."
  - `product_context` (Product context) — matched: `SaaS`
    - snippet: "Cloud infrastructure and DevOps work at an enterprise SaaS company. Owned the AWS account architecture (VPC, IAM, networking), t..."
- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `Kubernetes`
    - snippet: "...tworking), the Terraform modules for our service deployments, and the Kubernetes cluster operations. Designed the CI/CD pipelines (GitLab CI + ArgoCD)..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_55e5e0725eda` — general_software (Tier B)

- Occurrences: 10,055 (current role: 4,241) | archetype purity: 1.000
- Compounds: none

Text:

> Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `consumer-app`
    - snippet: "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including..."
  - `production_delivery` (Production delivery) — matched: `production features`
    - snippet: "...ntly) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the o..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_7a9b4a7d5a75` — general_software (Tier B)

- Occurrences: 10,025 (current role: 4,163) | archetype purity: 1.000
- Compounds: none

Text:

> Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft — accessibility, performance, animations — but limited backend exposure.

Assigned evidence:

- **Preferred**
  - `zero_to_one_ownership` (Zero-to-one or end-to-end ownership) — matched: `from scratch`, `led the migration`
    - snippet: "...g tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the fron..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_af0ab8d8a342` — general_software (Tier B)

- Occurrences: 10,015 (current role: 4,100) | archetype purity: 1.000
- Compounds: none

Text:

> Java backend development at a large enterprise — Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks.

Assigned evidence:

- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `distributed systems`, `Kafka`
    - snippet: "...the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_8f5eedb01688` — general_software (Tier B)

- Occurrences: 9,911 (current role: 4,164) | archetype purity: 1.000
- Compounds: none

Text:

> Full-stack web application development at a SaaS company. Built React-based admin interfaces and the Node.js REST API backing them. Worked across the stack: frontend components, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web stack though my comfort zone is the backend and database side. Recent learning has been on the testing and CI/CD discipline.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `SaaS`
    - snippet: "Full-stack web application development at a SaaS company. Built React-based admin interfaces and the Node.js REST API..."
  - `production_delivery` (Production delivery) — matched: `deployment`
    - snippet: "...stack: frontend components, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web sta..."
- **Preferred**
  - `distributed_inference` (Distributed systems or inference optimization) — matched: `Kubernetes`
    - snippet: "...nents, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web stack though my comfort z..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_1d67f17f78c5` — general_software (Tier B)

- Occurrences: 9,785 (current role: 4,102) | archetype purity: 1.000
- Compounds: none

Text:

> Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team — moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering.

Assigned evidence:

- **Direct requirement**
  - `python_engineering` (Python engineering) — matched: `pytest`
    - snippet: "...ct. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with develo..."
- **Core role**
  - `product_context` (Product context) — matched: `product`
    - snippet: "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and py..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_12b13980ad1d` — general_professional (Tier B)

- Occurrences: 25,515 (current role: 7,770) | archetype purity: 0.921
- Compounds: none

Text:

> Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_035626b6b33e` — general_professional (Tier B)

- Occurrences: 25,290 (current role: 7,605) | archetype purity: 0.920
- Compounds: none

Text:

> Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `product`, `SaaS`
    - snippet: "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 ticket..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_a4f0fbc7e63b` — general_professional (Tier B)

- Occurrences: 25,237 (current role: 7,638) | archetype purity: 0.919
- Compounds: none

Text:

> Marketing leadership role at a B2B SaaS company. Owned the demand-generation function — content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `SaaS`
    - snippet: "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function — content marketing, pa..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_5a9f2eac4d01` — general_professional (Tier B)

- Occurrences: 25,207 (current role: 7,755) | archetype purity: 0.922
- Compounds: none

Text:

> Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited.

Assigned evidence:

- **Risk context**
  - `consulting_services_context` (Consulting or services context) — matched: `consulting firm`, `consulting toolkit`, `clients`, `advisory`
    - snippet: "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business di..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_3d9f31f6db0e` — general_professional (Tier B)

- Occurrences: 25,164 (current role: 7,619) | archetype purity: 0.920
- Compounds: none

Text:

> Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_91d9a2d3c529` — general_professional (Tier B)

- Occurrences: 25,104 (current role: 7,518) | archetype purity: 0.919
- Compounds: none

Text:

> Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up.

Assigned evidence:

- **Core role**
  - `product_context` (Product context) — matched: `product`
    - snippet: "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecy..."

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_1b5ff6cb1b66` — general_professional (Tier B)

- Occurrences: 25,078 (current role: 7,658) | archetype purity: 0.923
- Compounds: none

Text:

> Senior accounting role at a mid-sized company — month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_fa678c2bc44f` — general_professional (Tier B)

- Occurrences: 25,071 (current role: 7,638) | archetype purity: 0.920
- Compounds: none

Text:

> Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics — including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---

### `career_2d475ce2e723` — general_professional (Tier B)

- Occurrences: 25,029 (current role: 7,620) | archetype purity: 0.921
- Compounds: none

Text:

> Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months.

Assigned evidence:

- (no signals assigned)

Review:

- False positives to remove: 
- Missing evidence (false negatives): 
- Verdict: [ ] correct  [ ] fix rubric

---
