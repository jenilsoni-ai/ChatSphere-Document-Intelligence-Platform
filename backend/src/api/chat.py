from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime
import logging
import traceback
import json

from ..db.firebase import FirestoreDB, FirebaseAuth
from ..models.chat import ChatSessionCreate, ChatSessionResponse, MessageCreate, MessageResponse, ChatSession, ChatMessage, SavedSession
from ..services.query_engine import QueryEngine
from ..services.auth import get_current_user, User
from ..utils.logging import get_logger
from pydantic import BaseModel
from ..core.dependencies import get_chatbot_or_404

# Configure logger
logger = get_logger(__name__)

router = APIRouter()
firestore_db = FirestoreDB()
firebase_auth = FirebaseAuth()
query_engine = QueryEngine()

# Get current user ID from token
async def get_current_user_id(token: str = Depends(firebase_auth.oauth2_scheme)):
    return await firebase_auth.verify_token(token)

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(session_data: ChatSessionCreate, user_id: str = Depends(get_current_user_id)):
    """Create a new chat session"""
    try:
        # Check if chatbot exists and user has access
        chatbot = await firestore_db.get_chatbot(session_data.chatbotId)
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Generate unique ID for chat session
        session_id = str(uuid.uuid4())
        
        # Create chat session in Firestore
        session_dict = {
            "id": session_id,
            "chatbotId": session_data.chatbotId,
            "userId": user_id,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "messages": []
        }
        
        await firestore_db.create_chat_session(session_dict)
        
        return session_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create chat session: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(user_id: str = Depends(get_current_user_id)):
    """List all chat sessions for the current user"""
    try:
        sessions = await firestore_db.list_chat_sessions(user_id)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list chat sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get chat session details"""
    try:
        session = await firestore_db.get_chat_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user owns the chat session
        if session.get("userId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chat session"
            )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get chat session: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, message_data: MessageCreate, user_id: str = Depends(get_current_user_id)):
    """Send a message in a chat session"""
    try:
        # Check if chat session exists and belongs to user
        chat_session = await firestore_db.get_chat_session(session_id)
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        if chat_session.get('userId') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this chat session"
            )
        
        # Get chatbot ID from chat session
        chatbot_id = chat_session.get('chatbotId')
        if not chatbot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat session has no associated chatbot"
            )
        
        # Get chatbot
        chatbot = await firestore_db.get_chatbot(chatbot_id)
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Extract chatbot settings
        settings = chatbot.get('settings', {})
        temperature = settings.get('temperature', 0.7)
        max_tokens = settings.get('maxTokens', 1024)
        model = settings.get('model', 'llama3-70b-8192')
        instructions = settings.get('instructions', '')
        
        # Get documents associated with chatbot
        document_ids = chatbot.get('documents', [])
        
        # Get chat messages
        messages = chat_session.get('messages', [])
        
        # Add user message to chat session
        user_message = {
            "role": "user",
            "content": message_data.content,
            "timestamp": datetime.now()
        }
        
        messages.append(user_message)
        
        # Initialize query engine
        query_engine = QueryEngine()
        
        # Generate response using query engine
        response_text, sources, tokens, rag_status = await query_engine.query(
            query=message_data.content,
            document_ids=document_ids,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            instructions=instructions
        )
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(),
            "metadata": {
                "temperature": temperature,
                "tokens": tokens,
                "sources": sources,
                "rag_status": rag_status
            }
        }
        
        # Add assistant message to chat session
        messages.append(assistant_message)
        
        # Update chat session with assistant message
        await firestore_db.update_chat_session(session_id, {
            "messages": messages,
            "updatedAt": datetime.now()
        })
        
        return assistant_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_chat_history(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get chat history for a session"""
    try:
        # Get chat session
        session = await firestore_db.get_chat_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user owns the chat session
        if session.get("userId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chat session"
            )
        
        # Return messages
        return session.get("messages", [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get chat history: {str(e)}"
        )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a chat session"""
    try:
        # Get chat session
        session = await firestore_db.get_chat_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user owns the chat session
        if session.get("userId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this chat session"
            )
        
        # Delete chat session
        await firestore_db.delete_chat_session(session_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete chat session: {str(e)}"
        )

@router.post("/widget/{chatbot_id}")
async def chat_with_widget(chatbot_id: str, request_data: dict):
    """
    Chat with a chatbot through the website widget (no authentication required)
    """
    logger.info(f"Widget chat request for chatbot: {chatbot_id}")
    logger.info(f"Request data: {request_data}")
    
    try:
        # Extract the message and session ID
        message = request_data.get("message", "")
        session_id = request_data.get("sessionId")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get or create session
        if not session_id:
            # Create new session
            session_id = str(uuid.uuid4())
            widget_sessions[session_id] = {
                "chatbot_id": chatbot_id,
                "messages": []
            }
            logger.info(f"Created new widget session: {session_id}")
        elif session_id not in widget_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get session data
        session = widget_sessions[session_id]
        
        # Verify chatbot IDs match
        if session["chatbot_id"] != chatbot_id:
            raise HTTPException(status_code=400, detail="Invalid session for this chatbot")
        
        # Get the chatbot configuration
        chatbot = await get_chatbot_or_404(chatbot_id)
        
        # Get settings from chatbot
        settings = chatbot.get("settings", {})
        temperature = settings.get("temperature", 0.7)
        instructions = settings.get("instructions", "")
        documents = chatbot.get("documents", [])
        
        # Initialize query engine with proper configuration
        query_engine = QueryEngine(
            temperature=temperature,
            instructions=instructions
        )
        
        # Generate response using query method which handles context properly
        response_text, sources, tokens = await query_engine.query(
            query=message,
            document_ids=documents,
            chat_history=session["messages"]
        )
        
        # Update session history
        session["messages"].append({
            "role": "user",
            "content": message
        })
        session["messages"].append({
            "role": "assistant",
            "content": response_text
        })
        
        logger.info(f"Widget chat response generated for chatbot: {chatbot_id}")
        
        # Return the response with session ID and sources
        return {
            "sessionId": session_id,
            "response": response_text,
            "sources": sources
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in widget chat: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Request models
class ChatRequest(BaseModel):
    message: str

class WidgetSessionRequest(BaseModel):
    chatbotId: Optional[str] = None

class WidgetMessageRequest(BaseModel):
    sessionId: str
    message: str

# Response models
class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []

class SessionResponse(BaseModel):
    sessionId: str
    welcomeMessage: Optional[str] = None

class PreviewRequest(BaseModel):
    chatbotId: Optional[str] = None
    message: str
    documents: List[str] = []
    settings: Dict[str, Any] = {}

class PreviewResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    rag_status: Optional[str] = None

# In-memory storage for widget sessions (would be replaced by database in production)
widget_sessions = {}

@router.post("/widget/{chatbot_id}/session", response_model=SessionResponse)
async def create_widget_session(
    chatbot_id: str,
    request: WidgetSessionRequest = Body(...)
):
    """Create a new chat session for the widget"""
    try:
        logger.info(f"Creating widget session for chatbot: {chatbot_id}")
        
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Store session info (in a real implementation, this would be in a database)
        widget_sessions[session_id] = {
            "chatbot_id": chatbot_id,
            "messages": []
        }
        
        # In a real implementation, we would fetch the chatbot configuration
        # to get a welcome message and other settings
        welcome_message = "Hi there! How can I help you today?"
        
        logger.info(f"Widget session created: {session_id}")
        
        return SessionResponse(
            sessionId=session_id,
            welcomeMessage=welcome_message
        )
    except Exception as e:
        logger.error(f"Error creating widget session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/widget/{chatbot_id}/message", response_model=ChatResponse)
async def chat_with_widget(
    chatbot_id: str,
    request: WidgetMessageRequest = Body(...)
):
    """Process a message from the widget"""
    try:
        logger.info(f"Processing widget message for chatbot: {chatbot_id}, session: {request.sessionId}")
        
        # Verify session exists
        if request.sessionId not in widget_sessions:
            logger.error(f"Session not found: {request.sessionId}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get session data
        session = widget_sessions[request.sessionId]
        
        # Verify chatbot IDs match
        if session["chatbot_id"] != chatbot_id:
            logger.error(f"Chatbot ID mismatch: {session['chatbot_id']} != {chatbot_id}")
            raise HTTPException(status_code=400, detail="Invalid session for this chatbot")
        
        # Initialize query engine
        query_engine = QueryEngine()
        
        message = request.message
        chat_history = session["messages"]
        instructions = "You are a helpful chatbot assistant."  # Would come from chatbot settings
        temperature = 0.7  # Would come from chatbot settings
        
        # Get context from documents
        context = query_engine.get_context(
            query=message,
            documents=[]  # In production, would fetch document IDs from chatbot configuration
        )
        
        # Generate response
        response = query_engine._query_llm_only(
            query_text=message,
            temperature=temperature,
            instructions=instructions
        )
        
        # Update session history
        session["messages"].append({
            "role": "user",
            "content": message
        })
        session["messages"].append({
            "role": "assistant",
            "content": response["response"]
        })
        
        # Return response
        return ChatResponse(
            response=response["response"],
            sources=[]  # In production, would extract sources from response
        )
    except Exception as e:
        logger.error(f"Error processing widget message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.post("/chatbots/preview", response_model=PreviewResponse)
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
        response_text, sources, _, rag_status = await query_engine.query(
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
        logger.error(f"Error in preview chatbot: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to preview chatbot: {str(e)}")