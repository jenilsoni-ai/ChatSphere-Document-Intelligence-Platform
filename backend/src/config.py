from pydantic_settings import BaseSettings
import os
from typing import Optional
import logging

class Settings(BaseSettings):
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # Firebase settings
    # Allow loading from GOOGLE_APPLICATION_CREDENTIALS env var OR FIREBASE_CREDENTIALS in .env file
    # MODIFY: FIREBASE_CREDENTIALS: Optional[str] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    FIREBASE_CREDENTIALS: Optional[str] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None) # Keep trying env var first
    # BaseSettings will load from .env if the above is None and FIREBASE_CREDENTIALS is in .env
    FIREBASE_STORAGE_BUCKET: Optional[str] = None

    # Vector store settings
    ZILLIZ_URI: str
    ZILLIZ_API_KEY: str
    ZILLIZ_COLLECTION_NAME: str = "document_embeddings"

    # LLM settings
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama3-70b-8192"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024

    # Embedding settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Firecrawl settings
    FIRECRAWL_API_KEY: str

    class Config:
        env_file = ".env"
        # env_file_encoding = 'utf-8' # Optional: specify encoding if needed
        case_sensitive = True

settings = Settings()

# Add a check and log after loading settings
logger = logging.getLogger(__name__)
if settings.FIREBASE_CREDENTIALS:
    logger.info(f"Firebase credentials loaded from: {settings.FIREBASE_CREDENTIALS}")
    if not os.path.exists(settings.FIREBASE_CREDENTIALS):
        logger.error(f"Firebase credentials file specified but not found at path: {settings.FIREBASE_CREDENTIALS}")
elif not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    logger.warning("Firebase credentials not found via GOOGLE_APPLICATION_CREDENTIALS env var or FIREBASE_CREDENTIALS in .env file.")
else: # Only GOOGLE_APPLICATION_CREDENTIALS was set
    logger.info(f"Firebase credentials loaded from GOOGLE_APPLICATION_CREDENTIALS environment variable.") 