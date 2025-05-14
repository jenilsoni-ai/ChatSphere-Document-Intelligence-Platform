from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...core.config import settings
import os
import logging
from dotenv import set_key, find_dotenv

logger = logging.getLogger(__name__)

router = APIRouter()

class VectorStoreSettings(BaseModel):
    type: str  # "zilliz" or "qdrant"
    zilliz_uri: Optional[str] = None
    zilliz_api_key: Optional[str] = None
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

@router.get("")
async def get_vector_store_settings():
    """Get current vector store settings"""
    try:
        return {
            "type": settings.VECTOR_DB_TYPE,
            "zilliz_uri": settings.ZILLIZ_URI,
            "zilliz_api_key": "****" if settings.VECTOR_DB_TYPE=="zilliz" else None,
            "qdrant_url": settings.QDRANT_URL,
            "qdrant_api_key": "****" if settings.VECTOR_DB_TYPE=="qdrant" else None
        }
    except Exception as e:
        logger.error(f"Error getting vector store settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def update_vector_store_settings(settings_data: VectorStoreSettings):
    """Update vector store settings"""
    try:
        # Validate settings based on type
        if settings_data.type == "zilliz":
            if not settings_data.zilliz_uri or not settings_data.zilliz_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="Zilliz URI and API key are required for Zilliz Cloud"
                )
        elif settings_data.type == "qdrant":
            if not settings_data.qdrant_url or not settings_data.qdrant_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="Qdrant URL and API key are required for Qdrant"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported vector store type: {settings_data.type}"
            )

        # Update environment variables
        os.environ["VECTOR_DB_TYPE"] = settings_data.type
        if settings_data.type == "zilliz":
            os.environ["ZILLIZ_URI"] = settings_data.zilliz_uri
            os.environ["ZILLIZ_API_KEY"] = settings_data.zilliz_api_key
        else:  # qdrant
            os.environ["QDRANT_URL"] = settings_data.qdrant_url
            os.environ["QDRANT_API_KEY"] = settings_data.qdrant_api_key
        
        # Persist changes to .env so they survive restarts
        env_file = find_dotenv() or ".env"
        set_key(env_file, "VECTOR_DB_TYPE", settings_data.type)
        if settings_data.type == "zilliz":
            set_key(env_file, "ZILLIZ_URI", settings_data.zilliz_uri)
            set_key(env_file, "ZILLIZ_API_KEY", settings_data.zilliz_api_key)
        else:
            set_key(env_file, "QDRANT_URL", settings_data.qdrant_url)
            set_key(env_file, "QDRANT_API_KEY", settings_data.qdrant_api_key)
        
        # Reload settings to pick up persisted values
        settings.reload()
        
        # Log the update
        logger.info(f"Updated vector store settings: type={settings_data.type}")
        
        return {"message": "Vector store settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating vector store settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 