import logging
from sentence_transformers import SentenceTransformer

_model = None
logger = logging.getLogger(__name__)


def get_embedding_model(model_name='all-MiniLM-L6-v2'):
    global _model
    if _model is None:
        try:
            logger.info(f"Loading embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise
    return _model


def embed_texts(texts):
    """Create embeddings locally (sentence-transformers). No network API calls after first model download."""
    try:
        if not texts or not any(texts):
            logger.warning("No texts provided for embedding")
            return []
        
        model = get_embedding_model()
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        logger.info(f"Successfully embedded {len(texts)} texts")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to embed texts: {e}")
        raise
