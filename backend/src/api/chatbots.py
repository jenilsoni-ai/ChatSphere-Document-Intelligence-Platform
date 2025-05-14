from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
import uuid
from datetime import datetime
import logging
import traceback
from fastapi import UploadFile, File, Form
from pydantic import BaseModel

from ..db.firebase import firestore_db, firebase_auth
from ..models.chatbot import ChatbotCreate, ChatbotResponse, ChatbotUpdate, ChatbotDocumentAssign, ChatbotSettings, ChatMessage, PreviewRequest, PreviewResponse
from ..services.llm import LLMService
from ..services.query_engine import QueryEngine
from ..core.auth import get_current_user_id
from ..services.auth import get_current_user, User
from ..utils.logging import get_logger
from ..core.dependencies import get_chatbot_or_404

# Configure logger
logger = get_logger(__name__)

router = APIRouter()

# Initialize services
llm_service = LLMService()
query_engine = QueryEngine()

# Get current user ID from token
async def get_current_user_id(token: str = Depends(firebase_auth.oauth2_scheme)):
    token_data = await firebase_auth.verify_token(token)
    # Extract uid from token data (which is now a dictionary)
    if isinstance(token_data, dict):
        return token_data.get('uid')
    return token_data

@router.post("/preview", response_model=PreviewResponse)
async def preview_chatbot(
    preview_data: PreviewRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Preview chatbot response"""
    try:
        logger.info(f"Received preview request for chatbot ID: {preview_data.chatbotId}")
        logger.info(f"Preview settings: {preview_data.settings}")
        logger.info(f"Preview message: '{preview_data.message}'")
        logger.info(f"Documents provided: {preview_data.documents}")
        
        # Directly call query_engine.query
        response_text, sources, tokens, rag_status = await query_engine.query(
            query=preview_data.message,
            document_ids=preview_data.documents,
            chatbot_id=preview_data.chatbotId,  # Pass chatbot ID if available
            temperature=preview_data.settings.temperature,
            instructions=preview_data.settings.instructions,
            max_tokens=preview_data.settings.maxTokens,
            model=preview_data.settings.model
        )
        
        logger.info(f"Preview query complete. Response: {response_text[:100]}..., Sources: {len(sources)}, RAG Status: {rag_status}")
        
        return {
            "response": response_text,
            "sources": sources,
            "rag_status": rag_status
        }
        
    except Exception as e:
        logger.error(f"Error in preview endpoint: {str(e)}")
        logger.error(f"Preview error traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.post("", response_model=ChatbotResponse)
async def create_chatbot(
    chatbot: ChatbotCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new chatbot"""
    try:
        # Get the user's actual ID from the token
        user_uid = user_id.get('uid') if isinstance(user_id, dict) else user_id
        logger.info(f"Creating new chatbot for user: {user_uid}")
        logger.info(f"Chatbot data: name='{chatbot.name}', description='{chatbot.description}'")
        logger.info(f"Chatbot settings: {chatbot.settings}")
        logger.info(f"Chatbot documents: {chatbot.documents}")
        
        # Generate unique ID for chatbot
        chatbot_id = str(uuid.uuid4())
        logger.info(f"Generated chatbot ID: {chatbot_id}")
        
        # Create chatbot data
        current_time = datetime.now()
        chatbot_data = {
            "id": chatbot_id,
            "name": chatbot.name,
            "description": chatbot.description,
            "settings": chatbot.settings.dict(),
            "ownerId": user_uid,
            "documents": chatbot.documents,
            "createdAt": current_time,
            "updatedAt": current_time
        }
        
        # Save to Firestore using the FirestoreDB method
        await firestore_db.create_chatbot(chatbot_data)
        logger.info(f"Successfully created chatbot with ID: {chatbot_id}")
        
        # Verify the chatbot was created by retrieving it
        created_chatbot = await firestore_db.get_chatbot(chatbot_id)
        if not created_chatbot:
            logger.error(f"Chatbot was not found after creation: {chatbot_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chatbot created but could not be retrieved. Please try again."
            )
        
        logger.info(f"Verified chatbot was successfully persisted: {chatbot_id}")
        return ChatbotResponse(**created_chatbot)
    except Exception as e:
        logger.error(f"Failed to create chatbot: {str(e)}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chatbot: {str(e)}"
        )

@router.get("", response_model=List[ChatbotResponse])
async def list_chatbots(user_id: str = Depends(get_current_user_id)):
    """List all chatbots for the current user"""
    try:
        # Get the user's actual ID from the token
        user_uid = user_id.get('uid') if isinstance(user_id, dict) else user_id
        
        chatbots = await firestore_db.list_chatbots(user_uid)
        
        return chatbots
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list chatbots: {str(e)}"
        )

