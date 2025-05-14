from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import os

from .config import settings
from ..db.firebase import FirebaseAuth

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str) -> str:
    """Verify token and get current user ID
    
    Args:
        token: JWT token
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        firebase_auth = FirebaseAuth()
        user_id = await firebase_auth.verify_token(token)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(token: Optional[str] = None) -> Optional[str]:
    """Get current user ID if token is provided
    
    Args:
        token: Optional JWT token
        
    Returns:
        User ID or None
    """
    if not token:
        return None
    
    try:
        firebase_auth = FirebaseAuth()
        user_id = await firebase_auth.verify_token(token)
        return user_id
    except Exception:
        return None