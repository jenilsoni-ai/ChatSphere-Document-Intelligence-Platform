from fastapi import Depends, HTTPException, status
import logging
from ..db.firebase import FirebaseAuth

logger = logging.getLogger(__name__)
firebase_auth = FirebaseAuth()

async def get_current_user_id(token: str = Depends(firebase_auth.oauth2_scheme)):
    """
    Get current user ID from Firebase authentication token.
    This function is used as a dependency in protected routes.
    """
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing"
            )
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        token_data = await firebase_auth.verify_token(token)
        
        # Extract uid from token data
        if isinstance(token_data, dict):
            user_id = token_data.get('uid')
            if not user_id:
                logger.error("No uid found in token data")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Could not extract user ID"
                )
            return user_id
        
        return token_data
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token. Please log in again."
        ) 