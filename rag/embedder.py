import logging
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency at dev time
    SentenceTransformer = None  # type: ignore[assignment]


_MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDER = None


def get_embedder():
    """
    Lazily create and return a singleton SentenceTransformer encoder.

    The model is kept in memory for the lifetime of the process to avoid
    repeatedly loading it on the Raspberry Pi 5.
    """
    global _EMBEDDER

    if _EMBEDDER is not None:
        return _EMBEDDER

    log = logging.getLogger("rag.embedder")

    if SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Install it to enable RAG."
        )

    try:
        # CPU‑only model; small footprint for Pi 5.
        _EMBEDDER = SentenceTransformer(_MODEL_NAME, device="cpu")
        log.info("Loaded embedding model %s", _MODEL_NAME)
    except Exception as exc:  # pragma: no cover - runtime/hardware specific
        log.exception("Failed to load embedding model: %s", exc)
        raise

    return _EMBEDDER


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Encode a list of strings into dense vectors.

    We always convert to plain Python floats so that downstream consumers
    (ChromaDB) receive a simple `List[List[float]]` structure.
    """
    model = get_embedder()
    vectors = model.encode(texts, batch_size=16, convert_to_numpy=True)

    # `vectors` is a numpy array; convert each row to a plain list[float].
    return [ [float(x) for x in row] for row in vectors ]