@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get chatbot details"""
    try:
        logger.info(f"Fetching chatbot with ID: {chatbot_id}")
        
        # Get the user's actual ID from the token
        user_uid = user_id.get('uid') if isinstance(user_id, dict) else user_id
        logger.info(f"User ID: {user_uid}")
        
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        if not chatbot:
            logger.warning(f"Chatbot not found: {chatbot_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Check if user owns the chatbot
        chatbot_owner = chatbot.get("ownerId")
        logger.info(f"Chatbot owner: {chatbot_owner}, requesting user: {user_uid}")
        
        if chatbot_owner != user_uid:
            logger.warning(f"Unauthorized access attempt: User {user_uid} tried to access chatbot {chatbot_id} owned by {chatbot_owner}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chatbot"
            )
        
        logger.info(f"Successfully retrieved chatbot {chatbot_id}")
        return ChatbotResponse(**chatbot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get chatbot: {str(e)}"
        )

@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: str,
    chatbot_update: ChatbotUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Update an existing chatbot.
    Requires authentication. Only the chatbot's owner can update it.
    """
    try:
        # Extract uid from user_id (which could be a dict or string)
        user_uid = user_id.get('uid') if isinstance(user_id, dict) else user_id
        
        logger.info(f"Attempting to update chatbot {chatbot_id} by user {user_uid}")
        logger.info(f"Update data: {chatbot_update.dict()}")
        
        # Get the chatbot
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        if not chatbot:
            logger.error(f"Chatbot {chatbot_id} not found")
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        chatbot_owner = chatbot.get("ownerId")
        
        # Check if the current user is the owner
        if chatbot_owner != user_uid:
            logger.error(f"Unauthorized update attempt: User {user_uid} is not the owner of chatbot {chatbot_id} (owner is {chatbot_owner})")
            raise HTTPException(status_code=403, detail="Not authorized to update this chatbot")
        
        # Prepare update data
        update_data = {}
        
        if chatbot_update.name is not None:
            update_data["name"] = chatbot_update.name
        
        if chatbot_update.description is not None:
            update_data["description"] = chatbot_update.description
        
        if chatbot_update.settings is not None:
            update_data["settings"] = chatbot_update.settings.dict(exclude_unset=True)
        
        # Update timestamp
        update_data["updatedAt"] = datetime.now().isoformat()
        
        # Update document in Firestore
        await firestore_db.update_chatbot(chatbot_id, update_data)
        logger.info(f"Chatbot {chatbot_id} updated successfully")
        
        # Get updated chatbot
        updated_chatbot = await firestore_db.get_chatbot(chatbot_id)
        return ChatbotResponse(**updated_chatbot)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error updating chatbot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update chatbot: {str(e)}")

