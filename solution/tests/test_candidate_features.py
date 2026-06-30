import unittest

from solution.candidate_features import build_candidate_overlay


def candidate(description: str) -> dict:
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "current_title": "Senior AI Engineer",
            "years_of_experience": 7.0,
            "current_company": "SearchCo",
            "current_industry": "AI/ML",
            "location": "Noida, Uttar Pradesh",
            "country": "India",
        },
        "career_history": [
            {
                "company": "SearchCo",
                "title": "Senior AI Engineer",
                "industry": "AI/ML",
                "description": description,
                "duration_months": 36,
                "is_current": True,
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "advanced", "duration_months": 60},
            {"name": "FAISS", "proficiency": "advanced", "duration_months": 24},
        ],
        "redrob_signals": {
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.7,
            "avg_response_time_hours": 12,
            "notice_period_days": 30,
            "profile_views_received_30d": 20,
            "search_appearance_30d": 100,
            "saved_by_recruiters_30d": 5,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.8,
            "github_activity_score": 50,
            "willing_to_relocate": False,
            "preferred_work_mode": "hybrid",
        },
    }


class CandidateFeatureTests(unittest.TestCase):
    def test_build_candidate_overlay_extracts_career_compounds(self) -> None:
        overlay = build_candidate_overlay(
            candidate(
                "Owned and shipped a production embedding retrieval and ranking "
                "system using FAISS. Improved NDCG through online experiments."
            )
        )

        career = overlay["career_evidence"]
        self.assertIn("production_embeddings_retrieval", career["any_career_compound_ids"])
        self.assertIn("evaluated_ranking_system", career["any_career_compound_ids"])
        self.assertIn("python_engineering", overlay["skill_overlay"]["skill_signal_ids"])
        self.assertEqual(overlay["logistics_overlay"]["location_bucket"], "noida")

    def test_data_hybrid_role_does_not_create_vector_search_signal(self) -> None:
        overlay = build_candidate_overlay(
            candidate(
                "Backend + data hybrid role at a growth-stage startup. Built the "
                "company's first proper data warehouse, orchestration layer, and BI "
                "integration. Shipped a couple of small predictive features but the "
                "bulk of the role was data infrastructure."
            )
        )

        career = overlay["career_evidence"]
        self.assertNotIn("vector_hybrid_infrastructure", career["any_career_signal_ids"])
        self.assertNotIn(
            "production_vector_or_hybrid_search",
            career["any_career_compound_ids"],
        )

    def test_plain_language_search_discovery_maps_to_ranking_compounds(self) -> None:
        overlay = build_candidate_overlay(
            candidate(
                "Owned the search and discovery experience end-to-end at a consumer "
                "product, from how content is represented internally through to how "
                "the most relevant results appear for each user's intent. The work "
                "spanned data infrastructure, ranking algorithms, evaluation "
                "methodology, and direct collaboration with product on relevance."
            )
        )

        career = overlay["career_evidence"]
        self.assertIn("ranking_recommendation_matching", career["any_career_signal_ids"])
        self.assertIn("ranking_evaluation", career["any_career_signal_ids"])
        self.assertIn("end_to_end_intelligence_ownership", career["any_career_compound_ids"])

    def test_relevant_matches_plain_language_maps_to_evaluated_ranking(self) -> None:
        overlay = build_candidate_overlay(
            candidate(
                "Built systems that understand what users are looking for and connect "
                "them to the most relevant matches across a large dataset. Recent "
                "project was a complete overhaul of the matching layer; took it from "
                "a hand-tuned heuristic system to one with explicit modeling and "
                "evaluation."
            )
        )

        career = overlay["career_evidence"]
        self.assertIn("ranking_recommendation_matching", career["any_career_signal_ids"])
        self.assertIn("ranking_evaluation", career["any_career_signal_ids"])
        self.assertIn("evaluated_ranking_system", career["any_career_compound_ids"])


if __name__ == "__main__":
    unittest.main()
