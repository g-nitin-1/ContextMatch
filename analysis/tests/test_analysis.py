from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from analysis.behavioral_twins import behavior_distance
from analysis.common import strict_static_signature, summary_archetype
from analysis.integrity_checks import IntegrityChecker


def candidate_fixture() -> dict:
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Example",
            "headline": "Senior AI Engineer",
            "summary": "Senior AI engineer with 7 years of production experience.",
            "location": "Pune, Maharashtra",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "Senior AI Engineer",
            "current_company": "Sarvam AI",
            "current_company_size": "51-200",
            "current_industry": "AI/ML",
        },
        "career_history": [
            {
                "company": "Sarvam AI",
                "title": "Senior AI Engineer",
                "start_date": "2024-01-01",
                "end_date": None,
                "duration_months": 29,
                "is_current": True,
                "industry": "AI/ML",
                "company_size": "51-200",
                "description": "Built production retrieval and ranking systems.",
            },
            {
                "company": "Example Product",
                "title": "ML Engineer",
                "start_date": "2019-01-01",
                "end_date": "2023-12-01",
                "duration_months": 59,
                "is_current": False,
                "industry": "Software",
                "company_size": "201-500",
                "description": "Shipped recommendation models.",
            },
        ],
        "education": [
            {
                "institution": "Example Institute",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "start_year": 2014,
                "end_year": 2018,
                "tier": "tier_2",
            }
        ],
        "skills": [
            {
                "name": "Python",
                "proficiency": "expert",
                "endorsements": 20,
                "duration_months": 72,
            }
        ],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 20,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {},
            "connection_count": 100,
            "endorsements_received": 20,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 25, "max": 35},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 70,
            "search_appearance_30d": 50,
            "saved_by_recruiters_30d": 10,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.7,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }


class CommonTests(unittest.TestCase):
    def test_summary_archetype(self) -> None:
        self.assertEqual(
            summary_archetype("Senior AI engineer with 7.0 years.", ""),
            "senior_explicit_ai",
        )

    def test_static_signature_ignores_identity_and_behavior(self) -> None:
        left = candidate_fixture()
        right = json.loads(json.dumps(left))
        right["candidate_id"] = "CAND_0000002"
        right["profile"]["anonymized_name"] = "Other"
        right["redrob_signals"]["recruiter_response_rate"] = 0.1
        self.assertEqual(strict_static_signature(left), strict_static_signature(right))


class IntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        knowledge = json.loads(
            Path("analysis/knowledge_base.json").read_text(encoding="utf-8")
        )
        self.checker = IntegrityChecker(knowledge, date(2026, 6, 1))

    def test_clean_fixture_has_no_high_severity_issue(self) -> None:
        findings = self.checker.check(candidate_fixture())
        self.assertFalse(
            any(item["severity"] in {"high", "critical"} for item in findings)
        )

    def test_detects_pre_founding_employment(self) -> None:
        candidate = candidate_fixture()
        candidate["career_history"][0]["start_date"] = "2020-01-01"
        findings = self.checker.check(candidate)
        self.assertIn("company_pre_founding", {item["rule"] for item in findings})

    def test_detects_multiple_zero_duration_expert_skills(self) -> None:
        candidate = candidate_fixture()
        candidate["skills"] = [
            {
                "name": f"Skill {index}",
                "proficiency": "expert",
                "endorsements": 1,
                "duration_months": 0,
            }
            for index in range(3)
        ]
        findings = self.checker.check(candidate)
        self.assertIn(
            "expert_zero_duration_3plus", {item["rule"] for item in findings}
        )


class BehavioralTests(unittest.TestCase):
    def test_behavior_distance(self) -> None:
        left = {
            "inactive_days": 10,
            "open_to_work": 1,
            "response_rate": 0.9,
            "response_time_hours": 10,
            "notice_period_days": 15,
            "willing_to_relocate": 1,
            "saved_by_recruiters": 50,
            "interview_completion": 0.9,
        }
        right = dict(left)
        self.assertEqual(behavior_distance(left, right), 0.0)
        right["open_to_work"] = 0
        self.assertGreater(behavior_distance(left, right), 0.0)


if __name__ == "__main__":
    unittest.main()
