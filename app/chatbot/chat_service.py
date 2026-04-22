import logging
import os
from groq import Groq

from app.embeddings.embedder import embed_texts
from app.vectorstore.vector_db import get_collection
from app.vectorstore.vector_db import query
from app.vectorstore.vector_db import upsert_documents
from sentence_transformers import CrossEncoder
from app.config.observability import time_it
from app.processing.chunker import chunk_text

logger = logging.getLogger(__name__)

_cross_encoder = None
_groq_client = None

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            logger.info("Loading Cross-Encoder model...")
            _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512, device='cpu')
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            raise
    return _cross_encoder

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY environment variable is not set. API calls will fail.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client

@time_it("Retrieve and Re-rank Context")
def _get_relevant_context(query_text, user_id=None, space_id=None, top_k=2):
    try:
        embedding = embed_texts([query_text])[0]
        where_clause = {}
        if user_id:
            where_clause['userId'] = user_id
        if space_id:
            where_clause['spaceId'] = space_id

        # Broad search to retrieve 15 results
        response = query(embedding, n_results=15, where=where_clause or None)
        docs = []
        doc_lists = response.get('documents', [])
        meta_lists = response.get('metadatas', [])
        
        for i in range(len(doc_lists)):
            for doc, meta in zip(doc_lists[i], meta_lists[i]):
                title = meta.get('title', 'Unknown Source')
                space_id = meta.get('spaceId', 'Unknown Space')
                space_name = meta.get('spaceName', space_id)
                author_id = meta.get('userId', 'Unknown User')
                author_name = meta.get('userName', author_id)
                # Inject human-readable metadata into the text chunk so the LLM knows the author/space naturally
                docs.append(f"[Source: {title}, Space: {space_name}, Author: {author_name}]\n{doc}")

        if not docs:
            return None

        # Re-Ranking Phase
        cross_encoder = get_cross_encoder()
        pairs = [[query_text, doc] for doc in docs]
        scores = cross_encoder.predict(pairs)

        # Sort documents by score in descending order
        scored_docs = list(zip(scores, docs))
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Select top_k docs based on reranker
        best_docs = [doc for score, doc in scored_docs[:top_k]]

        return ' \n'.join(best_docs)
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return None

@time_it("LLM Generation (Groq)")
def generate_answer(query_text, user_id=None, space_id=None):
    try:
        context = _get_relevant_context(query_text, user_id=user_id, space_id=space_id)
        
        if context is None:
            return "Sorry, I encountered an error while searching for content. Please try again."
        
        if not context.strip():
            if user_id and space_id:
                return "I couldn't find any content in the specified space for this user. Try searching across all spaces or check if the space has content."
            elif user_id:
                return "I couldn't find any content for this user. Try searching across all spaces."
            elif space_id:
                return "I couldn't find any content in the specified space. Try searching across all spaces or check if the space has content."
            else:
                return "I couldn't find any relevant content in your spaces."

        # Safety override - Groq handles large contexts easily, but this keeps costs/latency down
        if len(context) > 6000:
            context = context[:6000] + "... [truncated for length]"

        # Groq Llama3 format
        system_prompt = (
            "You are a strict, helpful AI assistant. Use the following context to answer the user's question.\n"
            "CRITICAL RULE: If the answer is not explicitly contained in the context provided below, you MUST reply exactly with: \"I do not have enough information to answer that question.\"\n"
            "However, if the user is just saying hello or asking your name, you may respond normally to those conversational inputs.\n\n"
            f"Context:\n{context}\n"
        )

        client = get_groq_client()
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": query_text,
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=500,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating answer with Groq: {e}")
            return "Sorry, I encountered an error while communicating with the cloud engine. Please check your GROQ_API_KEY."

    except Exception as e:
        logger.error(f"Error in generate_answer: {e}")
        return "Sorry, I encountered an unexpected error. Please try again."

def update_vector_db(processed_records):
    """Embed locally and upsert into Chroma."""
    try:
        texts = []
        ids = []
        metadatas = []
        for record in processed_records:
            if not record.get('contentText'):
                continue
                
            raw_text = record['contentText']
            chunks = chunk_text(raw_text, chunk_size=400, overlap=50)
            
            for i, chunk in enumerate(chunks):
                text = chunk
                user_id = record.get('userId')
                space_id = record.get('spaceId')
                doc_id = f"{record.get('contentId')}_{i}"
                ids.append(doc_id)
                texts.append(text)
                # Chroma metadata must be str / int / float / bool — never None
                metadatas.append({
                    'userId': '' if user_id is None else str(user_id),
                    'userName': '' if record.get('userName') is None else str(record.get('userName')),
                    'spaceId': '' if space_id is None else str(space_id),
                    'spaceName': '' if record.get('spaceName') is None else str(record.get('spaceName')),
                    'title': '' if record.get('title') is None else str(record.get('title')),
                })

        if texts:
            embeddings = embed_texts(texts)
            get_collection()
            upsert_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
            logger.info(f"Successfully upserted {len(texts)} documents to vector DB")
        else:
            logger.warning("No valid content found to update vector DB")
    except Exception as e:
        logger.error(f"Error updating vector DB: {e}")
        raise
