from solution.jd_parser import spec_from_jd_text
from solution.role_title_ordering_experiment import (
    role_title_alignment_score,
    role_title_ordering_modifier,
    score_with_role_title_ordering,
)
from solution.tests.test_ranker import overlay


def senior_ai_spec():
    return spec_from_jd_text(
        "Senior AI Engineer\n"
        "Hands-on IC role building production retrieval and ranking systems."
    )


def test_role_title_alignment_prefers_matching_ai_engineering_title():
    assert role_title_alignment_score("Senior AI Engineer", "Senior AI Engineer") == 1.0
    assert role_title_alignment_score(
        "Senior AI Engineer",
        "Senior AI Engineer",
    ) > role_title_alignment_score("Senior AI Engineer", "Senior Data Scientist")


def test_role_title_ordering_modifier_is_bounded_and_evidence_based():
    spec = senior_ai_spec()
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

    modifier = role_title_ordering_modifier(spec, candidate, cap=0.4)

    assert 0.0 < modifier <= 0.4


def test_role_title_ordering_modifier_requires_explicit_senior_title_for_senior_jd():
    spec = senior_ai_spec()
    candidate = overlay(
        title="Applied ML Engineer",
        compounds=["end_to_end_intelligence_ownership"],
        signals=[
            "retrieval_search",
            "ranking_recommendation_matching",
            "operational_ownership",
            "zero_to_one_ownership",
        ],
    )

    assert role_title_ordering_modifier(spec, candidate, cap=0.4) == 0.0


def test_role_title_ordering_preserves_blocked_candidates():
    spec = senior_ai_spec()
    blocked = overlay(honeypot_rules=["company_pre_founding"])

    scored, modifier = score_with_role_title_ordering(spec, blocked, cap=0.4)

    assert modifier == 0.0
    assert scored.blocked
    assert scored.score == -999.0
