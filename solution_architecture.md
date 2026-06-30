# Solution Architecture — General JD→Candidate Ranking System

Status: implementation started in `solution/`. The submitted solution is a **general
system that takes any JD + candidate pool and returns a trustworthy shortlist** by
understanding the role and weighing demonstrated career evidence. The released
Senior-AI-Engineer JD and the 100k pool are one *instance*; the JD is an **input**, parsed
at run time, never hard-coded.

## 1. Non-negotiable design principles (learned, not optional)

1. **Career-demonstrated work > self-declared skills > semantic surface match.** The JD
   says the keyword-richest skills sections are a trap; the ranker must reflect that order.
2. **Integrity / honeypot filtering is a HARD deterministic gate** — never learned, never
   soft-scored. Embeddings and LLMs cannot catch "8 years at a company founded 3 years
   ago"; only dated chronology checks can. >10% honeypots in top-100 = disqualification.
3. **Behavior is a bounded modifier** applied after static relevance, capped, peer-normalized
   for large cohorts, near-zero for the tiny senior cohorts (no stable baseline there).
4. **Semantic matching is a bounded recall aid, not precision.** The active solution uses a
   lightweight career-weighted lexical semantic fallback; embedding experiments are kept as
   diagnostics because they produced the same top-100 set while adding model-artifact
   complexity. Semantic score must not outrank demonstrated evidence.
5. **No training labels required.** Embeddings (unsupervised similarity) + evidence rules +
   integrity gate need no labels.
6. **Local proxy labels are evaluation-only.** They can test regressions during development,
   but the submitted ranker must derive scores from the JD and candidate records.

## 2. Compute compliance

- **Precompute (offline, unlimited time, allowed by spec §10.3):** candidate feature table
  with career evidence, skill evidence, integrity flags, behavior/logistics overlays, and
  cached semantic tokens.
- **Ranking step (≤5 min wall, ≤16 GB RAM, CPU-only, no network):** parse the JD, load
  precomputed features, score, gate, rank, write CSV + reasoning.
- **Disk:** the feature table is large but still within the challenge artifact budget; no
  model weights are needed for the active ranking path.
- Declare `pre_computation_required: true` if the precomputed feature artifact is shipped.

## 3. Pipeline

```
            JOB DESCRIPTION (input)
                    |
   [Stage 0] JD Understanding (precompute, once per JD)
                    |
        requirement_spec.json + semantic aspect queries
                    |
candidates.jsonl -> [Stage 1] Offline precompute
                    |   - semantic token cache (career-weighted)
                    |   - candidate feature table (evidence, integrity, behavior)
                    v
        [Stage 2] Ranking step (<=5 min, CPU, no network)
          1 parse JD + aspect sub-queries
          2 semantic score   (bounded recall aid)
          3 evidence score   (career > skills; driven by requirement_spec)
          4 seniority alignment (JD-derived level x IC/management track)
          5 behavior/logistics modifiers (bounded)
          6 HARD integrity gate (honeypots/disqualifiers removed)
          7 hybrid combine -> final score
          8 rank -> top 100 + grounded reasoning
                    |
            submission.csv  ->  [Stage 3] Validation + local audit
```

## 4. Component detail

### Stage 0 — JD Understanding (the general interface)
Parse the JD into a structured `requirement_spec` (LLM-assisted offline, or rule-based).
This is what makes the system general: swap the JD, regenerate the spec, re-rank.

`requirement_spec.json` (schema):
```json
{
  "role_title": "Senior AI Engineer",
  "seniority": {"min_years": 5, "max_years": 9, "hard": false},
  "must_have": [
    {"id": "prod_retrieval", "desc": "production embeddings/retrieval", "weight": 1.0,
     "evidence_signals": ["embeddings","retrieval_search","production_delivery"],
     "compound": "production_embeddings_retrieval",
     "compounds": [
       "production_embeddings_retrieval",
       "production_vector_or_hybrid_search",
       "end_to_end_intelligence_ownership",
       "evaluated_ranking_system"
     ]}
  ],
  "nice_to_have": [
    {"id": "ltr", "desc": "learning-to-rank", "weight": 0.4,
     "evidence_signals": ["learning_to_rank"]}
  ],
  "hard_disqualifiers": [
    {"id": "services_only", "scope": "entire_career"},
    {"id": "research_only_no_prod", "scope": "entire_career"}
  ],
  "soft_negatives": [{"id": "recent_shallow_llm", "scope": "career_timeline"}],
  "location": {"preferred": ["Pune","Noida","NCR"], "relocate_ok": true},
  "semantic_queries": [
    "built and shipped a production ranking/recommendation system",
    "designed retrieval and evaluation (NDCG/MRR) at scale"
  ]
}
```
Disqualifier/soft-negative *definitions* include scope and guards so a single services or
research role does not incorrectly disqualify an otherwise relevant product engineer.

### Stage 1 — Offline precompute
- **Semantic token text:** weight career-history descriptions > headline/summary > skills
  so semantic matching follows the same career-first hierarchy as evidence scoring.
- **Candidate feature table:** per-candidate evidence signals and compounds, integrity
  flags, behavior overlay, location bucket, and skill signals.
- Commit or regenerate artifacts; record sha256 in a freeze manifest before final submit.

### Stage 2 — Ranking step
1. **Parse JD aspect queries** from the role description and requirement spec.
2. **Semantic score** = career-weighted token coverage against JD aspects. This is capped
   and cannot make a candidate eligible by itself.