@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(chatbot_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a chatbot"""
    try:
        # Get chatbot to check ownership
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Check if user owns the chatbot
        if chatbot.get("ownerId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this chatbot"
            )
            
        logger.info(f"Starting deletion process for chatbot {chatbot_id}")
        
        # Delete all chat sessions associated with this chatbot
        try:
            logger.info(f"Deleting chat sessions for chatbot {chatbot_id}")
            sessions = await firestore_db.list_chat_sessions_by_chatbot(chatbot_id)
            for session in sessions:
                await firestore_db.delete_chat_session(session["id"])
            logger.info(f"Deleted {len(sessions)} chat sessions")
        except Exception as e:
            logger.error(f"Error deleting chat sessions: {str(e)}")
            # Continue with deletion even if session cleanup fails
        
        # Note: We don't delete the actual documents as they might be used by other chatbots
        # We only remove the references to them from this chatbot
        
        # Delete chatbot from Firestore
        logger.info(f"Deleting chatbot metadata from Firestore")
        await firestore_db.delete_chatbot(chatbot_id)
        
        logger.info(f"Chatbot {chatbot_id} deleted successfully")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chatbot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete chatbot: {str(e)}"
        )

@router.post("/{chatbot_id}/documents", response_model=ChatbotResponse)
async def assign_documents(chatbot_id: str, document_data: ChatbotDocumentAssign, user_id: str = Depends(get_current_user_id)):
    """Assign documents to a chatbot"""
    try:
        # Get chatbot to check ownership
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Check if user owns the chatbot
        if chatbot.get("ownerId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this chatbot"
            )
        
        # Verify all documents exist and are owned by the user
        for doc_id in document_data.documentIds:
            document = await firestore_db.get_document(doc_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {doc_id} not found"
                )
            if document.get("ownerId") != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to use document {doc_id}"
                )
        
        # Update chatbot documents
        current_docs = chatbot.get("documents", [])
        new_docs = list(set(current_docs + document_data.documentIds))
        
        update_data = {
            "documents": new_docs,
            "updatedAt": datetime.now()
        }
        
        # Update chatbot in Firestore
        await firestore_db.update_chatbot(chatbot_id, update_data)
        
        # Get updated chatbot
        updated_chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        return ChatbotResponse(**updated_chatbot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign documents: {str(e)}"
        )

@router.delete("/{chatbot_id}/documents/{document_id}", response_model=ChatbotResponse)
async def remove_document(chatbot_id: str, document_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove a document from a chatbot"""
    try:
        # Get chatbot to check ownership
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Check if user owns the chatbot
        if chatbot.get("ownerId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this chatbot"
            )
        
        # Update chatbot documents
        current_docs = chatbot.get("documents", [])
        if document_id not in current_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not assigned to this chatbot"
            )
        
        new_docs = [doc for doc in current_docs if doc != document_id]
        
        update_data = {
            "documents": new_docs,
            "updatedAt": datetime.now()
        }
        
        # Update chatbot in Firestore
        await firestore_db.update_chatbot(chatbot_id, update_data)
        
        # Get updated chatbot
        updated_chatbot = await firestore_db.get_chatbot(chatbot_id)
        
        return ChatbotResponse(**updated_chatbot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to remove document: {str(e)}"
        )

@router.get("/widget-config/{chatbot_id}")
async def get_widget_config(chatbot_id: str):
    """
    Get widget configuration for a chatbot (no authentication required)
    """
    logger.info(f"Widget config requested for chatbot: {chatbot_id}")
    
    try:
        # Get the chatbot from database
        chatbot = await get_chatbot_or_404(chatbot_id)
        
        # Extract widget-specific settings
        settings = chatbot.get("settings", {})
        appearance = settings.get("appearance", {})
        
        # Return widget configuration with proper structure
        return {
            "settings": {
                "appearance": {
                    "position": appearance.get("widgetPosition", "bottom-right"),
                    "primaryColor": appearance.get("primaryColor", "#6366f1"),
                    "secondaryColor": appearance.get("secondaryColor", "#4f46e5"),
                    "chatTitle": chatbot.get("name", "Chat Assistant"),
                    "showBranding": appearance.get("showBranding", True),
                    "initialMessage": settings.get("welcomeMessage", "Hi! How can I help you today?")
                }
            },
            "name": chatbot.get("name", "Chat Assistant"),
            "description": chatbot.get("description", "")
        }
    
    except Exception as e:
        logger.error(f"Error getting widget config: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting widget configuration: {str(e)}")

# Utility function to get a chatbot or raise 404
async def get_chatbot_or_404(chatbot_id: str):
    """Get a chatbot or raise a 404 error if not found"""
    from ..db.firebase import FirestoreDB
    
    try:
        # Get database reference
        firestore_db = FirestoreDB()
        
        # Get the chatbot from Firebase
        chatbot_ref = firestore_db.db.collection("chatbots").document(chatbot_id)
        chatbot_doc = chatbot_ref.get()
        
        if not chatbot_doc.exists:
            logger.warning(f"Chatbot not found: {chatbot_id}")
            raise HTTPException(status_code=404, detail="Chatbot not found")
            
        # Return chatbot data
        return chatbot_doc.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chatbot: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot: {str(e)}")