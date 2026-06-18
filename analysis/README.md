# Deterministic Dataset Analysis

Install the analysis dependencies:

```bash
python3 -m pip install -r analysis/requirements.txt
```

Run all analyses from the repository root:

```bash
python3 -m analysis.run_all
```

Run stages independently:

```bash
python3 -m analysis.profile_archetypes
python3 -m analysis.integrity_checks
python3 -m analysis.behavioral_twins
python3 -m analysis.generator_reconstruction
python3 -m analysis.jd_evidence_catalog
python3 -m analysis.candidate_overlay
python3 -m analysis.idea2_scorer
python3 -m analysis.skill_assessment_experiment
python3 -m analysis.build_report
```

Generate the optional one-time JD evidence audit worksheet after the catalog
exists:

```bash
python3 -m analysis.build_audit_worksheet
```

Outputs are written to `artifacts/analysis/`.

`generator_reconstruction.py` is the reverse-engineering stage of Idea 2. It
learns static generator classes from exact-template co-occurrence, clusters
behavior separately, measures field dependencies, and analyzes integrity
failures as possible post-generation mutations. It deliberately does not assign
relevance scores.

`jd_evidence_catalog.py` applies the versioned
`analysis/jd_evidence_rubric.json` to the 44 career templates, then aggregates
candidate-weighted evidence for the 12 fine generator atoms. It records exact
matched snippets and compound JD coverage without assigning relevance tiers.

`build_audit_worksheet.py` lays out the finite 44-template evidence catalog for
manual review. It is not part of `run_all`; it is a version-lock audit aid.

`candidate_overlay.py` streams all candidates and joins generator structure,
career-template evidence, skills, recency, logistics, behavior, and integrity
flags into candidate-level records. It evaluates the four structured
`candidate_overlay_rules` and the versioned `skill_signal_patterns` from the
rubric, but still does not assign relevance tiers or scores.

`idea2_scorer.py` consumes the candidate overlay and builds the first
multi-world deterministic proxy ranking. It reports stability across plausible
worlds and writes full candidate scores, but it is not a validated local
leaderboard score.

`skill_assessment_experiment.py` is a post-freeze experiment. It adds a
bounded modifier from Redrob per-skill assessment scores, compares the result
with frozen `idea2-1.0.0`, and does not modify the freeze manifest or frozen
submission.

The integrity knowledge base is versioned in `analysis/knowledge_base.json`.
External chronology checks preserve their source URLs in the generated issue
records. Flagged records are suspicious, not confirmed official honeypots.
