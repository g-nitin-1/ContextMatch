# Other Ideas for Building a Proxy Ranking

## Important Distinction

The challenge documents reveal only part of the hidden relevance system:

- Honeypots are forced to relevance tier 0.
- Tier 3 or higher is considered relevant for P@10.
- The job description refers to a strong plain-language candidate as Tier 5.
- NDCG is used, which indicates graded relevance rather than only relevant or
  irrelevant labels.

The complete tier definitions, assignment rules, and NDCG gain mapping are not
documented. Any mapping from dataset archetypes to relevance tiers is therefore
a hypothesis, not a known fact.

## Idea 2: Reverse-Engineer the Synthetic Data Generator

Instead of asking a large model to act as the recruiter, attempt to recover the
latent structure used to generate the synthetic candidates and hidden labels.

### Independence Boundary

Idea 2 must be completed and frozen without using:

- Idea 1 teacher judgments
- LLM-generated labels
- Semantic embeddings
- Hidden leaderboard feedback

It may use deterministic parsing, exact-template analysis, structured
statistics, the job description, documented challenge rules, and versioned
external chronology facts. Idea 1 will be built separately after Idea 2 is
frozen. Their rankings will then be compared for agreement and disagreement,
without retroactively tuning Idea 2 to imitate Idea 1.

This may be particularly effective because the dataset contains strong
generator fingerprints:

- 300,171 career entries use only 44 unique career-description templates.
- Candidate summaries occur in several sharply defined archetypes.
- Some archetypes have small, exact-sized populations.
- The challenge explicitly describes keyword stuffers, plain-language Tier 5
  candidates, behavioral twins, and approximately 80 honeypots.

### Observed Profile Archetypes

Preliminary analysis found:

| Profile archetype | Approximate count |
|---|---:|
| Plain-language senior system builders | 8 |
| Explicit senior AI engineers | 21 |
| Applied ML/search/recommendation engineers | 150 |
| Generic ML/data science profiles | 1,000 |
| Data/backend-adjacent profiles | 5,000 |
| General software engineers | 25,000 |
| Remaining mostly irrelevant professions | Approximately 68,000 |

These groups may correlate with hidden relevance tiers, but this must be tested
as a hypothesis rather than treated as ground truth.

## 1. Recover Candidate Archetypes

Canonicalize candidate text before clustering:

- Replace names and candidate IDs.
- Replace company names.
- Replace dates, durations, scale numbers, and percentages.
- Normalize titles and skill synonyms.
- Separate summary, headline, skills, and career descriptions.

Cluster candidates using:

- Exact or near-exact template matching
- Structured co-occurrence of titles, careers, industries, and skills
- Hierarchical clustering of generator-template distributions

The goal is to identify the generator's profile families without allowing
individual candidate details to obscure the shared structure.

### Completed Reconstruction

The deterministic reconstruction currently finds:

- 76 normalized summary templates
- 44 exact career-description templates
- 179 normalized headline templates
- 7 coarse static generator families
- 12 fine static template atoms
- Weak evidence for discrete behavioral classes; behavior is better represented
  as continuous signals plus missing-data patterns
- Four distinct contradiction-mutation families

The seven coarse families recover:

| Reconstructed family | Candidates |
|---|---:|
| Explicit senior AI | 21 |
| Applied ML/search/recommendation | 150 |
| Generic ML/data science | 1,000 |
| Data/backend adjacent | 5,000 |
| General software | 25,000 |
| Plain-language senior systems | 8 |
| General professional/direct occupation branch | 68,821 |

The family layer was selected at `k=7`, the strongest silhouette elbow. The
maximum-silhouette `k=12` solution is retained separately as fine generator
atoms rather than being mistaken for twelve relevance classes.

Generated evidence:

- `artifacts/analysis/generator_reconstruction_report.md`
- `artifacts/analysis/generator_manifest.json`
- `artifacts/analysis/generator_dependencies.json`
- `artifacts/analysis/generator_assignments.csv`

