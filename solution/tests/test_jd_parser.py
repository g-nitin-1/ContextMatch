import tempfile
import unittest
from pathlib import Path

from solution.jd_parser import parse_jd, spec_from_jd_text


class JdParserTests(unittest.TestCase):
    def test_spec_from_jd_text_detects_ranking_retrieval_role(self) -> None:
        spec = spec_from_jd_text(
            "Senior AI Engineer\n"
            "Build production retrieval, ranking, embeddings, and vector search. "
            "Own NDCG and online experiments for a recommendation system."
        )

        self.assertEqual(spec.role_title, "Senior AI Engineer")
        self.assertIn("production_retrieval", [item.id for item in spec.must_have])
        self.assertIn("evaluated_ranking", [item.id for item in spec.must_have])
        self.assertIn("retrieval_search", spec.evidence_signal_ids)
        production = next(
            item for item in spec.must_have if item.id == "production_retrieval"
        )
        self.assertIn("end_to_end_intelligence_ownership", production.compounds)

    def test_parse_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "jd.txt"
            path.write_text(
                "Lead Machine Learning Engineer\n"
                "Ship production ML systems and mentor engineers.",
                encoding="utf-8",
            )

            spec = parse_jd(path)

        self.assertEqual(spec.role_title, "Lead Machine Learning Engineer")
        self.assertTrue(spec.must_have)

    def test_seniority_for_junior_role(self) -> None:
        spec = spec_from_jd_text(
            "Junior Data Analyst\n"
            "Entry-level role for dashboards, SQL analysis, and reporting."
        )

        self.assertEqual(spec.seniority["level"], "junior")
        self.assertGreater(spec.seniority["strength"], 0)

    def test_seniority_for_engineering_manager_role(self) -> None:
        spec = spec_from_jd_text(
            "Engineering Manager\n"
            "Manage a team of backend engineers, handle hiring, mentoring, "
            "delivery ownership, and performance reviews."
        )

        self.assertEqual(spec.seniority["track"], "management")
        self.assertIn("people_leadership", [item.id for item in spec.must_have])

    def test_seniority_neutral_for_plain_backend_role(self) -> None:
        spec = spec_from_jd_text(
            "Backend Engineer\n"
            "Build APIs, data models, and reliable services."
        )

        self.assertEqual(spec.seniority["level"], "unspecified")
        self.assertEqual(spec.seniority["track"], "either")
        self.assertEqual(spec.seniority["strength"], 0.0)

    def test_seniority_for_senior_ic_role(self) -> None:
        spec = spec_from_jd_text(
            "Senior AI Engineer — Founding Team\n"
            "This role writes code. We need a hands-on individual contributor "
            "who owns production retrieval systems end-to-end. If you moved into "
            "architecture, principal, or management roles, this is not that role."
        )

        self.assertEqual(spec.seniority["level"], "senior")
        self.assertEqual(spec.seniority["track"], "ic")
        self.assertGreater(spec.seniority["strength"], 0)


if __name__ == "__main__":
    unittest.main()
