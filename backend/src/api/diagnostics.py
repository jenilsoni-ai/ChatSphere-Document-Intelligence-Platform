from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging
from datetime import datetime
import traceback

from ..db.vector_store import get_vector_db
from ..db.firebase import FirestoreDB
from ..services.document_processor import DocumentProcessor
from ..services.embedding import EmbeddingService
from ..core.auth import get_current_user_id
from ..services.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
firestore_db = FirestoreDB()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/vector-db", dependencies=[Depends(get_current_user_id)])
async def vector_db_status():
    """Check vector database connection status"""
    try:
        # Initialize vector DB
        vector_db = get_vector_db()
        
        # Check connection
        status = vector_db.check_connection()
        
        return status
    except Exception as e:
        logger.error(f"Error checking vector database status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check vector database status: {str(e)}"
        )

@router.get("/document-stats", dependencies=[Depends(get_current_user_id)])
async def document_stats():
    """Get document statistics"""
    try:
        # Initialize Firestore
        firestore_db = FirestoreDB()
        
        # Get document counts by status
        result = await firestore_db.get_document_stats()
        
        return result
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document stats: {str(e)}"
        )

@router.post("/test-embedding", dependencies=[Depends(get_current_user_id)])
async def test_embedding(text: str):
    """Test embedding generation for a text"""
    try:
        if not text or len(text) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must be at least 10 characters long"
            )
            
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Generate embedding
        start_time = datetime.now()
        embedding = await embedding_service.get_embedding(text)
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "text_length": len(text),
            "embedding_dimension": len(embedding),
            "duration_seconds": duration,
            "embedding_preview": embedding[:5]  # Just show the first 5 values
        }
    except Exception as e:
        logger.error(f"Error testing embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test embedding: {str(e)}"
        )

@router.get("/system-status", dependencies=[Depends(get_current_user_id)])
async def system_status():
    """Get overall system status"""
    try:
        # Initialize components
        vector_db = get_vector_db()
        firestore_db = FirestoreDB()
        
        # Check vector DB
        vector_status = vector_db.check_connection()
        
        # Get document stats
        document_stats = await firestore_db.get_document_stats()
        
        # Check embedding service
        embedding_service = EmbeddingService()
        embedding_status = "ok"
        try:
            # Generate a test embedding
            await embedding_service.get_embedding("This is a test embedding for system status check.")
        except Exception as e:
            embedding_status = f"error: {str(e)}"
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "vector_db": vector_status.get("status"),
                "document_store": "ok",  # Firestore is likely up if we got document_stats
                "embedding": embedding_status
            },
            "vector_db_details": vector_status,
            "document_stats": document_stats
        }
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/stats/overview")
async def get_overview_stats(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get overview statistics for the dashboard"""
    try:
        logger.info(f"Fetching overview stats for user: {user_id}")
        
        # Extract just the user ID string
        user_id_str = user_id.id
        
        # Get total chatbots
        chatbots = await firestore_db.list_chatbots(user_id_str)
        total_chatbots = len(chatbots)
        logger.debug(f"Found {total_chatbots} chatbots")

        # Get total conversations (chat sessions)
        chat_sessions = await firestore_db.list_chat_sessions(user_id_str)
        total_conversations = len(chat_sessions)
        logger.debug(f"Found {total_conversations} conversations")

        # Get total datasources (documents)
        documents = await firestore_db.list_documents(user_id_str)
        total_datasources = len(documents)
        logger.debug(f"Found {total_datasources} datasources")

        stats = {
            "total_chatbots": total_chatbots,
            "total_conversations": total_conversations,
            "total_datasources": total_datasources
        }
        logger.info(f"Successfully fetched stats for user {user_id_str}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to fetch overview stats for user {user_id}: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch overview stats: {str(e)}"
        ) 