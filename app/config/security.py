import os
from fastapi import Request, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Simple API Key setup
API_KEY = os.getenv("API_KEY", "default-dev-key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        # Default allow list behavior for dev
        if os.getenv("FLASK_ENV") == "production":
            raise HTTPException(status_code=403, detail="Could not validate API KEY")
        else:
            return API_KEY
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403, detail="Could not validate API KEY"
        )

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)