3. **Evidence score** = weighted match of candidate evidence to `requirement_spec`
   must/nice items. Each capability can define multiple satisfying compounds, so a
   candidate who demonstrates the same underlying capability through end-to-end ownership or
   evaluated ranking systems is not under-scored just because the career text names a
   different implementation route. Signal-only matches remain partial; skills count least,
   only as a capped trust bump (tested > listed).
4. **Seniority alignment** = JD-derived level x track fit, weighted by demonstrated
   ownership/scope. A second capped ordering term normalizes positive fit so senior IC
   builders rise for senior IC JDs without hard-coding a cohort prior.
5. **Role-title ordering alignment** = for senior IC JDs, a capped title-family/function
   nudge when the candidate is already evidence-qualified, has demonstrated ownership, and
   explicitly carries a senior/staff/lead/principal technical title matching the JD role
   family. This moves the top slots toward the JD's title intent without admitting weak
   profiles.
6. **Behavior/logistics modifiers** = bounded signals applied after static relevance.
7. **Hard integrity gate** = drop/zero any candidate with a honeypot proxy
   (company-pre-founding, tech-before-release-in-career-text) or a hard disqualifier.
   Runs before the top-100 cut; the run asserts no unsafe candidate is in the top 100.
8. **Hybrid combine:** evidence is dominant; semantic, skills, seniority, behavior,
   logistics, and soft negatives are bounded terms. Integrity is a filter, not a term.
9. **Reasoning:** grounded strictly in the candidate's own fields (title, years, named
   skills, matched evidence, concerns) — specific, honest, rank-consistent.

### Stage 3 — Validation and local audit
Keep two separate checks:

- **General validator (`solution.validate_output`)**: submission columns, exactly 100 rows,
  unique ranks and candidate IDs, candidate IDs present in the input universe, finite
  non-increasing scores, and non-empty reasoning. This is JD-agnostic and belongs to the
  submission-facing solution.
- **Local benchmark audit (`analysis.solution_dataset_audit`)**: synthetic archetype mix,
  proxy-overlap counts, and dataset-specific leak checks. This is a development diagnostic
  only; it is not part of the general ranker contract and should not be described as how the
  solution works.
- **Counterfactual tests:** remove career evidence (score must drop), swap a technical title
  for an irrelevant title while keeping skills (must drop), inject an impossible employment
  date (must be gated), and simulate 6-month inactivity (mild drop). Direction and bounded
  magnitude must be correct.
- **Reasoning audit:** sample 10 rows and confirm every explanation is grounded in candidate
  fields, not private proxy labels.

## 5. Reuse map (most of the work already exists and is general)

| Existing asset | Role in new system |
|---|---|
| `analysis/integrity_checks.py` | The hard integrity gate — used directly, JD-agnostic |
| `solution/jd_parser.py` | JD-to-requirement-spec interface |
| `solution/candidate_features.py` | Candidate feature table from raw records |
| `solution/ranker.py` | Submission-facing ranker |
| freeze manifest pattern | Hash-verified artifacts + reproducible entrypoint |

What is not in the submitted path: dataset generator priors or hidden-label assumptions.
Those remain development diagnostics only.

## 6. Build milestones

1. `requirement_spec` schema + a generated spec for the released JD (the general interface).
2. Precompute candidate feature JSONL with career-weighted semantic tokens.
3. Semantic scoring module with capped career-weighted token coverage.
4. Generalize evidence scoring to consume `requirement_spec`.
5. Hybrid combiner + hard integrity gate + soft-negative caps + reasoning generator.
6. `solution.ranker` entrypoint: load artifacts → rank → CSV; assert budget + honeypot=0.
7. Expand validation beyond `solution.validate_output` with counterfactual tests and a
   reproducibility manifest.
8. Freeze: version-lock, `submission_metadata.yaml` (declare precompute), README with the
   single reproduce command and the precompute script.

## 7. Acceptance criteria (all must hold before submit)

- [ ] Ranking step reproduces in <5 min, <16 GB, CPU-only, no network.
- [ ] Top-100 high-integrity-risk count = 0 under the generic integrity gate.
- [ ] Career evidence dominates: a stuffer (AI skills, irrelevant title, no career evidence)
      does not enter the top 100; a plain-language Tier-5 (career evidence, no buzzwords) does.
- [ ] Counterfactual directions all correct.
- [ ] Reasoning passes the Stage-4 checklist on a 10-row sample.
- [ ] Output validates against `validate_submission.py`.
- [ ] Defensible architecture story (semantic retrieval + evidence + evaluation + integrity)
      with real git history.

## 8. Risk register

| Risk | Mitigation |
|---|---|
| Semantic match ranks keyword-stuffers/honeypots high | Evidence-dominant weights; semantic capped; hard integrity gate |
| Plain-language Tier-5 missed by keyword logic | Multi-compound evidence, ownership signals, and JD-derived seniority alignment |
| Embedding too slow / needs network | Active path does not require embeddings; embedding experiment remains optional |
| Soft-learned integrity leaks a honeypot | Integrity stays a deterministic hard filter, asserted on the top 100 |
| Overfitting to local proxy labels | Proxy labels are a cross-check only; anchor on JD-derived requirements, counterfactuals, and manual audit |
| Stage-3 reproduction of precompute | Commit artifacts + a regeneration script; declare precompute in metadata |

## 9. Fallback

The lightweight lexical semantic scorer is the active path inside the general system. The
embedding scorer remains an optional experiment and should only be adopted if it improves
manual/proxy validation checks without weakening the hard integrity guarantees.
