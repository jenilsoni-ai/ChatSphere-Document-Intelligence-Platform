import os
import uuid
import tempfile
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from ..core.config import settings
from ..db.firebase import FirestoreDB, FirebaseStorage
from ..db.vector_store import get_vector_db
from ..utils.pdf_utils import extract_text_from_pdf
from loguru import logger

class ProcessingStep:
    """Enum for processing steps"""
    DOWNLOAD = "download"
    TEXT_EXTRACTION = "text_extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    CLEANUP = "cleanup"

class ProcessingStepStatus:
    """Enum for processing step status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentProcessor:
    def __init__(self):
        self.firestore = FirestoreDB()
        self.storage = FirebaseStorage()
        self.vector_db = get_vector_db()
        
        # Initialize embedding model - renamed from embed_model to embeddings
        self.embeddings = HuggingFaceEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )
    
    async def process_document(self, document_id: str) -> Dict[str, Any]:
        """Process a document fetched from Firestore, handle file download or direct content.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dictionary with processing stats (chunk_count, download_time, processing_time, total_time)
        """
        start_time = datetime.now()
        processing_stats = {
            "startTime": start_time.isoformat(),
            "steps": {},
            "stepTimes": {}
        }
        current_step = None
        
        try:
            # Update document status to processing
            await self.firestore.update_document(
                document_id,
                {
                    "processingStatus": "processing", 
                    "updatedAt": datetime.utcnow().isoformat(),
                    "processingStats": processing_stats
                }
            )
            
            # Get document from Firestore
            document_data = await self.firestore.get_document(document_id)
            if not document_data:
                logger.error(f"Document {document_id} not found")
                await self._update_document_status(document_id, "failed", "Document not found", processing_stats)
                return {"error": "Document not found"}
            
            logger.info(f"Processing document: {document_id}")
            
            # Prepare base metadata
            base_metadata = {
                "document_id": document_id,
                "name": document_data.get("name", "Untitled"),
                "created_at": document_data.get("createdAt", datetime.utcnow().isoformat())
            }
            
            # Check if this is a file or direct text
            storage_path = document_data.get("storageUri")
            
            # Process file from storage
            if storage_path:
                # STEP 1: DOWNLOAD
                current_step = ProcessingStep.DOWNLOAD
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
                
                download_start = datetime.now()
                try:
                    local_file_path = await self.storage.download_file(storage_path)
                    download_time = (datetime.now() - download_start).total_seconds()
                    processing_stats["stepTimes"][current_step] = download_time
                    logger.info(f"Downloaded file in {download_time:.2f} seconds")
                    
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                    
                    # STEP 2-5: PROCESS CONTENT
                    try:
                        chunks = await self._process_content(document_id, base_metadata, file_path=local_file_path, processing_stats=processing_stats)
                    finally:
                        # STEP 6: CLEANUP - Remove temp file regardless of success
                        current_step = ProcessingStep.CLEANUP
                        await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
                        
                        try:
                            if os.path.exists(local_file_path):
                                os.unlink(local_file_path)
                                logger.info(f"Deleted temporary file: {local_file_path}")
                            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                        except Exception as e:
                            logger.warning(f"Failed to delete temporary file: {str(e)}")
                            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(e))
                except Exception as download_err:
                    logger.error(f"Failed to download file for document {document_id}: {download_err}")
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(download_err))
                    await self._update_document_status(document_id, "failed", f"Failed to download file: {str(download_err)}", processing_stats)
                    return {"error": f"Failed to download file: {str(download_err)}"}
            
            # Direct text content (e.g., from website)
            else:
                text_content = document_data.get("content")
                if not text_content:
                    logger.error(f"Document {document_id} has no content or file")
                    await self._update_document_status(document_id, "failed", "Document has no content or file", processing_stats)
                    return {"error": "Document has no content or file"}
                
                chunks = await self._process_content(document_id, base_metadata, text_content=text_content, processing_stats=processing_stats)
            
            if not chunks:
                logger.error(f"No chunks created for document {document_id}")
                await self._update_document_status(document_id, "failed", "No chunks created", processing_stats)
                return {"error": "No chunks created"}
            
            # Calculate processing time
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Update final processing stats
            processing_stats["endTime"] = end_time.isoformat()
            processing_stats["totalTime"] = total_time
            processing_stats["chunkCount"] = len(chunks)
            
            # Update document status to completed
            update_data = {
                "processingStatus": "completed",
                "chunkCount": len(chunks),
                "vectorIds": [chunk['id'] for chunk in chunks],
                "processingStats": processing_stats,
                "updatedAt": datetime.utcnow().isoformat(),
                "error": None
            }
            
            await self.firestore.update_document(document_id, update_data)
            logger.info(f"Document {document_id} processing completed in {total_time:.2f} seconds with {len(chunks)} chunks")
            
            # Prepare results
            result_data = {
                "chunk_count": len(chunks),
                "vector_ids": [chunk['id'] for chunk in chunks],
                "processing_time": total_time,
                "processing_stats": processing_stats
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            await self._update_document_status(document_id, "failed", str(e), processing_stats)
            return {"error": str(e)}
    
    async def _update_processing_status(self, document_id: str, step: str, status: str, processing_stats: Dict[str, Any], error: Optional[str] = None):
        """Update processing status for a specific step"""
        try:
            # Update step status
            if "steps" not in processing_stats:
                processing_stats["steps"] = {}
                
            processing_stats["steps"][step] = {
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if error:
                processing_stats["steps"][step]["error"] = error
            
            # Update document with new processing stats
            await self.firestore.update_document(
                document_id,
                {
                    "processingStats": processing_stats,
                    "updatedAt": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update processing status for document {document_id}, step {step}: {str(e)}")
    
    async def _update_document_status(self, document_id: str, status: str, error: Optional[str] = None, processing_stats: Optional[Dict[str, Any]] = None):
        """Update document status"""
        try:
            update_data = {
                "processingStatus": status,
                "updatedAt": datetime.utcnow().isoformat()
            }
            
            if error:
                update_data["error"] = error
                
            if processing_stats:
                update_data["processingStats"] = processing_stats
                
            await self.firestore.update_document(document_id, update_data)
        except Exception as e:
            logger.warning(f"Failed to update document status for {document_id}: {str(e)}")
    
    async def _process_content(self, 
                              document_id: str, 
                              base_metadata: Optional[Dict[str, Any]] = None,
                              file_path: Optional[str] = None, 
                              text_content: Optional[str] = None,
                              processing_stats: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process content from a file or text, generate embeddings, and prepare chunk data."""
        if not base_metadata:
            base_metadata = {"document_id": document_id}
            
        if not processing_stats:
            processing_stats = {"steps": {}}
            
        current_step = None
            
        try:
            documents = []
            
            # STEP 2: TEXT EXTRACTION
            current_step = ProcessingStep.TEXT_EXTRACTION
            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
            
            extraction_start = datetime.now()
            
            try:
                # Process text from file
                if file_path:
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    # Process PDF
                    if file_ext == '.pdf':
                        text = await asyncio.to_thread(extract_text_from_pdf, file_path)
                        if not text:
                            logger.warning(f"PDF extraction returned empty text for {document_id}")
                            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, "PDF extraction failed - empty result")
                            return []
                            
                        documents.append(Document(text=text, metadata=base_metadata))
                        
                    # Process TXT
                    elif file_ext == '.txt':
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            text = f.read()
                        if not text:
                            logger.warning(f"Text file is empty for {document_id}")
                            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, "Text file is empty")
                            return []
                            
                        documents.append(Document(text=text, metadata=base_metadata))
                        
                    # Process DOCX or other document types
                    else:
                        # Use LlamaIndex's SimpleDirectoryReader to handle various file types
                        reader = SimpleDirectoryReader(input_files=[file_path])
                        documents = await asyncio.to_thread(reader.load_data)
                        
                        # Add metadata to each document
                        for doc in documents:
                            doc.metadata.update(base_metadata)
                # Process direct text content
                elif text_content:
                    metadata = base_metadata.copy()
                    metadata["content"] = text_content
                    documents.append(Document(text=text_content, metadata=metadata))
                    
                else:
                    logger.error(f"No file path or text content provided for document {document_id}")
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, "No file path or text content provided")
                    return []
                
                # Validate text extraction results
                if not documents or all(not doc.text for doc in documents):
                    logger.error(f"Text extraction failed - no text content found for document {document_id}")
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, "Text extraction failed - no content found")
                    return []
                
                extraction_time = (datetime.now() - extraction_start).total_seconds()
                processing_stats["stepTimes"][current_step] = extraction_time
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                
            except Exception as extract_err:
                logger.error(f"Failed to extract text from document {document_id}: {extract_err}")
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(extract_err))
                return []
            
            # STEP 3: CHUNKING
            current_step = ProcessingStep.CHUNKING
            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
            
            chunking_start = datetime.now()
            
            try:
                # Split text into chunks
                splitter = SentenceSplitter(
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP
                )
                nodes = await asyncio.to_thread(splitter.get_nodes_from_documents, documents)
                
                if not nodes:
                    logger.error(f"Chunking failed - no chunks created for document {document_id}")
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, "Chunking failed - no chunks created")
                    return []
                
                chunking_time = (datetime.now() - chunking_start).total_seconds()
                processing_stats["stepTimes"][current_step] = chunking_time
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                
            except Exception as chunk_err:
                logger.error(f"Failed to chunk text for document {document_id}: {chunk_err}")
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(chunk_err))
                return []
            
            # STEP 4: EMBEDDING
            current_step = ProcessingStep.EMBEDDING
            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
            
            embedding_start = datetime.now()
            
            try:
                # Extract text from nodes
                texts_to_embed = [node.get_content(metadata_mode="none") for node in nodes]
                
                # Generate embeddings
                embeddings = await asyncio.to_thread(self.embeddings.get_text_embedding_batch, texts_to_embed)
                
                if len(embeddings) != len(nodes):
                    logger.error(f"Embedding mismatch - got {len(embeddings)} embeddings for {len(nodes)} chunks")
                    await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, f"Embedding mismatch - got {len(embeddings)} embeddings for {len(nodes)} chunks")
                    return []
                
                embedding_time = (datetime.now() - embedding_start).total_seconds()
                processing_stats["stepTimes"][current_step] = embedding_time
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                
            except Exception as embed_err:
                logger.error(f"Failed to generate embeddings for document {document_id}: {embed_err}")
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(embed_err))
                return []
            
            # STEP 5: STORAGE
            current_step = ProcessingStep.STORAGE
            await self._update_processing_status(document_id, current_step, ProcessingStepStatus.IN_PROGRESS, processing_stats)
            
            storage_start = datetime.now()
            
            try:
                # Prepare chunks for insertion
                chunks_for_insertion = []
                
                for i, (node, embedding) in enumerate(zip(nodes, embeddings)):
                    chunk_id = str(uuid.uuid4())
                    chunk_text = node.get_content(metadata_mode="none")
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update(node.metadata)
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['total_chunks'] = len(nodes)
                    chunk_metadata["content"] = chunk_text
                    
                    if "content" in chunk_metadata:
                        logger.info(f"Chunk {i}: 'content' key present. Preview: {chunk_text[:50]}")
                    else:
                        logger.error(f"Chunk {i}: 'content' key NOT present. Keys: {list(chunk_metadata.keys())}")
                    
                    chunk_data = {
                        'id': chunk_id,
                        'document_id': document_id,
                        'chunk_id': chunk_id,
                        'text': chunk_text,
                        'embedding': embedding,
                        'metadata': json.dumps(chunk_metadata)  # Add metadata as JSON string
                    }
                    chunks_for_insertion.append(chunk_data)
                
                # Insert chunks into vector database
                await self.vector_db.insert_embeddings(chunks_for_insertion)
                
                storage_time = (datetime.now() - storage_start).total_seconds()
                processing_stats["stepTimes"][current_step] = storage_time
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.COMPLETED, processing_stats)
                
                return chunks_for_insertion
                
            except Exception as storage_err:
                logger.error(f"Failed to store embeddings for document {document_id}: {storage_err}")
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(storage_err))
                return []
            
        except Exception as e:
            logger.error(f"Error processing content for document {document_id}: {str(e)}", exc_info=True)
            if current_step:
                await self._update_processing_status(document_id, current_step, ProcessingStepStatus.FAILED, processing_stats, str(e))
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its embeddings
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful
        """
        # Get document metadata
        document_data = await self.firestore.get_document(document_id)
        if not document_data:
            return False
        
        # Delete embeddings from Milvus
        await self.vector_db.delete_by_document_id(document_id)
        
        # Delete file from Firebase Storage
        storage_path = document_data.get('storageUri')
        if storage_path:
            await self.storage.delete_file(storage_path)
        
        # Delete document from Firestore
        await self.firestore.delete_document(document_id)
        
        return True
    
    async def reindex_document(self, document_id: str) -> bool:
        """Reindex a document
        
        Args:
            document_id: ID of the document to reindex
            
        Returns:
            True if successful
        """
        # Delete existing embeddings
        await self.vector_db.delete_by_document_id(document_id)
        
        # Process document again
        return await self.process_document(document_id)

    async def process_document_immediately(self, document_id: str, max_retries: int = 3) -> bool:
        """Process a document from Firebase Storage and store its embeddings
        
        Args:
            document_id: ID of the document to process
            max_retries: Maximum number of retries for fetching document
            
        Returns:
            True if successful
        """
        start_time = datetime.now()
        logger.info(f"Starting document processing at {start_time}")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Processing attempt {attempt + 1}/{max_retries} for document {document_id}")
                
                # Get document metadata from Firestore with retries
                document_data = await self.firestore.get_document(document_id)
                if not document_data:
                    if attempt < max_retries - 1:
                        logger.info(f"Document {document_id} not found, waiting 2 seconds before retry...")
                        await asyncio.sleep(2)
                        continue
                    error_msg = f"Document {document_id} not found after {max_retries} attempts"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Retrieved document metadata: {document_data.get('name')} ({document_data.get('fileType')})")
                
                # Verify document data is complete
                required_fields = ['storageUri', 'id', 'processingStatus']
                missing_fields = [field for field in required_fields if field not in document_data]
                if missing_fields:
                    error_msg = f"Document {document_id} is missing required fields: {', '.join(missing_fields)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Download file from Firebase Storage
                storage_path = document_data['storageUri']
                logger.info(f"Downloading document from storage: {storage_path}")
                download_start = datetime.now()
                local_file_path = await self.storage.download_file(storage_path)
                download_time = (datetime.now() - download_start).total_seconds()
                logger.info(f"Download completed in {download_time:.2f} seconds")
                
                # Process document
                logger.info("Starting document processing and vector embedding creation")
                process_start = datetime.now()
                chunks = await self._process_content(document_id=document_id, file_path=local_file_path)
                process_time = (datetime.now() - process_start).total_seconds()
                logger.info(f"Processing completed in {process_time:.2f} seconds")
                
                # Clean up temporary file
                try:
                    os.unlink(local_file_path)
                    logger.info("Temporary file cleaned up successfully")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {str(e)}")
                
                # Update document status to completed
                logger.info(f"Updating document status - {len(chunks)} chunks created")
                update_data = {
                    'processingStatus': 'completed',
                    'chunkCount': len(chunks),
                    'updatedAt': datetime.now().isoformat(),
                    'processingStats': {
                        'downloadTime': download_time,
                        'processTime': process_time,
                        'totalChunks': len(chunks),
                        'completedAt': datetime.now().isoformat()
                    }
                }
                
                # Retry the status update if it fails
                for update_attempt in range(3):
                    try:
                        await self.firestore.update_document(document_id, update_data)
                        break
                    except Exception as e:
                        if update_attempt == 2:  # Last attempt
                            logger.error(f"Failed to update document status after 3 attempts: {str(e)}")
                            raise
                        logger.warning(f"Failed to update document status (attempt {update_attempt + 1}): {str(e)}")
                        await asyncio.sleep(1)
                
                total_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Document processing completed successfully in {total_time:.2f} seconds")
                logger.info(f"Stats: Download={download_time:.2f}s, Process={process_time:.2f}s, Chunks={len(chunks)}")
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, waiting 2 seconds before retry...")
                    await asyncio.sleep(2)
                    continue
                    
                error_msg = f"Error processing document {document_id}: {str(e)}"
                logger.error(error_msg)
                logger.exception("Full traceback:")
                
                # Try to update document status to failed
                try:
                    await self.firestore.update_document(document_id, {
                        'processingStatus': 'failed',
                        'error': error_msg,
                        'errorTimestamp': datetime.now().isoformat(),
                        'processingStats': {
                            'failedAt': datetime.now().isoformat(),
                            'totalAttempts': attempt + 1,
                            'errorMessage': str(e)
                        }
                    })
                except Exception as update_error:
                    logger.error(f"Failed to update error status: {str(update_error)}")
                raise
        
        return False