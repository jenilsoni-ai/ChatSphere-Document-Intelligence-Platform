from typing import List, Dict, Any, Optional
import numpy as np

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from ..core.config import settings

class EmbeddingService:
    def __init__(self):
        """Initialize the embedding service with HuggingFace embedding model"""
        self.embeddings = HuggingFaceEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Generate embeddings using HuggingFace model
            embeddings = self.embeddings.get_text_embedding_batch(texts)
            return embeddings
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Generate embedding using HuggingFace model
            embedding = self.embeddings.get_text_embedding(text)
            return embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            raise Exception(f"Failed to compute similarity: {str(e)}")