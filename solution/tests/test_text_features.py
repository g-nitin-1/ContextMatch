import unittest

from solution.text_features import (
    career_weighted_text,
    career_weighted_tokens,
    query_coverage_score,
    query_coverage_score_from_tokens,
)


class TextFeatureTests(unittest.TestCase):
    def test_career_text_is_weighted_before_skills(self) -> None:
        candidate = {
            "profile": {"headline": "AI enthusiast", "summary": "Learning prompts"},
            "career_history": [
                {
                    "title": "Senior Engineer",
                    "company": "SearchCo",
                    "industry": "Internet",
                    "description": "Built production retrieval and ranking evaluation.",
                }
            ],
            "skills": [{"name": "Photoshop"}],
        }

        text = career_weighted_text(candidate)

        self.assertGreater(text.count("production retrieval"), 1)
        self.assertIn("Photoshop", text)

    def test_query_coverage_prefers_relevant_text(self) -> None:
        queries = ("production retrieval ranking evaluation",)

        relevant = query_coverage_score(
            queries,
            "Built production retrieval and ranking evaluation systems",
        )
        irrelevant = query_coverage_score(queries, "Managed accounting and sales")

        self.assertGreater(relevant, irrelevant)

    def test_query_coverage_from_tokens_matches_text_path(self) -> None:
        queries = ("production retrieval ranking evaluation",)
        text = "Built production retrieval and ranking evaluation systems"

        self.assertEqual(
            query_coverage_score(queries, text),
            query_coverage_score_from_tokens(queries, {"built", "production", "retrieval", "ranking", "evaluation", "systems"}),
        )

    def test_career_weighted_tokens_extracts_candidate_tokens(self) -> None:
        candidate = {
            "profile": {"headline": "", "summary": ""},
            "career_history": [
                {
                    "title": "Senior Engineer",
                    "company": "SearchCo",
                    "industry": "Internet",
                    "description": "Built production retrieval.",
                }
            ],
            "skills": [],
        }

        self.assertIn("retrieval", career_weighted_tokens(candidate))


if __name__ == "__main__":
    unittest.main()
