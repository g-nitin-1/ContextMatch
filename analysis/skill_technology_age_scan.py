#!/usr/bin/env python3
"""Scan skill durations against conservative technology availability dates.

This is a post-freeze diagnostic. It is intentionally not imported by run_all
or the frozen Idea 2 scorer because skill duration appears to contain broad
generator noise.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    stream_candidates,
    summary_archetype,
    write_json,
)


SCAN_VERSION = "skill-tech-age-scan-0.1.0"
DEFAULT_AS_OF = "2026-06-01"
DEFAULT_SUMMARY = "skill_technology_age_summary.json"
DEFAULT_REPORT = "skill_technology_age_report.md"

# Exact skill-name matches only. Do not match LoRA inside QLoRA.
#
# Dates are deliberately conservative: use the earliest public/project date
# where that is clearer than package availability, otherwise use first package
# availability for the current ecosystem name. This scan is for prevalence and
# QA, not for hard-excluding candidates.
SKILL_RELEASES: dict[str, dict[str, str]] = {
    "PyTorch": {
        "released_date": "2017-01-19",
        "basis": "public project release",
        "source": "https://pytorch.org/blog/a-year-in/",
    },
    "TensorFlow": {
        "released_date": "2015-11-09",
        "basis": "open-source announcement",
        "source": "https://opensource.googleblog.com/2015/11/tensorflow-smarter-machine-learning-for.html",
    },
    "scikit-learn": {
        "released_date": "2010-02-01",
        "basis": "conservative project-era date",
        "source": "https://scikit-learn.org/stable/about.html",
    },
    "Hugging Face Transformers": {
        "released_date": "2018-11-17",
        "basis": "first PyPI release in Hugging Face transformer-library lineage",
        "source": "https://pypi.org/project/pytorch-pretrained-bert/#history",
    },
    "Sentence Transformers": {
        "released_date": "2019-07-25",
        "basis": "first PyPI release",
        "source": "https://pypi.org/project/sentence-transformers/#history",
    },
    "FAISS": {
        "released_date": "2017-02-01",
        "basis": "conservative open-source project-era date",
        "source": "https://github.com/facebookresearch/faiss",
    },
    "LangChain": {
        "released_date": "2022-10-25",
        "basis": "first PyPI release",
        "source": "https://pypi.org/project/langchain/#history",
    },
    "LlamaIndex": {
        "released_date": "2023-02-16",
        "basis": "first PyPI release under llama-index",
        "source": "https://pypi.org/project/llama-index/#history",
    },
    "Pinecone": {
        "released_date": "2020-12-31",
        "basis": "first PyPI client release",
        "source": "https://pypi.org/project/pinecone-client/#history",
    },
    "Qdrant": {
        "released_date": "2021-02-09",
        "basis": "first PyPI client release",
        "source": "https://pypi.org/project/qdrant-client/#history",
    },
    "Weaviate": {
        "released_date": "2019-11-04",
        "basis": "first PyPI client release",
        "source": "https://pypi.org/project/weaviate-client/#history",
    },
    "Milvus": {
        "released_date": "2019-06-16",
        "basis": "first PyPI client release",
        "source": "https://pypi.org/project/pymilvus/#history",
    },
    "pgvector": {
        "released_date": "2021-06-12",
        "basis": "first PyPI package release",
        "source": "https://pypi.org/project/pgvector/#history",
    },
    "OpenSearch": {
        "released_date": "2021-09-20",
        "basis": "first PyPI client release",
        "source": "https://pypi.org/project/opensearch-py/#history",
    },
    "Haystack": {
        "released_date": "2019-11-28",
        "basis": "first PyPI release",
        "source": "https://pypi.org/project/farm-haystack/#history",
    },
    "PEFT": {
        "released_date": "2023-01-19",
        "basis": "first PyPI release",
        "source": "https://pypi.org/project/peft/#history",
    },
    "LoRA": {
        "released_date": "2021-06-01",
        "basis": "paper month",
        "source": "https://arxiv.org/abs/2106.09685",
    },
    "QLoRA": {
        "released_date": "2023-05-23",
        "basis": "paper date",
        "source": "https://arxiv.org/abs/2305.14314",
    },
    "FastAPI": {
        "released_date": "2018-12-05",
        "basis": "first PyPI release",
        "source": "https://pypi.org/project/fastapi/#history",
    },
    "Docker": {
        "released_date": "2013-03-20",
        "basis": "public project release",
        "source": "https://www.docker.com/blog/happy-10th-birthday-docker/",
    },
    "Kubernetes": {
        "released_date": "2014-06-07",
        "basis": "public project-era date",
        "source": "https://kubernetes.io/blog/2015/07/how-did-quake-demo-from-dockercon-work/",
    },
    "React": {
        "released_date": "2013-05-29",
        "basis": "open-source announcement",
        "source": "https://legacy.reactjs.org/blog/2013/06/05/why-react.html",
    },
}


def month_age(released_date: str, as_of: date) -> int:
    released = date.fromisoformat(released_date)
    return (as_of.year - released.year) * 12 + as_of.month - released.month


def load_ranked_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row["candidate_id"] for row in csv.DictReader(handle)]


def scan(dataset: Path, as_of: date, output_dir: Path) -> dict[str, Any]:
    ages = {
        skill: month_age(entry["released_date"], as_of)
        for skill, entry in SKILL_RELEASES.items()
    }
    release_table = {
        skill: {
            **entry,
            "age_months_as_of": ages[skill],
        }
        for skill, entry in SKILL_RELEASES.items()
    }

    candidate_count = 0
    checked_skill_mentions = 0
    skill_candidate_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    issue_candidates_by_skill: dict[str, set[str]] = defaultdict(set)
    issue_candidates: dict[str, list[dict[str, Any]]] = {}
    issue_candidates_by_archetype: dict[str, set[str]] = defaultdict(set)
    examples_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for candidate in stream_candidates(dataset):
        candidate_count += 1
        candidate_id = candidate["candidate_id"]
        profile = candidate["profile"]
        archetype = summary_archetype(
            profile.get("summary", ""),
            profile.get("current_title", ""),
        )
        seen_skills = set()
        for skill in candidate.get("skills", []):
            name = skill.get("name")
            duration = skill.get("duration_months")
            if name not in SKILL_RELEASES or not isinstance(duration, int):
                continue
            checked_skill_mentions += 1
            if name not in seen_skills:
                skill_candidate_counts[name] += 1
                seen_skills.add(name)
            max_possible = ages[name]
            if duration <= max_possible:
                continue
            issue = {
                "skill": name,
                "duration_months": duration,
                "max_possible_months": max_possible,
                "excess_months": duration - max_possible,
                "released_date": SKILL_RELEASES[name]["released_date"],
            }
            issue_counts[name] += 1
            issue_candidates_by_skill[name].add(candidate_id)
            issue_candidates.setdefault(candidate_id, []).append(issue)
            issue_candidates_by_archetype[archetype].add(candidate_id)
            if len(examples_by_skill[name]) < 8:
                examples_by_skill[name].append(
                    {
                        "candidate_id": candidate_id,
                        "summary_archetype": archetype,
                        **issue,
                    }
                )

    repo_root = output_dir.parents[1]
    frozen_top100 = load_ranked_ids(output_dir / "idea2_submission.csv")
    team_top100 = load_ranked_ids(repo_root / "idea1_top100.csv")

    def top_hits(ids: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "rank": rank,
                "candidate_id": candidate_id,
                "issues": issue_candidates[candidate_id],
            }
            for rank, candidate_id in enumerate(ids, 1)
            if candidate_id in issue_candidates
        ]

    summary = {
        "scan_version": SCAN_VERSION,
        "as_of": as_of.isoformat(),
        "interpretation_boundary": (
            "Skill-duration chronology is a data-quality diagnostic, not a "
            "hard honeypot rule, because violations are broad across strong "
            "cohorts and occur in structured skill metadata."
        ),
        "candidate_count": candidate_count,
        "known_skill_release_count": len(SKILL_RELEASES),
        "checked_skill_mentions": checked_skill_mentions,
        "unique_candidates_with_issue": len(issue_candidates),
        "issue_count": sum(issue_counts.values()),
        "by_skill": {
            skill: {
                "candidate_count_with_skill": skill_candidate_counts[skill],
                "issue_count": issue_counts[skill],
                "unique_candidate_count": len(issue_candidates_by_skill[skill]),
                "release": release_table[skill],
                "examples": examples_by_skill.get(skill, []),
            }
            for skill in SKILL_RELEASES
        },
        "unique_issue_candidates_by_archetype": {
            archetype: len(ids)
            for archetype, ids in sorted(issue_candidates_by_archetype.items())
        },
        "frozen_idea2_top100": {
            "issue_candidate_count": len(top_hits(frozen_top100)),
            "issue_candidates": top_hits(frozen_top100),
        },
        "team_qwen_top100": {
            "issue_candidate_count": len(top_hits(team_top100)),
            "issue_candidates": top_hits(team_top100),
        },
    }
    return summary


def write_report(summary: dict[str, Any], path: Path) -> None:
    rows = []
    for skill, payload in summary["by_skill"].items():
        release = payload["release"]
        rows.append(
            (
                skill,
                release["released_date"],
                release["age_months_as_of"],
                payload["candidate_count_with_skill"],
                payload["unique_candidate_count"],
            )
        )
    rows.sort(key=lambda item: (-item[4], item[0]))

    lines = [
        "# Skill Technology-Age Scan",
        "",
        f"Scan version: `{summary['scan_version']}`",
        f"As of: `{summary['as_of']}`",
        "",
        "This is a post-freeze diagnostic. It is not a hard integrity gate.",
        "",
        "## Summary",
        "",
        f"- Candidates scanned: {summary['candidate_count']:,}",
        f"- Dated skill names checked: {summary['known_skill_release_count']}",
        f"- Checked dated-skill mentions: {summary['checked_skill_mentions']:,}",
        f"- Unique candidates with at least one issue: {summary['unique_candidates_with_issue']:,}",
        f"- Total skill-duration issues: {summary['issue_count']:,}",
        f"- Frozen Idea2 top-100 candidates with issue: {summary['frozen_idea2_top100']['issue_candidate_count']}",
        f"- Team Qwen top-100 candidates with issue: {summary['team_qwen_top100']['issue_candidate_count']}",
        "",
        "## Counts By Skill",
        "",
        "| Skill | Release date | Age months | Candidates with skill | Violating candidates |",
        "|---|---:|---:|---:|---:|",
    ]
    for skill, released, age, with_skill, violating in rows:
        lines.append(
            f"| {skill} | {released} | {age} | {with_skill} | {violating} |"
        )

    lines.extend(
        [
            "",
            "## Violating Candidates By Archetype",
            "",
            "| Archetype | Unique candidates |",
            "|---|---:|",
        ]
    )
    for archetype, count in summary["unique_issue_candidates_by_archetype"].items():
        lines.append(f"| {archetype} | {count} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation_boundary"],
            "",
            "The large top-100 hit rate means this signal should not be promoted "
            "to a hard honeypot rule without external confirmation. It is better "
            "treated as evidence that `skills.duration_months` is generated from "
            "candidate seniority rather than from each technology's true age.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    as_of = date.fromisoformat(args.as_of)
    summary = scan(args.dataset, as_of, args.output_dir)
    summary_path = args.output_dir / args.summary
    report_path = args.output_dir / args.report
    write_json(summary_path, summary)
    write_report(summary, report_path)
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
