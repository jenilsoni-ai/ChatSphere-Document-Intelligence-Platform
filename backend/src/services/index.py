from typing import List, Dict, Any, Optional
import os
import tempfile

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Document
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from ..core.config import settings
from ..db.vector_store import get_vector_db
from .embedding import EmbeddingService

class IndexService:
    def __init__(self):
        """Initialize the index service"""
        self.vector_db = get_vector_db()
        self.embedding_service = EmbeddingService()
        
        # Initialize embedding model - renamed from embed_model to embeddings
        self.embeddings = HuggingFaceEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )
    
    async def create_index(self, documents: List[Document], document_id: str) -> List[str]:
        """Create a vector index for a list of documents
        
        Args:
            documents: List of Document objects
            document_id: ID of the document being indexed
            
        Returns:
            List of vector IDs
        """
        try:
            if settings.VECTOR_DB_TYPE.lower() == "qdrant":
                # Qdrant vector store
                client = self.vector_db.client
                vector_store = QdrantVectorStore(
                    client=client,
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    prefer_grpc=True
                )
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                # Tag each document with the document_id metadata
                for doc in documents:
                    if "metadata" not in doc.metadata:
                        doc.metadata["metadata"] = {}
                    doc.metadata["metadata"]["document_id"] = document_id
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=self.embeddings
                )
                # Collect vector IDs from the index
                vector_ids = [node.vector_id for node in index.docstore.docs.values() if getattr(node, "vector_id", None)]
                return vector_ids
            else:
                # Milvus vector store
                vector_store = MilvusVectorStore(
                    collection_name=settings.ZILLIZ_COLLECTION_NAME,
                    uri=settings.ZILLIZ_URI,
                    token=settings.ZILLIZ_API_KEY,
                    dim=settings.EMBEDDING_DIMENSION
                )
                
                storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )
                
                # Create index with document ID as metadata
                for doc in documents:
                    if "metadata" not in doc.metadata:
                        doc.metadata["metadata"] = {}
                    doc.metadata["metadata"]["document_id"] = document_id
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=self.embeddings
                )
                vector_ids = []
                for node in index.docstore.docs.values():
                    if hasattr(node, "vector_id") and node.vector_id:
                        vector_ids.append(node.vector_id)
                return vector_ids
        except Exception as e:
            raise Exception(f"Failed to create index: {str(e)}")
    
    async def delete_index(self, vector_ids: List[str]) -> bool:
        """Delete vectors from the index
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            True if successful
        """
        try:
            # Delete vectors from Milvus
            await self.vector_db.delete_vectors(vector_ids)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete index: {str(e)}")
    
    async def get_index_for_documents(self, document_ids: List[str]):
        """Get a query index for a list of documents
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            VectorStoreIndex object
        """
        try:
            # Select vector store implementation based on configuration
            if settings.VECTOR_DB_TYPE.lower() == "qdrant":
                client = self.vector_db.client
                vector_store = QdrantVectorStore(
                    client=client,
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    prefer_grpc=True,
                    metadata_filter={"document_id": {"$in": document_ids}}
                )
            else:
                # Milvus vector store with metadata filter
                vector_store = MilvusVectorStore(
                    collection_name=settings.ZILLIZ_COLLECTION_NAME,
                    uri=settings.ZILLIZ_URI,
                    token=settings.ZILLIZ_API_KEY,
                    dim=settings.EMBEDDING_DIMENSION,
                    metadata_filter={"document_id": {"$in": document_ids}}
                )
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # Create index
            index = VectorStoreIndex(
                [],
                storage_context=storage_context,
                embed_model=self.embeddings
            )
            
            return index
        except Exception as e:
            raise Exception(f"Failed to get index for documents: {str(e)}")