from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import logging
import firebase_admin
from firebase_admin import auth, credentials
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin if not already done
try:
    if not firebase_admin._apps:
        # If using a service account file
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized with service account")
        else:
            # Initialize without credentials (for Firebase emulator or using env vars)
            firebase_admin.initialize_app()
            logger.info("Firebase Admin initialized without credentials")
    else:
        logger.info("Firebase Admin already initialized")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin: {e}")
    # Initialize a dummy app for development if Firebase fails
    class DummyApp:
        name = "dummy-app"
    firebase_admin._apps = {"[DEFAULT]": DummyApp()}
    logger.warning("Using dummy Firebase app for development")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

class User(BaseModel):
    """User model for authentication"""
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    disabled: Optional[bool] = None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the token.
    This function is used as a dependency in protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the token with Firebase
        decoded_token = auth.verify_id_token(token, check_revoked=True, clock_skew_seconds=60)
        user_id = decoded_token.get("uid")
        
        if user_id is None:
            raise credentials_exception
        
        # Get user info
        user_record = auth.get_user(user_id)
        
        return User(
            id=user_id,
            email=user_record.email,
            display_name=user_record.display_name,
            disabled=user_record.disabled
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception

# For development/testing without Firebase
def get_test_user() -> User:
    """Get a test user for development without Firebase"""
    return User(
        id="test-user-id",
        email="test@example.com",
        display_name="Test User",
        disabled=False
    ) 