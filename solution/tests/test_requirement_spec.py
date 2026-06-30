import unittest

from solution.requirement_spec import SPEC_VERSION, RequirementSpec, load_spec


class RequirementSpecTests(unittest.TestCase):
    def test_default_spec_loads(self) -> None:
        spec = load_spec()

        self.assertEqual(spec.schema_version, SPEC_VERSION)
        self.assertEqual(spec.role_title, "Senior AI Engineer")
        self.assertIn("retrieval_search", spec.evidence_signal_ids)
        self.assertIn("production_embeddings_retrieval", spec.compound_ids)
        self.assertIn("end_to_end_intelligence_ownership", spec.compound_ids)
        self.assertIn("services_only_entire_career", spec.hard_disqualifiers)

    def test_legacy_single_compound_loads_as_compound_set(self) -> None:
        spec = RequirementSpec.from_dict(
            {
                "schema_version": SPEC_VERSION,
                "role_title": "Role",
                "seniority": {},
                "must_have": [
                    {
                        "id": "retrieval",
                        "desc": "Retrieval systems",
                        "weight": 1.0,
                        "evidence_signals": ["retrieval_search"],
                        "compound": "production_embeddings_retrieval",
                    }
                ],
                "semantic_queries": ["retrieval systems"],
            }
        )

        item = spec.must_have[0]
        self.assertEqual(item.compound, "production_embeddings_retrieval")
        self.assertEqual(item.compounds, ("production_embeddings_retrieval",))

    def test_multiple_compounds_are_supported(self) -> None:
        spec = RequirementSpec.from_dict(
            {
                "schema_version": SPEC_VERSION,
                "role_title": "Role",
                "seniority": {},
                "must_have": [
                    {
                        "id": "retrieval",
                        "desc": "Retrieval systems",
                        "weight": 1.0,
                        "evidence_signals": ["retrieval_search"],
                        "compound": "production_embeddings_retrieval",
                        "compounds": [
                            "production_embeddings_retrieval",
                            "end_to_end_intelligence_ownership",
                        ],
                    }
                ],
                "semantic_queries": ["retrieval systems"],
            }
        )

        item = spec.must_have[0]
        self.assertEqual(item.compound, "production_embeddings_retrieval")
        self.assertEqual(
            item.compounds,
            (
                "production_embeddings_retrieval",
                "end_to_end_intelligence_ownership",
            ),
        )

    def test_must_have_is_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "must_have"):
            RequirementSpec.from_dict(
                {
                    "schema_version": SPEC_VERSION,
                    "role_title": "Role",
                    "seniority": {},
                    "must_have": [],
                    "semantic_queries": ["query"],
                }
            )


if __name__ == "__main__":
    unittest.main()
