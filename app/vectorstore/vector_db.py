import logging
import os
from pinecone import Pinecone

logger = logging.getLogger(__name__)

_pc = None
_index = None

def get_client():
    global _pc
    if _pc is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            logger.error("PINECONE_API_KEY is not set in environment!")
            raise RuntimeError("PINECONE_API_KEY is missing from .env")
        try:
            _pc = Pinecone(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise
    return _pc

def get_collection(name='braincache'):
    global _index
    if _index is None:
        try:
            client = get_client()
            _index = client.Index(name)
            logger.info(f"Connected to Pinecone Index: {name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index {name}. Ensure it exists on the dashboard! Error: {e}")
            raise
    return _index

def upsert_documents(ids, texts, embeddings, metadatas=None):
    try:
        collection = get_collection()
        vectors = []
        for i in range(len(ids)):
            meta = metadatas[i] if (metadatas and i < len(metadatas)) else {}
            # Pinecone requires textual data to be stored inside metadata
            meta['text'] = texts[i]
            vectors.append({
                "id": str(ids[i]),
                "values": [float(v) for v in embeddings[i]],
                "metadata": meta
            })
        
        # Pinecone upsert limit is ~100 vectors per request for free tier stability
        for i in range(0, len(vectors), 100):
            collection.upsert(vectors=vectors[i:i+100])
            
        logger.info(f"Successfully upserted {len(ids)} documents to Pinecone")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert documents to Pinecone: {e}")
        raise

def query(embedding, n_results=15, where=None):
    try:
        collection = get_collection()
        
        # Translate Chroma 'where' clauses to Pinecone 'filter' syntax if needed
        # Lucky for us, simple equality filters are basically identical!
        filter_dict = where if where else None
        
        # Top_k limits how many matches we return
        res = collection.query(
            vector=[float(v) for v in embedding], 
            top_k=n_results, 
            include_metadata=True, 
            filter=filter_dict
        )
        
        # We must physically restructure Pinecone's Dict into ChromaDB's Array structure!
        # Because we don't want to break app.chatbot.chat_service.py logic!
        documents = [[]]
        metadatas = [[]]
        
        for match in res.get('matches', []):
            meta = match.get('metadata', {})
            # Safe text retrieval
            text_string = meta.get('text', '')
            
            documents[0].append(text_string)
            metadatas[0].append(meta)
            
        if not documents[0]:
            logger.info(f"No documents found for query with filters: {filter_dict}")
            
        return {'documents': documents, 'metadatas': metadatas}
        
    except Exception as e:
        logger.error(f"Failed to query Pinecone: {e}")
        raise
