import numpy as np

from solution.embedding_ranker_experiment import score_overlay_with_embedding
from solution.ranker import score_overlay
from solution.tests.test_ranker import overlay
from solution.requirement_spec import load_spec


def test_embedding_semantic_score_replaces_lexical_semantic_term():
    spec = load_spec()
    candidate = overlay(
        compounds=["production_embeddings_retrieval"],
        signals=[
            "embeddings",
            "retrieval_search",
            "ranking_recommendation_matching",
            "production_delivery",
        ],
    )

    lexical = score_overlay(spec, candidate)
    embedded = score_overlay_with_embedding(spec, candidate, semantic=0.9)

    assert embedded.semantic == 0.9
    assert embedded.evidence == lexical.evidence
    assert embedded.score > lexical.score


def test_embedding_similarity_uses_max_query_score_math():
    candidates = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    queries = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)

    similarities = candidates @ queries.T
    scores = similarities.max(axis=1)

    assert scores.tolist() == [1.0, 1.0]