### Completed JD Evidence Catalog

The versioned rubric in `analysis/jd_evidence_rubric.json` now annotates all 44
career templates and aggregates candidate-weighted evidence for the 12 fine
atoms. It records direct requirements, core role evidence, preferred evidence,
risk contexts, exact matched snippets, and same-role compound evidence.

Generated evidence:

- `artifacts/analysis/jd_evidence_catalog.json`
- `artifacts/analysis/jd_evidence_report.md`

The catalog assigns no relevance tier or combined score. Candidate-specific
skills, recency, companies, location, behavior, and integrity remain overlays
for the next stage. Whole-career services-only and research-only conditions,
recent shallow-LLM work, and recent hands-on coding are explicitly reserved for
candidate-level evaluation so a single template context cannot misfire a JD
disqualifier.

## 2. Infer Relevance Distributions, Not Fixed Tiers

Do not immediately assert that an archetype equals one relevance tier. Assign a
probability distribution:

```text
Candidate archetype:
  P(Tier 5) = 0.70
  P(Tier 4) = 0.25
  P(Tier 3) = 0.05
```

The distribution can incorporate:

- Career evidence
- Current and historical titles
- Production ownership
- Ranking and retrieval evidence
- Evaluation experience
- Product-company experience
- JD disqualifiers
- Behavioral availability
- Integrity anomalies

Expected graded relevance can then be calculated across multiple possible tier
gain mappings.

## 3. Build a Honeypot and Integrity Engine

Detect contradictions with deterministic rules:

- Employment before a company was founded
- Role durations inconsistent with dates
- Total career duration inconsistent with years of experience
- Expert skills with zero months of use
- Multiple simultaneous current roles
- Current company or title inconsistent with career history
- Overlapping full-time employment beyond reasonable limits
- Education or employment occurring at impossible ages
- Technology use before the technology existed
- Claimed project scale inconsistent with role seniority or tenure

Some checks require external factual knowledge, such as company founding dates
and technology release dates. Build a versioned local knowledge table so the
ranking process remains reproducible.

Anomaly rules should have confidence levels:

- Hard contradiction: force or strongly suggest Tier 0
- Strong anomaly: large penalty
- Weak anomaly: uncertainty increase only

## 4. Recover Behavioral Latent Factors

The 23 Redrob signals are correlated observations rather than 23 independent
concepts. Model latent factors such as:

- Availability
- Responsiveness
- Recruiter demand
- Platform trust
- Interview reliability
- Mobility and logistical fit

Methods that could recover these factors:

- Exploratory factor analysis
- Principal component analysis after monotonic normalization
- Variational autoencoder for mixed structured data
- Monotonic generalized additive models
- Item-response-style latent variable models

Use domain constraints to orient the factors. For example:

- More recent activity should not reduce availability.
- Higher response rate should not reduce responsiveness.
- Longer notice period should not improve immediate availability.

## 5. Find Behavioral Twins

Search for candidate pairs or groups with nearly identical:

- Profile archetype
- Title and experience
- Career-description templates
- Skills and education

but substantially different behavioral signals.

These matched groups can isolate how the dataset generator intended behavior to
affect ranking. Examples:

- Active versus inactive
- High versus low recruiter response
- Short versus long notice period
- Willing versus unwilling to relocate
- Open versus not open to work

This is more reliable than estimating behavioral weights from unrelated
candidates.

## 6. Analyze Generator Dependencies

Measure which fields were likely generated together:

- Summary archetype versus current title
- Career template versus skill distribution
- Profile quality versus behavioral signals
- Company category versus experience level
- Anomaly type versus profile archetype

Useful tools include:

- Mutual information
- Conditional probability tables
- Bayesian networks
- Hierarchical clustering
- Association-rule mining

