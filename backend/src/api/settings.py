from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import traceback

from ..services.auth import get_current_user, User
from ..db.firebase import FirestoreDB
from ..utils.logging import get_logger
from src.api.endpoints.settings import router as vector_store_router

# Get logger
logger = get_logger(__name__)

router = APIRouter()
firestore_db = FirestoreDB()

# Include vector store settings router
router.include_router(vector_store_router, prefix="/vector-store", tags=["vector-store"])

@router.get("/")
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get the settings for the current user"""
    try:
        # Get user settings from database
        settings = await firestore_db.get_user_settings(current_user.id)
        
        # If settings don't exist, create default settings
        if not settings:
            default_settings = {
                "userId": current_user.id,
                "email": current_user.email,
                "displayName": current_user.display_name,
                "theme": "light",
                "notifications": {
                    "email": True,
                    "inApp": True
                },
                "apiKey": str(uuid.uuid4()),
                "usage": {
                    "messagesUsed": 0,
                    "documentsUploaded": 0,
                    "storageUsed": 0
                },
                "subscription": {
                    "plan": "free"
                },
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            # Create settings in database
            await firestore_db.create_user_settings(default_settings)
            return default_settings
        
        return settings
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )

@router.put("/")
async def update_user_settings(
    settings_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update the settings for the current user"""
    try:
        # Get current settings
        current_settings = await firestore_db.get_user_settings(current_user.id)
        
        # Validate that we're not updating protected fields
        protected_fields = {"userId", "apiKey", "createdAt", "subscription", "usage"}
        for field in protected_fields:
            if field in settings_data:
                settings_data.pop(field)
        
        # If settings don't exist, create default settings first
        if not current_settings:
            default_settings = {
                "userId": current_user.id,
                "email": current_user.email,
                "displayName": current_user.display_name,
                "theme": "light",
                "notifications": {
                    "email": True,
                    "inApp": True
                },
                "apiKey": str(uuid.uuid4()),
                "usage": {
                    "messagesUsed": 0,
                    "documentsUploaded": 0,
                    "storageUsed": 0
                },
                "subscription": {
                    "plan": "free"
                },
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            await firestore_db.create_user_settings(default_settings)
            current_settings = default_settings
        
        # Update settings
        update_data = {
            **settings_data,
            "updatedAt": datetime.now()
        }
        
        await firestore_db.update_user_settings(current_user.id, update_data)
        
        # Get updated settings
        updated_settings = await firestore_db.get_user_settings(current_user.id)
        
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating user settings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )

@router.post("/regenerate-api-key")
async def regenerate_api_key(current_user: User = Depends(get_current_user)):
    """Regenerate the API key for the current user"""
    try:
        # Generate a new API key
        new_api_key = str(uuid.uuid4())
        
        # Update the user settings with the new API key
        update_data = {
            "apiKey": new_api_key,
            "updatedAt": datetime.now()
        }
        
        # Update settings in database
        await firestore_db.update_user_settings(current_user.id, update_data)
        
        return {"apiKey": new_api_key}
    except Exception as e:
        logger.error(f"Error regenerating API key: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate API key: {str(e)}"
        ) 