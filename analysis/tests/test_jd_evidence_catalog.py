import json
import tempfile
import unittest
from pathlib import Path

from analysis.jd_evidence_catalog import annotate_text, load_rubric


class JDEvidenceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rubric = load_rubric()

    def test_detects_production_embedding_retrieval(self) -> None:
        text = (
            "Led the migration to embedding-based search for a candidate corpus. "
            "The production system used BGE embeddings and Pinecone retrieval, "
            "with index versioning and A/B testing against recruiter engagement."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertIn("embeddings", annotation["signals"])
        self.assertIn("retrieval_search", annotation["signals"])
        self.assertIn("vector_hybrid_infrastructure", annotation["signals"])
        self.assertIn("production_delivery", annotation["signals"])
        self.assertIn(
            "production_embeddings_retrieval", annotation["compounds"]
        )
        self.assertIn(
            "production_vector_or_hybrid_search", annotation["compounds"]
        )

    def test_plain_language_ranking_evidence_does_not_require_ai_keywords(
        self,
    ) -> None:
        text = (
            "Designed the ranking layer for a product used by millions. "
            "Owned the evaluation framework and kept it healthy in production."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertIn(
            "ranking_recommendation_matching", annotation["signals"]
        )
        self.assertIn("ranking_evaluation", annotation["signals"])
        self.assertIn("operational_ownership", annotation["signals"])
        self.assertIn("evaluated_ranking_system", annotation["compounds"])
        self.assertNotIn("embeddings", annotation["signals"])

    def test_query_understanding_counts_as_retrieval_evidence(self) -> None:
        text = (
            "Built infrastructure to surface relevant content to users. "
            "The work covered query understanding, index refresh, and ranking "
            "calibration."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertIn("retrieval_search", annotation["signals"])
        self.assertIn(
            "ranking_recommendation_matching", annotation["signals"]
        )
        self.assertIn("ranking_evaluation", annotation["signals"])

    def test_ab_interpretation_counts_as_ranking_evaluation(self) -> None:
        text = (
            "Built and shipped a production recommendation system. "
            "Ran it in a live A/B test and interpreted recruiter engagement "
            "metrics against the legacy ranker."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertIn(
            "ranking_recommendation_matching", annotation["signals"]
        )
        self.assertIn("ranking_evaluation", annotation["signals"])
        self.assertIn("evaluated_ranking_system", annotation["compounds"])

    def test_marketing_ai_keywords_do_not_create_ml_evidence(self) -> None:
        text = (
            "Marketing leadership at a SaaS company. Owned content marketing, "
            "SEO, paid acquisition, and AI-assisted campaign drafting."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertNotIn("embeddings", annotation["signals"])
        self.assertNotIn("retrieval_search", annotation["signals"])
        self.assertNotIn(
            "ranking_recommendation_matching", annotation["signals"]
        )
        self.assertFalse(annotation["compounds"])

    def test_generic_feedback_loop_is_not_online_experimentation(self) -> None:
        text = (
            "Managed a customer-support team and owned the customer feedback "
            "loop to product."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertNotIn("online_experimentation", annotation["signals"])

    def test_brand_production_side_is_not_technical_delivery(self) -> None:
        text = (
            "Owned brand identity and packaging design. Managed the production "
            "side of brand and packaging work."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertNotIn("production_delivery", annotation["signals"])

    def test_model_serving_integration_does_not_claim_delivery_ownership(self) -> None:
        text = (
            "Integrated a model-serving service built by another team into our "
            "API layer; my work was integration and observability, not the model."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertNotIn("production_delivery", annotation["signals"])
        self.assertIn("operational_ownership", annotation["signals"])

    def test_denied_productionization_does_not_claim_operational_ownership(
        self,
    ) -> None:
        text = (
            "The model is now used by the retention team, though my role was "
            "more on modeling than productionization."
        )
        annotation = annotate_text(text, self.rubric)
        self.assertIn("production_delivery", annotation["signals"])
        self.assertNotIn("operational_ownership", annotation["signals"])

    def test_whole_career_overlay_rules_are_explicit(self) -> None:
        overlays = self.rubric["candidate_overlay_rules"]
        self.assertEqual(
            overlays["services_only_entire_career"]["evaluation_scope"],
            "entire_career",
        )
        self.assertEqual(
            overlays["research_only_without_production"]["evaluation_scope"],
            "entire_career",
        )
        self.assertIn(
            "single consulting/services role",
            overlays["services_only_entire_career"]["must_not_trigger_from"],
        )

    def test_candidate_overlay_rules_are_well_formed(self) -> None:
        required = {
            "jd_strength": str,
            "evaluation_scope": str,
            "description": str,
            "required_inputs": list,
            "must_not_trigger_from": str,
            "automatic_tier_zero": bool,
        }
        overlays = self.rubric["candidate_overlay_rules"]
        self.assertGreaterEqual(len(overlays), 4)
        for rule_id, rule in overlays.items():
            with self.subTest(rule_id=rule_id):
                for field, expected_type in required.items():
                    self.assertIn(field, rule)
                    self.assertIsInstance(rule[field], expected_type)
                self.assertTrue(rule["required_inputs"])

    def test_skill_signal_patterns_are_well_formed(self) -> None:
        skill_patterns = self.rubric["skill_signal_patterns"]
        self.assertIn("retrieval_search", skill_patterns)
        self.assertIn("ml_depth", skill_patterns)
        for signal_id, entry in skill_patterns.items():
            with self.subTest(signal_id=signal_id):
                self.assertIsInstance(entry["label"], str)
                self.assertIsInstance(entry["description"], str)
                self.assertIsInstance(entry["patterns"], list)
                self.assertTrue(entry["patterns"])
                for pattern in entry["patterns"]:
                    self.assertIsInstance(pattern, str)

    def test_load_rubric_rejects_malformed_overlay_rule(self) -> None:
        bad_rubric = json.loads(json.dumps(self.rubric))
        del bad_rubric["candidate_overlay_rules"][
            "services_only_entire_career"
        ]["evaluation_scope"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bad_rubric.json"
            path.write_text(json.dumps(bad_rubric), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evaluation_scope"):
                load_rubric(path)

    def test_load_rubric_rejects_malformed_skill_patterns(self) -> None:
        bad_rubric = json.loads(json.dumps(self.rubric))
        bad_rubric["skill_signal_patterns"]["retrieval_search"]["patterns"] = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bad_rubric.json"
            path.write_text(json.dumps(bad_rubric), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "patterns"):
                load_rubric(path)


if __name__ == "__main__":
    unittest.main()