This can reveal whether some fields are genuine signals or merely decorative
noise added after the latent candidate type was selected.

## 7. Build an Uncertainty Set of Possible Ground Truths

Do not optimize against one guessed relevance formula. Generate many plausible
ground truths consistent with the documentation and observed data:

- Different archetype-to-tier mappings
- Different NDCG gain mappings
- Different behavioral modifier strengths
- Different treatments of JD disqualifiers
- Different uncertainty around borderline archetypes
- Hard and soft interpretations of anomaly rules

Evaluate each candidate-ranking system across all sampled worlds.

Report:

- Mean proxy score
- Worst-case proxy score
- Score variance
- Probability of outperforming each baseline
- Stability of the top 10 and top 50

Prefer rankers that are consistently strong rather than those that exploit one
specific assumed formula.

## 8. Counterfactual Validation

Create controlled variants of real profiles:

- Replace an ML title with an irrelevant title while preserving keyword skills.
- Remove career evidence but keep self-declared skills.
- Change recent activity to six months of inactivity.
- Increase notice period from 15 to 120 days.
- Introduce an impossible employment date.
- Replace product-company history with services-only history.

A sensible proxy ranker should respond in the expected direction. These tests
do not require hidden labels and can expose incorrect dependencies.

## 9. Baseline Triangulation

Build several intentionally different rankers:

- Title-only
- Skills-only
- Career-template-only
- Behavioral-only
- Deterministic JD rubric
- Generator-archetype model

Analyze agreement and disagreement:

- Candidates selected by every strong method are high-confidence.
- Candidates selected only by skills are likely keyword traps.
- Candidates selected only by template reconstruction may indicate generator
  exploitation.

Consensus is not proof, but it is more reliable than trusting one proxy.

## 10. Compare with Idea 1 Only After Freezing

Idea 2 must first produce a versioned, frozen ranking and all intermediate
evidence. Idea 1 can then independently produce its own ranking.

```text
Frozen Idea 2 ranking
        versus
Independent Idea 1 ranking
        =
Agreement, disagreement, and uncertainty analysis
```

Do not change Idea 2 weights or rules after seeing Idea 1. Differences should be
investigated as evidence:

- Agreement increases confidence.
- Idea 1-only selections may expose semantic evidence missed by reconstruction.
- Idea 2-only selections may expose generator structure missed by the teacher.
- Large disagreements should remain uncertain rather than being silently forced
  into consensus.

## 11. Avoid Overfitting to the Generator

The generator-reconstruction system should primarily be used as an evaluation
and research oracle. A final ranker based only on exact template matching would:

- Generalize poorly to unseen candidate language
- Be difficult to defend as a real recruiting system
- Risk learning accidental synthetic artifacts

The final constrained model should learn general career evidence, relevance,
integrity, and availability concepts.

Use difficult holdouts during development:

- Entire career-description templates
- Entire summary archetypes
- Companies
- Titles
- Anomaly categories

## Recommended Research Order

1. Catalog all text templates and profile archetypes.
2. Implement high-confidence integrity checks.
3. Identify likely honeypots and compare them with documented examples.
4. Find behavioral twins.
5. Reconstruct generator dependencies and mutation families.
6. Construct probabilistic archetype relevance hypotheses.
7. Build several deterministic Idea 2 baseline rankers.
8. Evaluate Idea 2 across many plausible hidden ground truths.
9. Freeze the Idea 2 specification, code, and ranking.
10. Build Idea 1 independently and compare the frozen rankings.

## Main Advantage

This approach tries to recover the process that produced the hidden labels,
rather than asking another model to independently invent relevance judgments.
For a heavily synthetic dataset, that may provide a more reliable proxy.

## Main Risk

The observed templates may not correspond directly to relevance tiers. The
organizers may have applied additional hidden rules, random variation, or
manual adjustments. All reconstructed mappings must therefore remain
probabilistic and should be cross-checked against semantic and factual evidence.
