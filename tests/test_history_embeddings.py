"""Embedding checks — fully local (fastembed/ONNX), no network, no database.

Downloads the ~130MB model on first run (cached by huggingface_hub
afterwards); marked slow so it's easy to skip in a tight inner loop with
`pytest -m "not slow"` if that ever matters.
"""
import numpy as np
import pytest

from policy_orchestrator.history.embeddings import embed

pytestmark = pytest.mark.slow


def cosine(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_embedding_has_expected_dimension():
    vector = embed("What position should the MP take on AI regulation?")
    assert len(vector) == 384


def test_embedding_is_deterministic():
    text = "Should the office back a startup tax incentive package?"
    assert embed(text) == embed(text)


def test_paraphrased_question_scores_above_similarity_threshold():
    from policy_orchestrator.settings import SIMILARITY_THRESHOLD

    original = "What position should the MP take on regulating high-risk AI systems in India?"
    paraphrase = "What should our stance be on high-risk AI regulation in the country?"
    assert cosine(embed(original), embed(paraphrase)) > SIMILARITY_THRESHOLD


def test_unrelated_question_scores_below_similarity_threshold():
    from policy_orchestrator.settings import SIMILARITY_THRESHOLD

    a = "What position should the MP take on regulating high-risk AI systems in India?"
    b = "Should the office back a startup-friendly tax incentive package for Bengaluru's tech sector?"
    assert cosine(embed(a), embed(b)) < SIMILARITY_THRESHOLD
