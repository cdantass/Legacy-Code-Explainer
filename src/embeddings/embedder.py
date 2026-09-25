#Geração de embeddings usando sentence-transformers. Modelo carregado uma única vez (singleton) para evitar overhead.
from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Gera embeddings para uma lista de textos."""
    model = get_model()
    # all-MiniLM-L6-v2 tem limite de contexto pequeno (~256 tokens),
    # então truncamos textos muito grandes para evitar perda de qualidade.
    truncated = [t[:2000] for t in texts]
    embeddings = model.encode(truncated, convert_to_numpy=True)
    return embeddings.tolist()