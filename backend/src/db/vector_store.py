import os
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import time
import json
from pymilvus import (
    connections, 
    utility,
    Collection, 
    FieldSchema, 
    CollectionSchema, 
    DataType
)
from ..core.config import settings
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance

logger = logging.getLogger(__name__)

class MilvusDB:
    def __init__(self):
        self.collection_name = settings.ZILLIZ_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.connection_established = False
        self.max_retries = 3
        logger.info(f"Initializing MilvusDB with collection: {self.collection_name}, dimension: {self.dimension}")
        self.connect_with_retry()
        self.initialize_collection()
    
    def connect_with_retry(self, retries=None):
        """Connect to Zilliz Cloud with retry logic"""
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to Zilliz Cloud at: {settings.ZILLIZ_URI} (Attempt {attempt+1}/{retries})")
                connections.connect(
                    alias="default", 
                    uri=settings.ZILLIZ_URI,
                    token=settings.ZILLIZ_API_KEY,
                    timeout=30  # Add timeout parameter
                )
                self.connection_established = True
                logger.info("Successfully connected to Zilliz Cloud")
                return True
            except Exception as e:
                logger.error(f"Connection attempt {attempt+1} failed: {str(e)}")
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {retries} attempts")
                    self.connection_established = False
                    raise
    
    def connect(self):
        """Connect to Zilliz Cloud"""
        return self.connect_with_retry(1)
    
    def check_connection(self) -> Dict[str, Any]:
        """Check connection status and return diagnostics
        
        Returns:
            Dictionary with connection status and diagnostics
        """
        try:
            # Try to list collections as a connection test
            collections = utility.list_collections()
            
            # Check if our collection exists
            has_collection = utility.has_collection(self.collection_name)
            
            # Get collection stats if available
            entity_count = 0
            if has_collection:
                collection = Collection(self.collection_name)
                entity_count = collection.num_entities
            
            return {
                "status": "connected",
                "collections": collections,
                "target_collection_exists": has_collection,
                "entity_count": entity_count,
                "uri": settings.ZILLIZ_URI.replace(settings.ZILLIZ_API_KEY, "****")  # Mask API key
            }
        except Exception as e:
            self.connection_established = False
            return {
                "status": "disconnected",
                "error": str(e),
                "uri": settings.ZILLIZ_URI.replace(settings.ZILLIZ_API_KEY, "****")  # Mask API key
            }
    
    def initialize_collection(self):
        """Initialize collection if it doesn't exist"""
        try:
            if not self.connection_established:
                logger.warning("Cannot initialize collection: Not connected to vector database")
                return False
                
            has_collection = utility.has_collection(self.collection_name)
            logger.info(f"Checking if collection '{self.collection_name}' exists: {has_collection}")
            
            if not has_collection:
                logger.info(f"Creating new collection: {self.collection_name}")
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                    FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),  # Add metadata field
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
                ]
                schema = CollectionSchema(fields=fields, description="Document chunks embeddings")
                collection = Collection(name=self.collection_name, schema=schema)
                
                # Create index for vector field
                logger.info(f"Creating vector index for collection: {self.collection_name}")
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "HNSW",
                    "params": {"M": 8, "efConstruction": 64}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
                logger.info(f"Successfully created collection and index")
            
            # Load collection
            logger.info(f"Loading collection: {self.collection_name}")
            collection = Collection(self.collection_name)
            collection.load()
            
            # Get collection info instead of stats
            try:
                entity_count = collection.num_entities
                logger.info(f"Collection entity count: {entity_count}")
            except Exception as e:
                logger.warning(f"Could not get entity count: {str(e)}")
            
            logger.info(f"Collection successfully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    def validate_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate embeddings before insertion
        
        Args:
            embeddings_data: List of dictionaries containing embedding data
                
        Returns:
            List of valid embeddings data
        """
        valid_embeddings = []
        for i, data in enumerate(embeddings_data):
            try:
                # Check required fields
                if not all(k in data for k in ["id", "document_id", "chunk_id", "text", "embedding"]):
                    logger.warning(f"Embedding data at index {i} missing required fields")
                    continue
                
                # Validate embedding dimensions
                if len(data["embedding"]) != self.dimension:
                    logger.warning(f"Embedding at index {i} has incorrect dimension: {len(data['embedding'])} (expected {self.dimension})")
                    continue
                
                # Check for NaN values in embedding
                if any(np.isnan(v) for v in data["embedding"]):
                    logger.warning(f"Embedding at index {i} contains NaN values")
                    continue
                
                # Check text length
                if len(data["text"]) > 65000:  # Slightly under the max of 65535 to be safe
                    logger.warning(f"Text at index {i} exceeds maximum length, truncating")
                    data["text"] = data["text"][:65000]
                
                # Create metadata if it doesn't exist
                if "metadata" not in data:
                    # Create JSON string with document_id and chunk_id
                    data["metadata"] = json.dumps({
                        "document_id": data["document_id"],
                        "chunk_id": data["chunk_id"]
                    })
                elif isinstance(data["metadata"], dict):
                    # Convert dict to JSON string
                    data["metadata"] = json.dumps(data["metadata"])
                
                # Check metadata length
                if len(data["metadata"]) > 65000:
                    logger.warning(f"Metadata at index {i} exceeds maximum length, truncating")
                    data["metadata"] = data["metadata"][:65000]
                
                valid_embeddings.append(data)
            except Exception as e:
                logger.error(f"Error validating embedding at index {i}: {str(e)}")
        
        logger.info(f"Validated {len(valid_embeddings)}/{len(embeddings_data)} embeddings")
        return valid_embeddings
    
    async def insert_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[str]:
        """Insert embeddings into the vector store
        
        Args:
            embeddings_data: List of dictionaries containing embedding data
                Each dict should have: id, document_id, chunk_id, text, embedding
                
        Returns:
            List of inserted IDs
        """
        try:
            if not embeddings_data:
                logger.warning("No embeddings data provided for insertion")
                return []
            
            if not self.connection_established:
                logger.warning("Cannot insert embeddings: Not connected to vector database")
                # Try to reconnect
                self.connect_with_retry()
                if not self.connection_established:
                    return []
            
            logger.info(f"Validating and inserting {len(embeddings_data)} embeddings into Zilliz collection: {self.collection_name}")
            
            # Validate embeddings
            valid_embeddings = self.validate_embeddings(embeddings_data)
            if not valid_embeddings:
                logger.error("No valid embeddings to insert")
                return []
            
            # Prepare data for insertion
            ids = [data["id"] for data in valid_embeddings]
            document_ids = [data["document_id"] for data in valid_embeddings]
            chunk_ids = [data["chunk_id"] for data in valid_embeddings]
            texts = [data["text"] for data in valid_embeddings]
            metadatas = [data["metadata"] for data in valid_embeddings]
            embeddings = [data["embedding"] for data in valid_embeddings]
            
            # Get collection
            collection = Collection(self.collection_name)
            
            # Insert data - with retry logic
            for attempt in range(self.max_retries):
                try:
                    insert_result = collection.insert([
                        ids, document_ids, chunk_ids, texts, metadatas, embeddings
                    ])
                    logger.info(f"Successfully inserted {len(valid_embeddings)} embeddings into Zilliz Cloud: {insert_result}")
                    break
                except Exception as e:
                    logger.error(f"Insertion attempt {attempt+1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying insertion in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to insert embeddings after {self.max_retries} attempts")
                        raise
            
            # Flush collection to make the data available for search
            collection.flush()
            logger.info(f"Flushed collection to make data available for search")
            
            return ids
        except Exception as e:
            logger.error(f"Error inserting embeddings into Zilliz Cloud: {str(e)}")
            raise
    
    async def search_similar(self, query_embedding: List[float], limit: int = 5, similarity_cutoff: float = 0.6) -> List[Dict[str, Any]]:
        """Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            limit: Number of results to return
            similarity_cutoff: Minimum similarity score (0-1)
            
        Returns:
            List of similar documents with metadata
        """
        try:
            if not self.connection_established:
                logger.warning("Cannot search: Not connected to vector database")
                # Try to reconnect
                self.connect_with_retry()
                if not self.connection_established:
                    return []
            
            logger.info(f"Searching for similar documents in Zilliz Cloud, top-{limit}, cutoff-{similarity_cutoff}")
            
            # Get collection
            collection = Collection(self.collection_name)
            
            # Define search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64}
            }
            
            # Execute search
            logger.info(f"Executing vector search in collection: {self.collection_name}")
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["document_id", "chunk_id", "text", "metadata"]
            )
            
            # Format results
            formatted_results = []
            for hit in results[0]:
                # Apply similarity cutoff
                if hit.score < similarity_cutoff:
                    continue
                    
                formatted_results.append({
                    "document_id": hit.entity.get("document_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "text": hit.entity.get("text"),
                    "metadata": hit.entity.get("metadata"),
                    "score": hit.score if hasattr(hit, 'score') else None
                })
            
            logger.info(f"Found {len(formatted_results)} similar documents passing the similarity threshold")
            if formatted_results:
                logger.info(f"Top match score: {formatted_results[0]['score'] if formatted_results else 'N/A'}")
            else:
                # If no results with current similarity cutoff, try with a lower cutoff
                if similarity_cutoff > 0.4:
                    logger.info(f"No results above similarity threshold {similarity_cutoff}, trying with lower threshold")
                    # Recursive call with lower similarity_cutoff
                    return await self.search_similar(query_embedding, limit, similarity_cutoff - 0.2)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching in Zilliz Cloud: {str(e)}")
            # Attempt to reconnect on failure
            self.connection_established = False
            self.connect_with_retry(1)
            raise
    
    async def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all embeddings for a document
        
        Args:
            document_id: ID of the document to delete embeddings for
        
        Returns:
            True if successful
        """
        if not self.connection_established:
            logger.warning("Cannot delete: Not connected to vector database")
            # Try to reconnect
            self.connect_with_retry()
            if not self.connection_established:
                return False
                
        try:
            collection = Collection(self.collection_name)
            expr = f'document_id == "{document_id}"'
            collection.delete(expr)
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document
        
        Args:
            document_id: ID of the document
        
        Returns:
            List of chunk data
        """
        if not self.connection_established:
            logger.warning("Cannot get chunks: Not connected to vector database")
            # Try to reconnect
            self.connect_with_retry()
            if not self.connection_established:
                return []
                
        try:
            collection = Collection(self.collection_name)
            expr = f'document_id == "{document_id}"'
            results = collection.query(
                expr=expr,
                output_fields=["id", "chunk_id", "text"]
            )
            return results
        except Exception as e:
            logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    def disconnect(self):
        """Disconnect from Zilliz Cloud"""
        try:
            connections.disconnect("default")
            self.connection_established = False
            logger.info("Disconnected from Zilliz Cloud")
        except Exception as e:
            logger.error(f"Error disconnecting from Zilliz Cloud: {str(e)}")

class QdrantDB:
    def __init__(self):
        # Initialize Qdrant client
        logger.info(f"Initializing QdrantDB with collection: {settings.QDRANT_COLLECTION_NAME}")
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        
        # Ensure collection exists with correct configuration
        try:
            cols = self.client.get_collections().collections
            names = [c.name for c in cols]
            
            # If collection exists, delete it to ensure correct configuration
            if self.collection_name in names:
                logger.info(f"Deleting existing Qdrant collection: {self.collection_name}")
                self.client.delete_collection(collection_name=self.collection_name)
            
            # Create collection with correct configuration
            logger.info(f"Creating new Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
            )
            logger.info(f"Successfully created Qdrant collection with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise

    def check_connection(self) -> dict:
        try:
            cols = self.client.get_collections().collections
            names = [c.name for c in cols]
            has_col = self.collection_name in names
            count = 0
            if has_col:
                count = self.client.count(collection_name=self.collection_name).count  # type: ignore
            return {
                "status": "connected",
                "collections": names,
                "target_collection_exists": has_col,
                "entity_count": count,
                "url": settings.QDRANT_URL
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "url": settings.QDRANT_URL
            }

    async def insert_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[str]:
        ids: List[str] = []
        if not embeddings_data:
            return ids
        points: List[PointStruct] = []
        for data in embeddings_data:
            payload = {
                "document_id": data.get("document_id"),
                "chunk_id": data.get("chunk_id"),
                "text": data.get("text")
            }
            # parse metadata JSON if present
            try:
                meta = data.get("metadata")
                if meta:
                    payload.update(json.loads(meta))
            except Exception:
                pass
            vector = data.get("embedding")
            pid = data.get("id")
            # Create point with vector field (not vectors)
            points.append(PointStruct(
                id=pid,
                vector=vector,  # Use vector instead of vectors
                payload=payload
            ))
            ids.append(pid)
        # Upsert points
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        return ids

    async def search_similar(self, query_embedding: List[float], limit: int = 5, similarity_cutoff: float = 0.6) -> List[Dict[str, Any]]:
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,  # Use query_vector directly
            limit=limit,
            with_payload=True
        )
        formatted: List[Dict[str, Any]] = []
        for hit in results:
            score = hit.score
            if score is not None and score < similarity_cutoff:
                continue
            payload = hit.payload or {}
            formatted.append({
                "document_id": payload.get("document_id"),
                "chunk_id": payload.get("chunk_id"),
                "text": payload.get("text"),
                "metadata": payload,
                "score": score
            })
        return formatted

    async def delete_by_document_id(self, document_id: str) -> bool:
        try:
            filt = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
            self.client.delete(collection_name=self.collection_name, filter=filt)
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from Qdrant: {e}")
            return False

    async def delete_vectors(self, vector_ids: List[str]) -> bool:
        try:
            self.client.delete(collection_name=self.collection_name, points=vector_ids)
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            return False

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        try:
            filt = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
            items = self.client.scroll(collection_name=self.collection_name, filter=filt, with_payload=True)
            chunks: List[Dict[str, Any]] = []
            for hit in items:
                payload = hit.payload or {}
                chunks.append({
                    "id": hit.id,
                    "chunk_id": payload.get("chunk_id"),
                    "text": payload.get("text")
                })
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks for document {document_id} from Qdrant: {e}")
            return []

    def disconnect(self):
        # QdrantClient does not require explicit disconnect
        pass

# Factory to select vector DB implementation

def get_vector_db():
    """Return the configured vector database client instance"""
    vtype = settings.VECTOR_DB_TYPE.lower()
    if vtype == "zilliz":
        return MilvusDB()
    elif vtype == "qdrant":
        return QdrantDB()
    else:
        raise ValueError(f"Unsupported vector DB type: {settings.VECTOR_DB_TYPE}")