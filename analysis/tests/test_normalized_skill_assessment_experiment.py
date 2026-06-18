import unittest

from analysis.normalized_skill_assessment_experiment import (
    ASSESSMENT_Z_WEIGHT,
    NORMALIZED_MAX,
    NORMALIZED_MIN,
    build_normalization_stats,
    normalization_group,
    normalized_assessment_score,
    normalized_signal_assessment_score,
)


class NormalizedSkillAssessmentExperimentTests(unittest.TestCase):
    def test_normalization_groups_pool_small_senior_cohorts(self) -> None:
        self.assertEqual(
            normalization_group("senior_explicit_ai"),
            "senior_pooled",
        )
        self.assertEqual(
            normalization_group("senior_plain_language"),
            "senior_pooled",
        )
        self.assertEqual(normalization_group("applied_ml"), "applied_ml")

    def test_group_mean_is_neutral(self) -> None:
        stats = {"mean": 70.0, "stddev": 10.0}
        self.assertEqual(
            normalized_assessment_score({"retrieval_search": 70.0}, stats),
            0.0,
        )

    def test_above_peer_mean_is_positive_and_below_is_negative(self) -> None:
        stats = {"mean": 70.0, "stddev": 10.0}
        self.assertGreater(
            normalized_assessment_score({"retrieval_search": 80.0}, stats),
            0.0,
        )
        self.assertLess(
            normalized_assessment_score({"retrieval_search": 60.0}, stats),
            0.0,
        )

    def test_normalized_modifier_is_bounded(self) -> None:
        stats = {"mean": 50.0, "stddev": 1.0}
        self.assertEqual(
            normalized_assessment_score(
                {
                    "retrieval_search": 100.0,
                    "vector_hybrid_infrastructure": 100.0,
                },
                stats,
            ),
            NORMALIZED_MAX,
        )
        self.assertEqual(
            normalized_assessment_score(
                {
                    "retrieval_search": 0.0,
                    "vector_hybrid_infrastructure": 0.0,
                },
                stats,
            ),
            NORMALIZED_MIN,
        )

    def test_one_standard_deviation_uses_signal_weight_hierarchy(self) -> None:
        stats = {"mean": 70.0, "stddev": 10.0}
        contribution = normalized_signal_assessment_score(
            80.0,
            0.10,
            stats,
        )
        self.assertAlmostEqual(contribution, 0.10 * ASSESSMENT_Z_WEIGHT)

    def test_stats_require_enough_observations(self) -> None:
        rows = [
            {
                "candidate_id": f"CAND_{index:07d}",
                "summary_archetype": "applied_ml",
            }
            for index in range(10)
        ]
        assessment_index = {
            row["candidate_id"]: {
                "mapped_signal_scores": {
                    "retrieval_search": 50.0 + index,
                },
            }
            for index, row in enumerate(rows)
        }
        with self.assertRaisesRegex(ValueError, "only 10 observations"):
            build_normalization_stats(rows, assessment_index)


if __name__ == "__main__":
    unittest.main()
