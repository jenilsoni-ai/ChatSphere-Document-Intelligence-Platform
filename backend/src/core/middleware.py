from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[Tuple[str, str], list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP and endpoint path
        client_ip = request.client.host
        path = request.url.path
        key = (client_ip, path)
        
        # Get current timestamp
        now = time.time()
        
        # Initialize or clean up old requests
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key] = [ts for ts in self.requests[key] if ts > now - 60]
        
        # Check rate limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": "60 seconds"
                }
            )
        
        # Add current request timestamp
        self.requests[key].append(now)
        
        # Process the request
        response = await call_next(request)
        return response

def setup_middleware(app: FastAPI):
    """Setup middleware for the FastAPI application"""
    app.add_middleware(RateLimitMiddleware)