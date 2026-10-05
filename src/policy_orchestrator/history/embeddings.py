"""Local, free text embeddings for semantic "have we asked this before?" search.

Uses fastembed (ONNX runtime under the hood) rather than sentence-transformers
specifically to avoid a torch/CUDA dependency — this runs on CPU, downloads
its ~130MB model once (cached under the user's home directory by
huggingface_hub), and costs nothing per call. No API key, no network
dependency after the first run.

The model is loaded lazily and cached at module scope — constructing
TextEmbedding is the expensive part (ONNX session init), calling .embed()
repeatedly on the same instance is cheap.
"""
from functools import lru_cache

from policy_orchestrator.settings import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=EMBEDDING_MODEL_NAME)


def embed(text: str) -> list[float]:
    """Return a single normalized embedding vector for `text`.

    fastembed's bge-* models already L2-normalize their output, so cosine
    similarity and dot product are equivalent here — pgvector's `<=>`
    (cosine distance) operator is used at the SQL layer regardless, so this
    doesn't have to be relied on, but it's worth knowing when reading query
    results.
    """
    (vector,) = _model().embed([text])
    return vector.tolist()
