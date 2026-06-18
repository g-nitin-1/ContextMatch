# ContextMatch

Deterministic candidate ranking for the Redrob Intelligent Candidate Discovery
challenge.

## Reproduce The Ranking

Requirements:

- Python 3.10 or newer
- CPU only
- No network access
- The released `candidates.jsonl` file

The ranking path uses only the Python standard library. From the repository
root:

```bash
python3 rank.py \
  --candidates India_runs_data_and_ai_challenge/candidates.jsonl \
  --out submission.csv
```

Validate the generated file:

```bash
python3 India_runs_data_and_ai_challenge/validate_submission.py submission.csv
```

`rank.py` verifies the hashes of the frozen generator manifest, JD evidence
catalog, and integrity knowledge base before ranking. It streams the candidate
input once, applies deterministic integrity and evidence rules, evaluates six
Idea 2 scoring worlds, enforces the top-100 integrity gate, and writes the
required `candidate_id,rank,score,reasoning` CSV.

The runtime path does not call hosted APIs, use a GPU, or require the research
pipeline's NumPy/scikit-learn dependencies.

## Method

The ranker combines:

- Reconstructed synthetic profile families and fine atoms
- A versioned regex rubric over the finite career-template library
- Candidate skills, recency, availability, location, and behavioral signals
- Whole-career disqualifier and conditional-negative rules
- Hard and strong integrity policies for factual contradictions
- Six explicit uncertainty worlds with bounded behavior and logistics effects

The final order is the mean proxy score across these worlds. This is a
methodology-based local proxy, not a recovered hidden leaderboard score.

The frozen specification is recorded in
`artifacts/analysis/idea2_freeze_manifest.json`.

## Research Pipeline

The reverse-engineering and audit pipeline is separate from ranking:

```bash
python3 -m pip install -r analysis/requirements.txt
python3 -m analysis.run_all
python3 -m unittest discover -s analysis/tests -v
```

Research details and limitations are documented in `progress.txt`,
`idea1.md`, `idea2.md`, and `artifacts/analysis/analysis_report.md`.
