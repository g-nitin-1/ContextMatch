import unittest
from datetime import date

from analysis.candidate_overlay import (
    evaluate_overlay_rules,
    evaluate_recent_shallow_llm_only,
    evaluate_research_only_without_production,
    evaluate_senior_not_coding_recently,
    evaluate_services_only_entire_career,
    load_skill_signal_patterns,
    summarize_skills,
)


AS_OF = date(2026, 6, 1)


def role(
    *,
    template_id: str = "career_test",
    company: str = "Example",
    title: str = "Engineer",
    industry: str = "Software",
    signals: list[str] | None = None,
    compounds: list[str] | None = None,
    duration_months: int = 10,
    start_date: str = "2025-08-01",
    end_date: str | None = None,
    is_current: bool = True,
    description: str = "",
) -> dict:
    return {
        "template_id": template_id,
        "company": company,
        "title": title,
        "industry": industry,
        "signals": signals or [],
        "compounds": compounds or [],
        "duration_months": duration_months,
        "start_date": start_date,
        "end_date": end_date,
        "is_current": is_current,
        "description": description,
    }


class CandidateOverlayRuleTests(unittest.TestCase):
    def test_services_only_fires_only_without_product_guard(self) -> None:
        verdict = evaluate_services_only_entire_career(
            [
                role(industry="IT Services", signals=["consulting_services_context"]),
                role(industry="Consulting", signals=["consulting_services_context"]),
            ]
        )
        self.assertTrue(verdict["fired"])

        guarded = evaluate_services_only_entire_career(
            [
                role(industry="IT Services", signals=["consulting_services_context"]),
                role(industry="SaaS", signals=["product_context"]),
            ]
        )
        self.assertFalse(guarded["fired"])
        self.assertIn("product", guarded["reason"])

    def test_research_only_requires_whole_career_and_no_production(self) -> None:
        verdict = evaluate_research_only_without_production(
            [
                role(
                    title="Research Scientist",
                    industry="Academic Lab",
                    signals=["research_only_context"],
                )
            ]
        )
        self.assertTrue(verdict["fired"])

        guarded = evaluate_research_only_without_production(
            [
                role(
                    title="Research Scientist",
                    industry="Academic Lab",
                    signals=["research_only_context"],
                ),
                role(signals=["production_delivery"]),
            ]
        )
        self.assertFalse(guarded["fired"])
        self.assertIn("production", guarded["reason"])

    def test_research_only_ignores_generic_content_research(self) -> None:
        verdict = evaluate_research_only_without_production(
            [
                role(
                    title="Content Strategist",
                    industry="Software",
                    description=(
                        "Used LLM tools for research, drafting, and editing "
                        "developer-tool articles."
                    ),
                )
            ]
        )
        self.assertFalse(verdict["fired"])

    def test_recent_shallow_llm_guarded_by_deep_production_rag(self) -> None:
        shallow = evaluate_recent_shallow_llm_only(
            [role(signals=["llm_application_context"], duration_months=8)],
            summarize_skills([]),
            AS_OF,
        )
        self.assertTrue(shallow["fired"])

        deep = evaluate_recent_shallow_llm_only(
            [
                role(
                    signals=[
                        "llm_application_context",
                        "retrieval_search",
                        "production_delivery",
                    ],
                    compounds=["production_embeddings_retrieval"],
                    duration_months=8,
                )
            ],
            summarize_skills([]),
            AS_OF,
        )
        self.assertFalse(deep["fired"])
        self.assertIn("production ML", deep["reason"])

    def test_senior_not_coding_recently_respects_hands_on_guard(self) -> None:
        profile = {"current_title": "Senior Engineering Manager"}
        verdict = evaluate_senior_not_coding_recently(
            [
                role(
                    title="Senior Engineering Manager",
                    signals=["mentoring_leadership"],
                    duration_months=18,
                )
            ],
            profile,
            AS_OF,
        )
        self.assertTrue(verdict["fired"])

        guarded = evaluate_senior_not_coding_recently(
            [
                role(
                    title="Senior ML Engineer",
                    signals=["python_engineering", "production_delivery"],
                    duration_months=18,
                )
            ],
            {"current_title": "Senior ML Engineer"},
            AS_OF,
        )
        self.assertFalse(guarded["fired"])
        self.assertIn("hands-on", guarded["reason"])

    def test_senior_title_alone_does_not_clear_hands_on_guard(self) -> None:
        verdict = evaluate_senior_not_coding_recently(
            [
                role(
                    title="Senior AI Engineer",
                    signals=["mentoring_leadership"],
                    duration_months=18,
                )
            ],
            {"current_title": "Senior AI Engineer"},
            AS_OF,
        )
        self.assertTrue(verdict["fired"])

    def test_skill_retrieval_pattern_avoids_bare_search(self) -> None:
        summary = summarize_skills(
            [
                {
                    "name": "Job Search",
                    "proficiency": "advanced",
                    "duration_months": 24,
                },
                {
                    "name": "RAG",
                    "proficiency": "advanced",
                    "duration_months": 24,
                },
            ],
            load_skill_signal_patterns(),
        )
        self.assertIn("retrieval_search", summary["skill_signal_ids"])
        job_search_only = summarize_skills(
            [
                {
                    "name": "Job Search",
                    "proficiency": "advanced",
                    "duration_months": 24,
                }
            ],
            load_skill_signal_patterns(),
        )
        self.assertNotIn("retrieval_search", job_search_only["skill_signal_ids"])

    def test_rule_bundle_returns_all_overlay_verdicts(self) -> None:
        verdicts = evaluate_overlay_rules(
            [role(industry="IT Services", signals=["consulting_services_context"])],
            summarize_skills([]),
            {"current_title": "Business Analyst"},
            AS_OF,
        )
        self.assertEqual(
            set(verdicts),
            {
                "services_only_entire_career",
                "research_only_without_production",
                "recent_shallow_llm_only",
                "senior_not_coding_recently",
            },
        )


if __name__ == "__main__":
    unittest.main()
