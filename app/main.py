import logging
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel, constr
from slowapi.errors import RateLimitExceeded

from app.chatbot.chat_service import generate_answer
from app.config.security import limiter, _rate_limit_exceeded_handler, get_api_key

logger = logging.getLogger(__name__)

app = FastAPI(title="ChatbotMP API", description="Production-ready RAG API")

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class ChatRequest(BaseModel):
    query: constr(min_length=1, max_length=1000) # Input validation limits prompt size
    userId: str | None = None
    spaceId: str | None = None

@app.post("/chat", dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute") # Strict but fair API limit
def chat(request: Request, chat_req: ChatRequest):
    try:
        logger.info(f"Processing query: '{chat_req.query[:50]}...' (user_id: {chat_req.userId}, space_id: {chat_req.spaceId})")
        
        answer = generate_answer(chat_req.query, user_id=chat_req.userId, space_id=chat_req.spaceId)
        
        if not answer:
            raise HTTPException(status_code=500, detail="Failed to generate answer")
            
        return {"answer": answer}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing your request")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "chatbot-api"}

@app.get("/")
def home():
    return {
        "message": "Chatbot API is running!",
        "endpoints": {
            "chat": "POST /chat - Chat with the bot",
            "health": "GET /health - Health check"
        }
    }