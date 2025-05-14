import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from functools import lru_cache

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Chatbot Platform API"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    
    # Firebase settings
    FIREBASE_CREDENTIALS: Optional[str] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    FIREBASE_API_KEY: Optional[str] = None
    FIREBASE_AUTH_DOMAIN: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_DATABASE_URL: Optional[str] = None
    
    # Vector Database settings
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "zilliz")  # Options: "zilliz" or "qdrant"
    
    # Zilliz Cloud settings
    ZILLIZ_URI: Optional[str] = os.getenv("ZILLIZ_URI")
    ZILLIZ_API_KEY: Optional[str] = os.getenv("ZILLIZ_API_KEY")
    ZILLIZ_COLLECTION_NAME: str = "document_embeddings"
    
    # Qdrant settings
    QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = "document_embeddings"
    
    # LLM settings
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "mixtral-8x7b-32768"
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7
    
    # Embedding settings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    
    # Document processing settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Firecrawl settings
    FIRECRAWL_API_KEY: Optional[str] = None
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def reload(self):
        """Reload settings from environment variables."""
        new_settings = Settings()
        # Copy all fields from the new instance
        for key, value in new_settings.model_dump().items():
            setattr(self, key, value)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()