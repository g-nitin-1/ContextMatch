import unittest
from copy import deepcopy

from analysis.idea2_scorer import WORLD_CONFIGS, score_candidate


def overlay_record(
    *,
    candidate_id: str = "CAND_TEST",
    archetype: str = "senior_plain_language",
    atom: str = "fine_atom_05",
    compounds: list[str] | None = None,
    signals: list[str] | None = None,
    skill_signals: list[str] | None = None,
    integrity_risk: str = "none",
    high_confidence_rules: list[str] | None = None,
    honeypot_proxy_rules: list[str] | None = None,
    overlay_rules: list[str] | None = None,
    inactive_days: int = 10,
    response_rate: float = 0.8,
    current_title: str = "Senior AI Engineer",
    location_bucket: str = "pune",
) -> dict:
    fired_rules = set(overlay_rules or [])
    return {
        "candidate_id": candidate_id,
        "static": {
            "summary_archetype": archetype,
            "fine_static_atom": atom,
            "static_class": "static_test",
            "current_title": current_title,
            "current_company": "Example",
            "current_industry": "AI/ML",
            "years_of_experience": 8.0,
        },
        "career_evidence": {
            "any_career_compound_ids": compounds or [],
            "current_compound_ids": compounds or [],
            "any_career_signal_ids": signals or [],
            "current_signal_ids": signals or [],
            "any_career_risk_context_ids": [],
            "current_risk_context_ids": [],
        },
        "skill_overlay": {
            "skill_signal_ids": skill_signals or [],
            "advanced_or_expert_signal_counts": {
                signal: 1 for signal in skill_signals or []
            },
            "max_duration_months_by_signal": {
                signal: 36 for signal in skill_signals or []
            },
        },
        "availability_overlay": {
            "inactive_days": inactive_days,
            "open_to_work": True,
            "notice_period_days": 30,
            "response_rate": response_rate,
            "response_time_hours": 12,
            "saved_by_recruiters_30d": 10,
            "search_appearance_30d": 150,
            "profile_views_30d": 40,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.7,
            "verification_count": 3,
            "github_activity_score": 70,
        },
        "logistics_overlay": {"location_bucket": location_bucket},
        "integrity_overlay": {
            "risk_level": integrity_risk,
            "high_confidence_rules": high_confidence_rules or [],
            "honeypot_proxy_rules": honeypot_proxy_rules or [],
        },
        "candidate_overlay_rules": {
            rule: {"fired": rule in fired_rules}
            for rule in (
                "services_only_entire_career",
                "research_only_without_production",
                "recent_shallow_llm_only",
                "senior_not_coding_recently",
            )
        },
    }


