from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

from ..db.firebase import FirestoreDB, FirebaseAuth
from ..services.auth import get_current_user, User
from ..utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

router = APIRouter()
firestore_db = FirestoreDB()
firebase_auth = FirebaseAuth()

# User profile model
class UserProfile(BaseModel):
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None
    settings: Dict[str, Any] = {}

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    try:
        logger.info(f"Getting profile for user: {current_user.id}")
        
        # Get user data from database
        user_data = await firestore_db.get_user(current_user.id)
        
        if not user_data:
            # User exists in auth but not in database, create basic profile
            user_data = {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name or "",
                "settings": {}
            }
            await firestore_db.create_user(user_data)
        
        return user_data
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        logger.info(f"Updating profile for user: {current_user.id}")
        
        # Get existing user data
        user_data = await firestore_db.get_user(current_user.id)
        
        if not user_data:
            # User exists in auth but not in database, create basic profile
            user_data = {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name or "",
                "settings": {}
            }
        
        # Update fields that are provided
        update_data = {}
        if profile_data.name is not None:
            update_data["name"] = profile_data.name
        
        if profile_data.avatar_url is not None:
            update_data["avatar_url"] = profile_data.avatar_url
            
        if profile_data.settings is not None:
            update_data["settings"] = profile_data.settings
        
        # Update user in database
        if update_data:
            await firestore_db.update_user(current_user.id, update_data)
            
            # Update the user data with the new values
            user_data.update(update_data)
        
        return user_data
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        ) 