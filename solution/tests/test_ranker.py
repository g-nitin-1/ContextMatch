import unittest
import json
import tempfile
from pathlib import Path

from solution.ranker import (
    _item_score,
    apply_rank_tone,
    build_reasoning,
    evidence_score,
    integrity_blocks,
    meets_career_evidence_floor,
    rank_raw_with_summary,
    rank_with_summary,
    semantic_score,
    seniority_alignment,
    seniority_ordering_modifier,
    score_overlay,
    skill_score,
)
from solution.jd_parser import spec_from_jd_text
from solution.requirement_spec import load_spec


def overlay(
    *,
    candidate_id: str = "CAND_TEST",
    compounds: list[str] | None = None,
    signals: list[str] | None = None,
    skill_signals: list[str] | None = None,
    risk_level: str = "none",
    honeypot_rules: list[str] | None = None,
    fired_rules: list[str] | None = None,
    title: str = "Senior AI Engineer",
    years: float = 7.0,
) -> dict:
    fired_rules = fired_rules or []
    return {
        "candidate_id": candidate_id,
        "static": {
            "current_title": title,
            "current_company": "ProductCo",
            "years_of_experience": years,
        },
        "career_evidence": {
            "any_career_compound_ids": compounds or [],
            "any_career_signal_ids": signals or [],
            "any_career_risk_context_ids": [],
        },
        "skill_overlay": {
            "skill_signal_ids": skill_signals or [],
            "advanced_or_expert_signal_counts": {
                signal: 1 for signal in (skill_signals or [])
            },
        },
        "availability_overlay": {
            "inactive_days": 10,
            "open_to_work": True,
            "response_rate": 0.7,
            "notice_period_days": 30,
        },
        "logistics_overlay": {"location_bucket": "noida"},
        "integrity_overlay": {
            "risk_level": risk_level,
            "honeypot_proxy_rules": honeypot_rules or [],
        },
        "candidate_overlay_rules": {
            rule_id: {"fired": rule_id in fired_rules}
            for rule_id in (
                "services_only_entire_career",
                "research_only_without_production",
                "recent_shallow_llm_only",
                "senior_not_coding_recently",
            )
        },
    }


class RankerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_spec()

    def test_career_evidence_outweighs_skills_only(self) -> None:
        strong_career = overlay(
            compounds=[
                "production_embeddings_retrieval",
                "evaluated_ranking_system",
                "end_to_end_intelligence_ownership",
            ],
            signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "production_delivery",
                "ranking_evaluation",
                "online_experimentation",
                "operational_ownership",
                "zero_to_one_ownership",
                "product_context",
            ],
        )
        skills_only = overlay(
            skill_signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "production_delivery",
                "ranking_evaluation",
            ]
        )

        self.assertGreater(
            evidence_score(self.spec, strong_career),
            evidence_score(self.spec, skills_only),
        )
        self.assertGreater(
            score_overlay(self.spec, strong_career).score,
            score_overlay(self.spec, skills_only).score,
        )
        self.assertGreater(skill_score(self.spec, skills_only), 0)

    def test_equivalent_compound_fully_satisfies_capability(self) -> None:
        item = next(
            item for item in self.spec.must_have if item.id == "production_retrieval"
        )

        self.assertEqual(
            _item_score(item, set(), {"end_to_end_intelligence_ownership"}),
            item.weight,
        )
        self.assertLess(
            _item_score(
                item,
                {"embeddings", "retrieval_search", "ranking_recommendation_matching"},
                set(),
            ),
            item.weight,
        )

    def test_honeypot_and_hard_disqualifier_block_candidate(self) -> None:
        honeypot = overlay(honeypot_rules=["company_pre_founding"])
        services_only = overlay(fired_rules=["services_only_entire_career"])

        self.assertIn("company_pre_founding", integrity_blocks(self.spec, honeypot))
        self.assertTrue(score_overlay(self.spec, honeypot).blocked)
        self.assertTrue(score_overlay(self.spec, services_only).blocked)

    def test_semantic_and_skills_cannot_bypass_career_evidence_floor(self) -> None:
        skills_only = overlay(
            skill_signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "ranking_evaluation",
            ]
        )
        skills_only["semantic_tokens"] = [
            "production",
            "retrieval",
            "ranking",
            "evaluation",
            "embeddings",
        ]

        scored = score_overlay(self.spec, skills_only)

        self.assertFalse(meets_career_evidence_floor(self.spec, skills_only))
        self.assertTrue(scored.blocked)
        self.assertIn("career_evidence_floor_not_met", scored.blocked_reasons)

    def test_support_only_career_signals_do_not_meet_evidence_floor(self) -> None:
        support_only = overlay(
            signals=[
                "product_context",
                "production_delivery",
                "meaningful_scale",
                "operational_ownership",
            ]
        )

        self.assertFalse(meets_career_evidence_floor(self.spec, support_only))
        self.assertTrue(score_overlay(self.spec, support_only).blocked)

    def test_technical_career_signal_meets_evidence_floor(self) -> None:
        technical = overlay(signals=["retrieval_search"])

        self.assertTrue(meets_career_evidence_floor(self.spec, technical))
        self.assertFalse(score_overlay(self.spec, technical).blocked)

    def test_seniority_alignment_is_bounded_and_ownership_based(self) -> None:
        senior = overlay(
            title="Senior AI Engineer",
            compounds=["end_to_end_intelligence_ownership"],
            signals=[
                "retrieval_search",
                "operational_ownership",
                "zero_to_one_ownership",
            ],
        )
        nonsenior = overlay(
            title="AI Engineer",
            compounds=["end_to_end_intelligence_ownership"],
            signals=[
                "retrieval_search",
                "operational_ownership",
                "zero_to_one_ownership",
            ],
        )

        self.assertGreater(
            seniority_alignment(self.spec, senior),
            seniority_alignment(self.spec, nonsenior),
        )
        self.assertLessEqual(
            abs(seniority_alignment(self.spec, senior)),
            self.spec.seniority["strength"],
        )

    def test_seniority_ordering_modifier_is_bounded_and_optional(self) -> None:
        senior = overlay(
            title="Senior AI Engineer",
            compounds=["end_to_end_intelligence_ownership"],
            signals=[
                "retrieval_search",
                "operational_ownership",
                "zero_to_one_ownership",
            ],
        )

        modifier = seniority_ordering_modifier(self.spec, senior, cap=0.4)
        without_modifier = score_overlay(
            self.spec,
            senior,
            seniority_ordering_cap=0.0,
        )
        with_modifier = score_overlay(self.spec, senior)

        self.assertGreater(modifier, 0.0)
        self.assertLessEqual(modifier, 0.4)
        self.assertAlmostEqual(
            with_modifier.score - without_modifier.score,
            modifier,
        )

    def test_senior_title_alone_gets_no_seniority_bonus(self) -> None:
        senior_title_only = overlay(
            title="Senior AI Engineer",
            signals=["retrieval_search"],
        )

        self.assertEqual(seniority_alignment(self.spec, senior_title_only), 0.0)

    def test_reasoning_is_field_grounded_and_jd_connected(self) -> None:
        candidate = overlay(
            title="Senior AI Engineer",
            compounds=[
                "production_embeddings_retrieval",
                "evaluated_ranking_system",
            ],
            signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "ranking_evaluation",
                "operational_ownership",
            ],
            skill_signals=["retrieval_search", "ranking_recommendation_matching"],
        )
        candidate["static"]["current_company"] = "SearchCo"
        candidate["skill_overlay"]["skill_names"] = ["Python", "BM25", "Elasticsearch"]

        reasoning = score_overlay(self.spec, candidate).reasoning

        self.assertIn("Senior AI Engineer", reasoning)
        self.assertIn("SearchCo", reasoning)
        self.assertIn("7.0 years", reasoning)
        self.assertIn("JD", reasoning)
        self.assertTrue("Python" in reasoning or "BM25" in reasoning)
        self.assertNotIn("evidence=", reasoning)
        self.assertNotIn("semantic=", reasoning)
        self.assertNotIn("evaluated_ranking_system", reasoning)
        self.assertNotIn("production_embeddings_retrieval", reasoning)

    def test_reasoning_surfaces_honest_concern(self) -> None:
        candidate = overlay(
            compounds=["production_embeddings_retrieval"],
            signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
            ],
        )
        candidate["availability_overlay"]["notice_period_days"] = 90

        reasoning = score_overlay(self.spec, candidate).reasoning

        self.assertIn("Concern:", reasoning)
        self.assertIn("90-day notice", reasoning)

    def test_rank_tone_changes_by_rank_band(self) -> None:
        reasoning = "Senior AI Engineer at SearchCo with 7.0 years. Concern: no major issue."

        self.assertTrue(apply_rank_tone(reasoning, 5).startswith("High-confidence"))
        self.assertTrue(apply_rank_tone(reasoning, 95).startswith("Viable"))

    def test_junior_jd_penalizes_staff_profile(self) -> None:
        junior_spec = spec_from_jd_text(
            "Junior Data Analyst\n"
            "Entry-level role for SQL dashboards and reporting."
        )
        junior = overlay(
            title="Junior Data Analyst",
            years=1.0,
            signals=["operational_ownership"],
        )
        staff = overlay(
            title="Staff Machine Learning Engineer",
            years=10.0,
            signals=["operational_ownership"],
        )

        self.assertGreater(
            seniority_alignment(junior_spec, junior),
            seniority_alignment(junior_spec, staff),
        )

    def test_management_jd_prefers_management_track(self) -> None:
        manager_spec = spec_from_jd_text(
            "Engineering Manager\n"
            "Manage a team of engineers, hiring, mentoring, delivery ownership, "
            "and performance reviews."
        )
        manager = overlay(
            title="Engineering Manager",
            signals=["mentoring_leadership", "operational_ownership"],
        )
        ic = overlay(
            title="Staff Software Engineer",
            signals=["python_engineering", "operational_ownership"],
        )

        self.assertGreater(
            seniority_alignment(manager_spec, manager),
            seniority_alignment(manager_spec, ic),
        )

    def test_rank_with_summary_reports_candidate_and_block_counts(self) -> None:
        strong = overlay(
            candidate_id="CAND_0000001",
            compounds=["production_embeddings_retrieval"],
            signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "production_delivery",
            ],
        )
        blocked = overlay(
            candidate_id="CAND_0000002",
            honeypot_rules=["company_pre_founding"],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "overlay.jsonl"
            path.write_text(
                json.dumps(strong) + "\n" + json.dumps(blocked) + "\n",
                encoding="utf-8",
            )

            run = rank_with_summary(self.spec, path, limit=1)

        self.assertEqual(run.candidate_count, 2)
        self.assertEqual(run.eligible_count, 1)
        self.assertEqual(run.blocked_count, 1)
        self.assertEqual(run.rows[0].candidate_id, "CAND_0000001")

    def test_rank_with_summary_uses_precomputed_semantic_tokens(self) -> None:
        strong = overlay(
            candidate_id="CAND_0000001",
            compounds=["production_embeddings_retrieval"],
            signals=[
                "embeddings",
                "retrieval_search",
                "ranking_recommendation_matching",
                "production_delivery",
            ],
        )
        strong["semantic_tokens"] = [
            "production",
            "retrieval",
            "ranking",
            "evaluation",
        ]

        self.assertGreater(semantic_score(self.spec, strong), 0)

    def test_rank_raw_with_summary_scores_candidate_jsonl(self) -> None:
        candidate = {
            "candidate_id": "CAND_0000001",
            "profile": {
                "current_title": "Senior AI Engineer",
                "years_of_experience": 7.0,
                "current_company": "SearchCo",
                "current_industry": "AI/ML",
                "location": "Noida",
                "country": "India",
            },
            "career_history": [
                {
                    "company": "SearchCo",
                    "title": "Senior AI Engineer",
                    "start_date": "2023-01-01",
                    "end_date": None,
                    "duration_months": 41,
                    "is_current": True,
                    "industry": "AI/ML",
                    "description": (
                        "Owned and shipped production embedding retrieval and "
                        "ranking evaluation systems."
                    ),
                }
            ],
            "education": [],
            "skills": [
                {"name": "Python", "proficiency": "advanced", "duration_months": 60}
            ],
            "redrob_signals": {
                "last_active_date": "2026-05-20",
                "signup_date": "2025-01-01",
                "open_to_work_flag": True,
                "recruiter_response_rate": 0.8,
                "avg_response_time_hours": 10,
                "notice_period_days": 30,
                "profile_views_received_30d": 20,
                "search_appearance_30d": 100,
                "saved_by_recruiters_30d": 5,
                "interview_completion_rate": 0.9,
                "offer_acceptance_rate": 0.8,
                "github_activity_score": 50,
                "willing_to_relocate": False,
                "preferred_work_mode": "hybrid",
                "expected_salary_range_inr_lpa": {"min": 10, "max": 20},
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidates = root / "candidates.jsonl"
            kb = root / "kb.json"
            candidates.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            kb.write_text('{"companies": {}, "technologies": {}}\n', encoding="utf-8")

            run = rank_raw_with_summary(self.spec, candidates, kb, limit=1)

        self.assertEqual(run.candidate_count, 1)
        self.assertEqual(run.eligible_count, 1)
        self.assertEqual(run.rows[0].candidate_id, "CAND_0000001")


if __name__ == "__main__":
    unittest.main()
