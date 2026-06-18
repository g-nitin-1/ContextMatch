#!/usr/bin/env python3
"""Run deterministic consistency and honeypot-oriented checks."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    markdown_table,
    stream_candidates,
    summary_archetype,
    write_json,
)


DEFAULT_KNOWLEDGE_BASE = Path(__file__).with_name("knowledge_base.json")
SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 4, "critical": 8}
HIGH_CONFIDENCE_RULES = {
    "company_pre_founding",
    "technology_before_release",
    "expert_zero_duration_3plus",
    "role_duration_large_mismatch",
    "career_duration_exceeds_experience",
}
RULE_CATEGORIES = {
    "company_pre_founding": "honeypot_evidence",
    "technology_before_release": "honeypot_evidence",
    "expert_zero_duration_3plus": "honeypot_evidence",
    "role_duration_large_mismatch": "honeypot_evidence",
    "career_duration_exceeds_experience": "honeypot_evidence",
    "career_date_order": "profile_integrity",
    "career_date_in_future": "profile_integrity",
    "current_role_count": "profile_integrity",
    "profile_current_role_mismatch": "profile_integrity",
    "education_date_order": "profile_integrity",
    "role_duration_mismatch": "soft_consistency",
    "career_history_incomplete": "soft_consistency",
    "overlapping_roles": "soft_consistency",
    "expert_zero_duration": "soft_consistency",
    "skill_duration_exceeds_experience": "soft_consistency",
    "salary_range_order": "behavioral_data_quality",
    "activity_before_signup": "behavioral_data_quality",
    "activity_in_future": "behavioral_data_quality",
}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def month_difference(start: date, end: date) -> int:
    return max(0, (end.year - start.year) * 12 + end.month - start.month)


def issue(
    rule: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
    source: str | None = None,
) -> dict[str, Any]:
    result = {
        "rule": rule,
        "category": RULE_CATEGORIES.get(rule, "other"),
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }
    if source:
        result["source"] = source
    return result


class IntegrityChecker:
    def __init__(self, knowledge_base: dict[str, Any], as_of: date):
        self.knowledge_base = knowledge_base
        self.as_of = as_of
        self.technology_patterns = []
        for name, entry in knowledge_base.get("technologies", {}).items():
            self.technology_patterns.append(
                (
                    name,
                    [re.compile(pattern, re.IGNORECASE) for pattern in entry["patterns"]],
                    date.fromisoformat(entry["released_date"]),
                    entry.get("source"),
                )
            )

    def check(self, candidate: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        profile = candidate["profile"]
        career = candidate.get("career_history", [])
        signals = candidate["redrob_signals"]

        current_roles = [role for role in career if role.get("is_current")]
        if len(current_roles) != 1:
            findings.append(
                issue(
                    "current_role_count",
                    "critical",
                    "Candidate must have exactly one current role.",
                    {"current_role_count": len(current_roles)},
                )
            )
        elif (
            current_roles[0].get("company") != profile.get("current_company")
            or current_roles[0].get("title") != profile.get("current_title")
        ):
            findings.append(
                issue(
                    "profile_current_role_mismatch",
                    "critical",
                    "Profile current role does not match career history.",
                    {
                        "profile_company": profile.get("current_company"),
                        "profile_title": profile.get("current_title"),
                        "career_company": current_roles[0].get("company"),
                        "career_title": current_roles[0].get("title"),
                    },
                )
            )

        intervals: list[tuple[date, date, dict[str, Any]]] = []
        stored_months = 0
        for role in career:
            start = parse_date(role.get("start_date"))
            end = parse_date(role.get("end_date")) or self.as_of
            if start is None:
                continue
            if end < start:
                findings.append(
                    issue(
                        "career_date_order",
                        "critical",
                        "Career role ends before it starts.",
                        {
                            "company": role.get("company"),
                            "start_date": role.get("start_date"),
                            "end_date": role.get("end_date"),
                        },
                    )
                )
                continue
            if start > self.as_of or end > self.as_of:
                findings.append(
                    issue(
                        "career_date_in_future",
                        "critical",
                        "Career role contains a date after the analysis reference date.",
                        {
                            "company": role.get("company"),
                            "start_date": role.get("start_date"),
                            "end_date": role.get("end_date"),
                            "as_of": self.as_of.isoformat(),
                        },
                    )
                )
            intervals.append((start, end, role))
            actual_months = month_difference(start, end)
            declared_months = int(role.get("duration_months", 0))
            stored_months += declared_months
            difference = abs(actual_months - declared_months)
            if difference > 2:
                severity = "high" if difference >= 12 else "medium"
                rule = (
                    "role_duration_large_mismatch"
                    if difference >= 12
                    else "role_duration_mismatch"
                )
                findings.append(
                    issue(
                        rule,
                        severity,
                        "Declared role duration is inconsistent with role dates.",
                        {
                            "company": role.get("company"),
                            "title": role.get("title"),
                            "declared_months": declared_months,
                            "calendar_months": actual_months,
                            "difference_months": difference,
                        },
                    )
                )

            company_entry = self.knowledge_base.get("companies", {}).get(
                role.get("company")
            )
            if company_entry:
                founded = date.fromisoformat(company_entry["founded_date"])
                precision = company_entry.get("precision", "day")
                predates = (
                    start.year < founded.year
                    if precision == "year"
                    else start < founded
                )
                if predates:
                    findings.append(
                        issue(
                            "company_pre_founding",
                            "high",
                            "Employment starts before the company's documented founding.",
                            {
                                "company": role.get("company"),
                                "role_start": start.isoformat(),
                                "founded_date": founded.isoformat(),
                                "date_precision": precision,
                            },
                            company_entry.get("source"),
                        )
                    )

            role_end = parse_date(role.get("end_date"))
            if role_end:
                description = role.get("description", "")
                for tech_name, patterns, released, source in self.technology_patterns:
                    if role_end < released and any(
                        pattern.search(description) for pattern in patterns
                    ):
                        findings.append(
                            issue(
                                "technology_before_release",
                                "high",
                                "Role ended before a named technology was released.",
                                {
                                    "company": role.get("company"),
                                    "role_end": role_end.isoformat(),
                                    "technology": tech_name,
                                    "released_date": released.isoformat(),
                                },
                                source,
                            )
                        )

        stated_months = float(profile.get("years_of_experience", 0.0)) * 12
        if stored_months > stated_months + 24:
            findings.append(
                issue(
                    "career_duration_exceeds_experience",
                    "high",
                    "Summed role durations substantially exceed stated experience.",
                    {
                        "stated_experience_months": round(stated_months, 1),
                        "summed_role_months": stored_months,
                        "difference_months": round(stored_months - stated_months, 1),
                    },
                )
            )
        elif stated_months > stored_months + 36:
            findings.append(
                issue(
                    "career_history_incomplete",
                    "low",
                    "Career history covers substantially less time than stated experience.",
                    {
                        "stated_experience_months": round(stated_months, 1),
                        "summed_role_months": stored_months,
                        "difference_months": round(stated_months - stored_months, 1),
                    },
                )
            )

        intervals.sort(key=lambda value: value[0])
        for index, (start_a, end_a, role_a) in enumerate(intervals):
            for start_b, end_b, role_b in intervals[index + 1 :]:
                if start_b >= end_a:
                    break
                overlap_end = min(end_a, end_b)
                overlap_months = month_difference(start_b, overlap_end)
                if overlap_months >= 6:
                    findings.append(
                        issue(
                            "overlapping_roles",
                            "medium" if overlap_months < 18 else "high",
                            "Two career roles overlap for an extended period.",
                            {
                                "first_company": role_a.get("company"),
                                "second_company": role_b.get("company"),
                                "overlap_months": overlap_months,
                            },
                        )
                    )

        zero_duration_expert = [
            skill.get("name")
            for skill in candidate.get("skills", [])
            if skill.get("proficiency") == "expert"
            and int(skill.get("duration_months", 0)) == 0
        ]
        if len(zero_duration_expert) >= 3:
            findings.append(
                issue(
                    "expert_zero_duration_3plus",
                    "high",
                    "At least three expert skills report zero months of usage.",
                    {
                        "count": len(zero_duration_expert),
                        "skills": zero_duration_expert,
                    },
                )
            )
        elif zero_duration_expert:
            findings.append(
                issue(
                    "expert_zero_duration",
                    "low",
                    "An expert skill reports zero months of usage.",
                    {"skills": zero_duration_expert},
                )
            )

        excessive_skill_durations = [
            {
                "skill": skill.get("name"),
                "duration_months": skill.get("duration_months"),
            }
            for skill in candidate.get("skills", [])
            if int(skill.get("duration_months", 0)) > stated_months + 24
        ]
        if excessive_skill_durations:
            findings.append(
                issue(
                    "skill_duration_exceeds_experience",
                    "low",
                    "Skill usage duration substantially exceeds stated experience.",
                    {"skills": excessive_skill_durations},
                )
            )

        for education in candidate.get("education", []):
            if education.get("end_year", 0) < education.get("start_year", 0):
                findings.append(
                    issue(
                        "education_date_order",
                        "critical",
                        "Education ends before it starts.",
                        {
                            "institution": education.get("institution"),
                            "start_year": education.get("start_year"),
                            "end_year": education.get("end_year"),
                        },
                    )
                )

        salary = signals.get("expected_salary_range_inr_lpa", {})
        if salary.get("min", 0) > salary.get("max", 0):
            findings.append(
                issue(
                    "salary_range_order",
                    "low",
                    "Expected salary minimum exceeds maximum.",
                    salary,
                )
            )
        signup = parse_date(signals.get("signup_date"))
        last_active = parse_date(signals.get("last_active_date"))
        if signup and last_active and last_active < signup:
            findings.append(
                issue(
                    "activity_before_signup",
                    "low",
                    "Last-active date predates platform signup.",
                    {
                        "signup_date": signup.isoformat(),
                        "last_active_date": last_active.isoformat(),
                    },
                )
            )
        if last_active and last_active > self.as_of:
            findings.append(
                issue(
                    "activity_in_future",
                    "critical",
                    "Last-active date is after the analysis reference date.",
                    {
                        "last_active_date": last_active.isoformat(),
                        "as_of": self.as_of.isoformat(),
                    },
                )
            )
        return findings


def risk_level(findings: list[dict[str, Any]]) -> str:
    if any(item["severity"] == "critical" for item in findings):
        return "critical"
    if any(
        item["severity"] == "high" and item["rule"] in HIGH_CONFIDENCE_RULES
        for item in findings
    ):
        return "high"
    score = sum(SEVERITY_WEIGHT[item["severity"]] for item in findings)
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    if score:
        return "low"
    return "none"


def analyze(
    dataset: Path, output_dir: Path, knowledge_base_path: Path, as_of: date
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    knowledge_base = json.loads(knowledge_base_path.read_text(encoding="utf-8"))
    checker = IntegrityChecker(knowledge_base, as_of)
    issue_counts: Counter[str] = Counter()
    issue_candidate_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    category_candidate_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    archetype_risk: dict[str, Counter[str]] = defaultdict(Counter)
    flagged_candidates = 0
    high_confidence_candidates = 0
    record_count = 0

    issues_path = output_dir / "integrity_issues.jsonl"
    with issues_path.open("w", encoding="utf-8") as handle:
        for candidate in stream_candidates(dataset):
            record_count += 1
            findings = checker.check(candidate)
            level = risk_level(findings)
            risk_counts[level] += 1
            profile = candidate["profile"]
            archetype = summary_archetype(
                profile.get("summary", ""), profile.get("current_title", "")
            )
            archetype_risk[archetype][level] += 1
            if not findings:
                continue
            flagged_candidates += 1
            if any(item["rule"] in HIGH_CONFIDENCE_RULES for item in findings):
                high_confidence_candidates += 1
            candidate_rules = {item["rule"] for item in findings}
            candidate_categories = {item["category"] for item in findings}
            issue_candidate_counts.update(candidate_rules)
            category_candidate_counts.update(candidate_categories)
            for item in findings:
                issue_counts[item["rule"]] += 1
                category_counts[item["category"]] += 1
                severity_counts[item["severity"]] += 1
            payload = {
                "candidate_id": candidate["candidate_id"],
                "summary_archetype": archetype,
                "current_title": profile.get("current_title"),
                "risk_level": level,
                "issues": findings,
            }
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True))
            handle.write("\n")

    summary = {
        "dataset": str(dataset),
        "knowledge_base": str(knowledge_base_path),
        "analysis_as_of": as_of.isoformat(),
        "record_count": record_count,
        "flagged_candidates": flagged_candidates,
        "high_confidence_contradiction_candidates": high_confidence_candidates,
        "risk_levels": dict(risk_counts.most_common()),
        "issue_counts": dict(issue_counts.most_common()),
        "issue_candidate_counts": dict(issue_candidate_counts.most_common()),
        "category_occurrences": dict(category_counts.most_common()),
        "category_candidate_counts": dict(category_candidate_counts.most_common()),
        "severity_counts": dict(severity_counts.most_common()),
        "archetype_risk_levels": {
            name: dict(counter) for name, counter in sorted(archetype_risk.items())
        },
        "high_confidence_rules": sorted(HIGH_CONFIDENCE_RULES),
    }
    write_json(output_dir / "integrity_summary.json", summary)

    report = [
        "# Integrity and Honeypot-Oriented Analysis",
        "",
        "These rules identify factual inconsistencies and suspicious profiles. They",
        "do not prove that every flagged candidate is an official honeypot.",
        "",
        "## Coverage",
        "",
        f"- Candidates checked: {record_count:,}",
        f"- Candidates with at least one issue: {flagged_candidates:,}",
        (
            "- Candidates with at least one high-confidence contradiction rule: "
            f"{high_confidence_candidates:,}"
        ),
        f"- Analysis reference date: {as_of.isoformat()}",
        "",
        "## Risk Levels",
        "",
        markdown_table(
            ("Risk level", "Candidates", "Share"),
            (
                (name, f"{count:,}", f"{count / record_count:.2%}")
                for name, count in risk_counts.most_common()
            ),
        ),
        "",
        "## Most Frequent Rules",
        "",
        markdown_table(
            ("Rule", "Candidates", "Occurrences"),
            (
                (
                    name,
                    f"{issue_candidate_counts[name]:,}",
                    f"{count:,}",
                )
                for name, count in issue_counts.most_common()
            ),
        ),
        "",
        "## Interpretation",
        "",
        "- Frequent signal anomalies are retained as low-severity data-quality",
        "  diagnostics; they are not treated as honeypot evidence.",
        "- `critical` is reserved for internal profile/schema contradictions.",
        "- `high` includes externally checkable chronology contradictions and the",
        "  challenge's explicit zero-duration expert-skill pattern.",
        "- Company and technology chronology checks retain source URLs in the JSONL.",
        "- Medium and low findings should normally be model features, not automatic",
        "  exclusions.",
        "- The official honeypot set remains hidden, so report counts are an upper",
        "  bound on suspicious records rather than recovered ground truth.",
        "",
    ]
    (output_dir / "integrity_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE
    )
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 6, 1))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = analyze(
        args.candidates, args.output_dir, args.knowledge_base, args.as_of
    )
    print(
        "Integrity analysis complete: "
        f"{summary['flagged_candidates']:,} flagged candidates."
    )


if __name__ == "__main__":
    main()