class Idea2ScorerTests(unittest.TestCase):
    def test_honeypot_proxy_is_hard_suppressed_in_hard_worlds(self) -> None:
        clean = overlay_record(
            compounds=["evaluated_ranking_system"],
            signals=["ranking_evaluation", "retrieval_search"],
        )
        honeypot = overlay_record(
            compounds=["evaluated_ranking_system"],
            signals=["ranking_evaluation", "retrieval_search"],
            integrity_risk="high",
            high_confidence_rules=["company_pre_founding"],
            honeypot_proxy_rules=["company_pre_founding"],
        )

        for world in WORLD_CONFIGS:
            clean_score = score_candidate(clean, world)["score"]
            honeypot_score = score_candidate(honeypot, world)["score"]
            self.assertLess(honeypot_score, clean_score)
            if world.integrity_policy == "hard":
                self.assertLess(honeypot_score, -50.0)

    def test_behavior_cannot_promote_irrelevant_profile_above_strong_senior(self) -> None:
        strong_senior = overlay_record(
            compounds=[
                "evaluated_ranking_system",
                "production_embeddings_retrieval",
                "shipper_with_evaluation_depth",
            ],
            signals=[
                "embeddings",
                "ranking_evaluation",
                "retrieval_search",
                "production_delivery",
            ],
            inactive_days=180,
            response_rate=0.2,
        )
        active_irrelevant = overlay_record(
            archetype="general_professional",
            atom="fine_atom_06",
            compounds=[],
            signals=[],
            skill_signals=[],
            inactive_days=1,
            response_rate=1.0,
        )

        for world in WORLD_CONFIGS:
            self.assertGreater(
                score_candidate(strong_senior, world)["score"],
                score_candidate(active_irrelevant, world)["score"],
            )

    def test_overlay_penalty_is_bounded_for_data_backend_tail(self) -> None:
        clean = overlay_record(
            archetype="data_backend_adjacent",
            atom="fine_atom_07",
            signals=["python_engineering"],
            skill_signals=["python_engineering", "ml_depth"],
        )
        penalized = overlay_record(
            archetype="data_backend_adjacent",
            atom="fine_atom_07",
            signals=["python_engineering"],
            skill_signals=["python_engineering", "ml_depth"],
            overlay_rules=["senior_not_coding_recently"],
        )

        for world in WORLD_CONFIGS:
            gap = (
                score_candidate(clean, world)["score"]
                - score_candidate(penalized, world)["score"]
            )
            self.assertGreater(gap, 0.0)
            self.assertLess(gap, 0.5)

    def test_removing_career_evidence_lowers_score_but_keeps_skill_signal(self) -> None:
        original = overlay_record(
            compounds=[
                "evaluated_ranking_system",
                "production_embeddings_retrieval",
                "shipper_with_evaluation_depth",
            ],
            signals=[
                "embeddings",
                "ranking_evaluation",
                "retrieval_search",
                "production_delivery",
            ],
            skill_signals=["embeddings", "retrieval_search", "python_engineering"],
        )
        no_career = deepcopy(original)
        no_career["career_evidence"] = {
            "any_career_compound_ids": [],
            "current_compound_ids": [],
            "any_career_signal_ids": [],
            "current_signal_ids": [],
            "any_career_risk_context_ids": [],
            "current_risk_context_ids": [],
        }

        for world in WORLD_CONFIGS:
            original_score = score_candidate(original, world)
            changed_score = score_candidate(no_career, world)
            self.assertGreater(original_score["score"], changed_score["score"])
            self.assertGreater(changed_score["skill_overlay"], 0.0)
            self.assertLessEqual(
                original_score["score"] - changed_score["score"],
                2.1,
            )

    def test_irrelevant_title_lowers_score_without_overriding_career(self) -> None:
        relevant = overlay_record(
            compounds=["evaluated_ranking_system"],
            signals=["ranking_evaluation", "retrieval_search"],
            current_title="Senior Machine Learning Engineer",
        )
        irrelevant = deepcopy(relevant)
        irrelevant["static"]["current_title"] = "HR Manager"

        for world in WORLD_CONFIGS:
            relevant_score = score_candidate(relevant, world)
            irrelevant_score = score_candidate(irrelevant, world)
            gap = relevant_score["score"] - irrelevant_score["score"]
            self.assertGreater(gap, 0.0)
            self.assertLess(gap, 0.5)
            self.assertGreater(irrelevant_score["career_evidence"], 0.0)

    def test_worsening_availability_lowers_score_by_a_bounded_amount(self) -> None:
        available = overlay_record(inactive_days=10, response_rate=0.8)
        unavailable = deepcopy(available)
        unavailable["availability_overlay"].update(
            {
                "inactive_days": 240,
                "open_to_work": False,
                "notice_period_days": 120,
                "response_rate": 0.2,
                "response_time_hours": 240,
                "saved_by_recruiters_30d": 0,
                "search_appearance_30d": 0,
                "profile_views_30d": 0,
                "interview_completion_rate": 0.4,
                "offer_acceptance_rate": 0.3,
                "verification_count": 0,
                "github_activity_score": 10,
            }
        )

        for world in WORLD_CONFIGS:
            gap = (
                score_candidate(available, world)["score"]
                - score_candidate(unavailable, world)["score"]
            )
            self.assertGreater(gap, 0.0)
            self.assertLess(gap, 1.1)

    def test_location_change_is_directional_and_bounded(self) -> None:
        local = overlay_record(location_bucket="pune")
        remote = deepcopy(local)
        remote["logistics_overlay"]["location_bucket"] = "outside_india"

        for world in WORLD_CONFIGS:
            gap = (
                score_candidate(local, world)["score"]
                - score_candidate(remote, world)["score"]
            )
            self.assertGreater(gap, 0.0)
            self.assertLess(gap, 0.5)

    def test_services_only_counterfactual_is_penalty_not_disqualification(self) -> None:
        product = overlay_record(
            compounds=["evaluated_ranking_system"],
            signals=["ranking_evaluation", "production_delivery"],
        )
        services_only = deepcopy(product)
        services_only["candidate_overlay_rules"][
            "services_only_entire_career"
        ]["fired"] = True

        for world in WORLD_CONFIGS:
            gap = (
                score_candidate(product, world)["score"]
                - score_candidate(services_only, world)["score"]
            )
            self.assertGreater(gap, 0.0)
            self.assertLess(gap, 1.0)


if __name__ == "__main__":
    unittest.main()
