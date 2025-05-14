from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from typing import List, Optional
import uuid
from datetime import datetime
import logging
import asyncio

from ..db.firebase import FirestoreDB, FirebaseStorage
from ..models.document import DocumentCreate, DocumentResponse, DocumentUpdate, DocumentUpload, Document
from ..services.document_processor import DocumentProcessor
from ..core.auth import get_current_user_id
from ..services.auth import get_current_user, User
from ..services.website_scraper import website_scraper
from ..tasks.document_tasks import process_document

router = APIRouter()
firestore_db = FirestoreDB()
firebase_storage = FirebaseStorage()
document_processor = DocumentProcessor()

logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id) 
):
    try:
        logger.info(f"User {user_id} starting document upload: {name} ({file.filename})")
        
        # Validate file type
        allowed_types = [".pdf", ".txt", ".docx"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_types):
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Create document ID first
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")

        # Upload file to storage (pass document_id and user_id)
        file_size = await firebase_storage.upload_file(file, document_id, user_id)
        storage_path = f"documents/{user_id}/{document_id}/{file.filename}" # Construct storage path
        logger.info(f"File uploaded successfully to storage: {storage_path}")
        
        # Create document data in Firestore
        document_data = {
            "id": document_id, # Add ID to the data
            "name": name, # Use name from form
            "description": description, # Use description from form
            "ownerId": user_id, # Add owner ID
            "fileType": file.filename.split('.')[-1] if '.' in file.filename else 'unknown',
            "fileSize": file_size,
            "uploadedAt": datetime.utcnow().isoformat(),
            "storageUri": storage_path,
            "processingStatus": "pending",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "chunkCount": 0,
            "vectorIds": [],
            "error": None
        }
        
        # Create document record in Firestore using the generated ID
        await firestore_db.create_document(document_data) # Assuming create_document handles setting with ID
        logger.info(f"Document metadata created in Firestore for ID: {document_id}")
        
        # Queue document processing task to the correct queue
        logger.info(f"Starting synchronous document processing for document ID: {document_id}")
        try:
            await process_document(document_id)
            logger.info(f"Synchronous processing completed for document ID: {document_id}")
        except Exception as process_error:
            logger.error(f"Synchronous processing failed for document ID {document_id}: {process_error}", exc_info=True)
            # Optionally re-raise or handle the error appropriately for the API response
            # For now, we log it and let the function continue to return 'pending', 
            # but the status in Firestore would have been set to 'failed' by process_document
            pass 
        logger.info(f"Document processing initiated synchronously for document ID: {document_id}")
        
        # Return the document ID and status
        # The status is initially 'pending', but will be updated by process_document.
        # Consider if the API should wait and return the final status, or return immediately.
        # For now, returning 'pending' as before.
        return {
            "documentId": document_id,
            "status": "pending", # Or potentially query the status after await?
            "message": "Document upload successful. Processing initiated.", # MODIFIED
            "name": name, # Return name for consistency
            "id": document_id # Return id as well
        }
        
    except Exception as e:
        logger.error(f"Error in document upload for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("", response_model=List[DocumentResponse])
async def list_documents(user_id: str = Depends(get_current_user_id)):
    """List all documents for the current user"""
    try:
        logger.info(f"Listing documents for user: {user_id}")
        documents = await firestore_db.list_documents(user_id)
        logger.info(f"Found {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Failed to list documents for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Get document details"""
    try:
        document = await firestore_db.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user owns the document
        if document.get("ownerId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get document: {str(e)}"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a document"""
    try:
        logger.info(f"Starting deletion process for document {document_id}")
        
        # Get document to check ownership
        document = await firestore_db.get_document(document_id)
        
        if not document:
            logger.warning(f"Document {document_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get the user's actual ID from the token
        user_uid = user_id.get('uid') if isinstance(user_id, dict) else user_id
        
        # Check if user owns the document
        if document.get("ownerId") != user_uid:
            logger.warning(f"User {user_uid} not authorized to delete document {document_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document"
            )
            
        try:
            # First, remove document from any chatbots that reference it
            chatbots = await firestore_db.list_chatbots(user_uid)
            for chatbot in chatbots:
                if document_id in chatbot.get("documents", []):
                    logger.info(f"Removing document {document_id} from chatbot {chatbot['id']}")
                    current_docs = chatbot.get("documents", [])
                    new_docs = [doc for doc in current_docs if doc != document_id]
                    await firestore_db.update_chatbot(chatbot["id"], {
                        "documents": new_docs,
                        "updatedAt": datetime.now()
                    })
            
            # Delete vector embeddings if they exist
            if document.get("vectorIds"):
                logger.info(f"Deleting vector embeddings for document {document_id}")
                await document_processor.delete_document(document_id)
            
            # Delete file from Firebase Storage if it exists
            storage_uri = document.get("storageUri")
            if storage_uri:
                logger.info(f"Deleting file from storage: {storage_uri}")
                try:
                    await firebase_storage.delete_file(storage_uri)
                except Exception as e:
                    logger.warning(f"Failed to delete file from storage: {str(e)}")
                    # Continue with deletion even if storage deletion fails
            
            # Finally, delete document from Firestore
            logger.info(f"Deleting document metadata from Firestore")
            await firestore_db.delete_document(document_id)
            
            logger.info(f"Document {document_id} deleted successfully")
            return None
            
        except Exception as e:
            logger.error(f"Error during document deletion process: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Reindex a document"""
    try:
        # Get document to check ownership
        document = await firestore_db.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user owns the document
        if document.get("ownerId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to reindex this document"
            )
        
        # Update document status to processing
        await firestore_db.update_document(document_id, {
            "processingStatus": "processing",
            "chunkCount": None,
            "vectorIds": None
        })
        
        # Process document immediately
        await document_processor.process_document_immediately(document_id)
        
        # Get updated document
        updated_document = await firestore_db.get_document(document_id)
        
        return updated_document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reindex document: {str(e)}"
        )

@router.post("/url")
async def create_document_from_url(
    url: str = Body(...),
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Create a new document from a website URL"""
    document_id = None # Initialize document_id
    try:
        logger.info(f"Starting website content extraction from URL: {url}")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format. URL must start with http:// or https://"
            )
        
        # Scrape the website content
        scraped_data = await website_scraper.scrape_url(url)
        if not scraped_data:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from the website. Please check if the URL is accessible."
            )
            
        logger.info(f"Successfully extracted content from URL: {url}")
        logger.info(f"Content length: {len(scraped_data['content'])} characters")
            
        # Create document ID first
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID for URL import: {document_id}")
        
        # Prepare document data
        document_data = {
            "id": document_id,
            "name": name or scraped_data['title'] or f"Website - {url[:50]}...", # Ensure name is not empty
            "description": description or scraped_data['description'] or "",
            "ownerId": current_user.id,
            "content": scraped_data['content'], # Store raw content temporarily
            "fileType": "website",
            "fileSize": len(scraped_data['content'].encode('utf-8')),
            # MODIFY: Set status to pending
            "processingStatus": "pending", 
            "source_url": url,
            "source_type": "website",
            "metadata": {
                "word_count": scraped_data['word_count'],
                "source_url": url,
                "title": scraped_data['title'],
                "description": scraped_data['description']
            },
            "uploadedAt": datetime.now(),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
        
        # Save initial metadata to database
        await firestore_db.create_document(document_data)
        logger.info(f"Initial document metadata created successfully with ID: {document_id}")

        # ADD: Trigger synchronous processing
        logger.info(f"Starting synchronous processing for URL document ID: {document_id}")
        try:
            await process_document(document_id)
            logger.info(f"Synchronous URL processing completed for document ID: {document_id}")
            # Optional: Update status explicitly to 'completed' here if process_document doesn't always do it on success?
        except Exception as process_error:
            logger.error(f"Synchronous URL processing failed for document ID {document_id}: {process_error}", exc_info=True)
            # Status should have been set to 'failed' within process_document
            pass # Let the API return the initial pending status
        
        # Return initial response - processing happens in the background (now synchronously)
        return {
            "id": document_id, # Use the generated ID
            "name": document_data['name'],
            "description": document_data['description'],
            # MODIFY: Return pending status
            "status": "pending", 
            # MODIFY: Update message
            "message": "Website content extracted. Processing started.", 
            "metadata": document_data['metadata']
        }
        
    except HTTPException as http_exc:
        # If processing failed above, ensure status is updated if needed
        if document_id and "processing failed" in str(http_exc.detail).lower():
             try:
                 await firestore_db.update_document(document_id, {"processingStatus": "failed", "error": str(http_exc.detail)})
             except Exception: pass # Ignore update error
        raise http_exc
    except Exception as e:
        logger.error(f"Error creating document from URL: {str(e)}", exc_info=True)
        # If processing failed above, ensure status is updated if needed
        if document_id:
             try:
                 await firestore_db.update_document(document_id, {"processingStatus": "failed", "error": str(e)})
             except Exception: pass # Ignore update error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create document: {str(e)}"
        )