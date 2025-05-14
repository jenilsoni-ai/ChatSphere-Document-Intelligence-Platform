from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
import logging

from .config import settings
from .security import get_current_user, get_optional_user
from ..db.firebase import FirebaseAuth, FirestoreDB, firestore_db

logger = logging.getLogger(__name__)

# Initialize Firebase Auth
firebase_auth = FirebaseAuth()
firestore_db = FirestoreDB()

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token
    
    Args:
        token: JWT token from OAuth2 scheme
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid
    """
    return await get_current_user(token)

async def get_optional_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Get optional user ID from token
    
    Args:
        token: Optional JWT token from OAuth2 scheme
        
    Returns:
        User ID or None
    """
    return await get_optional_user(token)

async def validate_document_owner(document_id: str, user_id: str) -> bool:
    """Validate that the user owns the document
    
    Args:
        document_id: Document ID
        user_id: User ID
        
    Returns:
        True if user owns the document
        
    Raises:
        HTTPException: If document not found or user does not own the document
    """
    document = await firestore_db.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.get("ownerId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    return True

async def validate_chatbot_owner(chatbot_id: str, user_id: str) -> bool:
    """Validate that the user owns the chatbot
    
    Args:
        chatbot_id: Chatbot ID
        user_id: User ID
        
    Returns:
        True if user owns the chatbot
        
    Raises:
        HTTPException: If chatbot not found or user does not own the chatbot
    """
    chatbot = await firestore_db.get_chatbot(chatbot_id)
    
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    
    if chatbot.get("ownerId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chatbot"
        )
    
    return True

async def validate_chat_session_owner(session_id: str, user_id: str) -> bool:
    """Validate that the user owns the chat session
    
    Args:
        session_id: Chat session ID
        user_id: User ID
        
    Returns:
        True if user owns the chat session
        
    Raises:
        HTTPException: If chat session not found or user does not own the chat session
    """
    session = await firestore_db.get_chat_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    if session.get("userId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat session"
        )
    
    return True

async def get_chatbot_or_404(chatbot_id: str) -> Dict[str, Any]:
    """Get a chatbot by ID or raise 404"""
    chatbot = await firestore_db.get_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chatbot {chatbot_id} not found"
        )
    return chatbot

async def get_document_or_404(document_id: str) -> Dict[str, Any]:
    """Get a document by ID or raise 404"""
    document = await firestore_db.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document

async def get_chat_session_or_404(session_id: str) -> Dict[str, Any]:
    """Get a chat session by ID or raise 404"""
    session = await firestore_db.get_chat_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found"
        )
    return session