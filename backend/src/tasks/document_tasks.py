import logging
from datetime import datetime
from typing import Optional

from src.db.firebase import firestore_db, storage
from src.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

async def process_document(document_id: str) -> dict:
    """
    Process a document synchronously within the request cycle.
    """
    logger.info(f"Starting processing for document ID: {document_id}")

    # Instantiate processor inside the task
    document_processor = DocumentProcessor()

    try:
        # Get document from Firestore
        logger.info(f"Getting document {document_id} from Firestore.")
        doc = await firestore_db.get_document(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found in Firestore.")
            raise Exception(f"Document {document_id} not found")
        logger.info(f"Document {document_id} found.")

        # Update status to processing
        logger.info(f"Updating document {document_id} status to 'processing'.")
        await firestore_db.update_document(
            document_id,
            {
                "processingStatus": "processing",
                "updatedAt": datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Document {document_id} status updated to 'processing'.")

        # Process the document
        logger.info(f"Calling document_processor.process_document for {document_id}.")
        result = await document_processor.process_document(document_id=document_id)
        logger.info(f"document_processor.process_document completed for {document_id}.")

        logger.info(f"Document processing task finished for {document_id}")
        
        return result

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        
        # Simple error handling: update status to failed and re-raise
        try:
            await firestore_db.update_document(
                document_id,
                {
                    "processingStatus": "failed",
                    "error": str(e),
                    "updatedAt": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Updated document {document_id} status to failed.")
        except Exception as update_err:
            logger.error(f"Failed to update document {document_id} status to failed: {update_err}")
        
        # Re-raise the original exception so the caller knows something went wrong
        raise e 