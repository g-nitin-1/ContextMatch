from solution.jd_parser import spec_from_jd_text
from solution.senior_ordering_experiment import (
    score_with_senior_ordering,
    senior_ordering_modifier,
)
from solution.tests.test_ranker import overlay


def test_senior_ordering_modifier_is_bounded():
    spec = spec_from_jd_text(
        "Senior AI Engineer\n"
        "Hands-on IC role building production retrieval and ranking systems."
    )
    candidate = overlay(
        title="Senior AI Engineer",
        compounds=["end_to_end_intelligence_ownership"],
        signals=[
            "retrieval_search",
            "ranking_recommendation_matching",
            "operational_ownership",
            "zero_to_one_ownership",
        ],
    )

    modifier = senior_ordering_modifier(spec, candidate, cap=0.4)

    assert 0.0 < modifier <= 0.4


def test_senior_ordering_modifier_does_not_lift_non_aligned_candidate():
    spec = spec_from_jd_text(
        "Senior AI Engineer\n"
        "Hands-on IC role building production retrieval and ranking systems."
    )
    candidate = overlay(
        title="AI Engineer",
        signals=["retrieval_search"],
    )

    assert senior_ordering_modifier(spec, candidate, cap=0.4) == 0.0


def test_score_with_senior_ordering_preserves_blocked_candidates():
    spec = spec_from_jd_text(
        "Senior AI Engineer\n"
        "Hands-on IC role building production retrieval and ranking systems."
    )
    blocked = overlay(honeypot_rules=["company_pre_founding"])

    scored = score_with_senior_ordering(spec, blocked, cap=0.4)

    assert scored.blocked
    assert scored.score == -999.0
