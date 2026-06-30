# Solution Implementation

This folder contains the submission-facing JD-to-candidate ranking system. It reads a job
description, derives a structured requirement spec, evaluates full candidate profiles, and
writes a ranked shortlist.

Current build status:

- `jd_parser.py` reads `.docx`, `.txt`, or `.md` job descriptions and derives a structured
  requirement spec.
- `requirement_spec.py` validates a structured JD requirement spec.
- `candidate_features.py` extracts career, skill, behavior, logistics, and integrity
  evidence from raw candidate records.
- `precompute.py` caches candidate features and semantic tokens so ranking can run quickly
  for any JD.
- `text_features.py` builds career-weighted candidate text and a lightweight lexical
  semantic fallback.
- `ranker.py` applies the parsed JD spec, hard-gates integrity/disqualifier failures, and
  writes a top-100 CSV.
- The ranker enforces a career-evidence floor: semantic text overlap and skills alone
  cannot make a candidate eligible without JD-relevant technical career evidence.
- Seniority is parsed from the JD as a bounded `level x track` alignment term. It nudges
  evidence-qualified candidates toward the JD's requested level/IC-vs-management track,
  with an additional capped ordering term for candidates whose demonstrated ownership and
  track already fit the JD. It cannot bypass the evidence floor or become a hidden hard
  prior.
- For senior IC JDs, the ranker also applies a capped role-title ordering term when an
  already-qualified candidate has explicit senior/staff/lead/principal title alignment and
  the title matches the JD role family. This is an ordering nudge only, not an eligibility
  gate.

Precompute candidate features once:

```bash
python3 -m solution.precompute \
  --candidates India_runs_data_and_ai_challenge/candidates.jsonl \
  --out artifacts/solution/candidate_features.jsonl
```

Rank for a JD:

```bash
python3 -m solution.ranker \
  --jd India_runs_data_and_ai_challenge/job_description.docx \
  --features artifacts/solution/candidate_features.jsonl \
  --out artifacts/analysis/solution_ranker_submission.csv
```

Validate the ranker output in a JD-agnostic way:

```bash
python3 -m solution.validate_output \
  --submission artifacts/analysis/solution_ranker_submission.csv \
  --features artifacts/solution/candidate_features.jsonl
```

The command prints the total candidates scanned, eligible/blocked counts, elapsed wall
time, and maximum memory used.

Dataset-specific sanity checks live outside this package, for example
`analysis/solution_dataset_audit.py`. Those checks may use benchmark archetypes or proxy
files and are not part of the general solution contract.

What is not built yet:

- hash-verified solution artifacts and freeze manifest;

The current ranker is fully runnable and submission-format valid. A separate embedding
experiment exists, but the submitted ranker keeps the simpler capped lexical semantic
fallback because it produced the same top-100 set while adding model-artifact complexity.