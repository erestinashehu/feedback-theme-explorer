import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

_model = SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    vector = _model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    vectors = _model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a)
    b_arr = np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)