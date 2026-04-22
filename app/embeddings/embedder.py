import logging
import os
import requests
import time

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
_model = None

def get_hf_token():
    return os.getenv("HF_TOKEN")

def embed_query_cloud(text):
    """
    Use Hugging Face Inference API to embed a single query.
    This saves 500MB of RAM on Render.
    """
    token = get_hf_token()
    if not token:
        logger.error("HF_TOKEN missing! Cannot use cloud embeddings.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": [text]}
    
    try:
        # Retry logic for the model "waking up" on Hugging Face
        for _ in range(3):
            response = requests.post(HF_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()[0]
            elif response.status_code == 503: # Model loading
                logger.info("Hugging Face model is waking up, waiting 5s...")
                time.sleep(5)
                continue
            else:
                logger.error(f"HF API Error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Cloud embedding request failed: {e}")
        return None

def embed_texts(texts):
    """
    Local embedding for heavy-duty sync tasks. 
    NOTE: Import is INSIDE to prevent Render from crashing on startup.
    """
    global _model
    try:
        if not texts or not any(texts):
            return []
        
        # We only import and load the heavy model if this specific function is called.
        # Render will NEVER call this, so it stays safe under 512MB RAM!
        if _model is None:
            logger.info("Loading heavy local embedding model (Local Only)...")
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            
        embeddings = _model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        logger.info(f"Successfully embedded {len(texts)} texts locally")
        return embeddings
    except Exception as e:
        logger.error(f"Local embedding failed: {e}")
        raise
