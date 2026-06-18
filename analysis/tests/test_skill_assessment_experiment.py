import unittest

from analysis.idea2_scorer import career_evidence_score, skill_score
from analysis.skill_assessment_experiment import (
    ASSESSMENT_MAX,
    assessment_quality_multiplier,
    summarize_assessments,
)


PATTERNS = {
    "retrieval_search": (r"\bBM25\b",),
    "vector_hybrid_infrastructure": (r"\bPinecone\b",),
}


class SkillAssessmentExperimentTests(unittest.TestCase):
    def test_missing_assessment_is_neutral(self) -> None:
        evidence = summarize_assessments({}, PATTERNS)
        self.assertEqual(evidence["assessment_score"], 0.0)

    def test_irrelevant_assessment_is_neutral(self) -> None:
        evidence = summarize_assessments({"Excel": 99}, PATTERNS)
        self.assertEqual(evidence["assessment_score"], 0.0)
        self.assertEqual(evidence["unmapped_assessment_names"], ["Excel"])

    def test_strong_assessment_outweighs_one_self_declared_skill(self) -> None:
        assessed = summarize_assessments({"BM25": 90}, PATTERNS)
        self_declared = skill_score(
            {
                "skill_overlay": {
                    "skill_signal_ids": ["retrieval_search"],
                    "advanced_or_expert_signal_counts": {"retrieval_search": 1},
                    "max_duration_months_by_signal": {"retrieval_search": 48},
                }
            }
        )
        self.assertGreater(assessed["assessment_score"], self_declared)

    def test_production_career_evidence_remains_stronger(self) -> None:
        assessed = summarize_assessments(
            {"BM25": 95, "Pinecone": 95},
            PATTERNS,
        )
        career = career_evidence_score(
            {
                "career_evidence": {
                    "any_career_compound_ids": [
                        "production_embeddings_retrieval",
                        "evaluated_ranking_system",
                    ],
                    "current_compound_ids": [
                        "production_embeddings_retrieval",
                    ],
                    "any_career_signal_ids": [
                        "embeddings",
                        "retrieval_search",
                        "production_delivery",
                        "ranking_evaluation",
                    ],
                    "current_signal_ids": ["retrieval_search"],
                }
            }
        )
        self.assertGreater(career, assessed["assessment_score"])

    def test_modifier_is_bounded(self) -> None:
        evidence = summarize_assessments(
            {"BM25": 100, "Pinecone": 100},
            PATTERNS,
        )
        self.assertLessEqual(evidence["assessment_score"], ASSESSMENT_MAX)

    def test_low_score_does_not_become_positive_evidence(self) -> None:
        evidence = summarize_assessments({"BM25": 20}, PATTERNS)
        self.assertLess(evidence["assessment_score"], 0.0)
        self.assertLess(assessment_quality_multiplier(20), 0.0)


if __name__ == "__main__":
    unittest.main()
