from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    """Base model for document"""
    name: str
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    """Model for document creation"""
    pass

class DocumentUpdate(BaseModel):
    """Model for document update"""
    name: Optional[str] = None
    description: Optional[str] = None

class Document(DocumentBase):
    """Model for document in database"""
    id: str
    ownerId: str
    fileType: str
    fileSize: int
    uploadedAt: datetime
    createdAt: datetime
    updatedAt: datetime
    processingStatus: str  # 'processing', 'completed', 'failed', or 'ready' for website documents
    storageUri: str
    metadata: Optional[Dict[str, Any]] = None
    vectorIds: Optional[List[str]] = None
    chunkCount: Optional[int] = None
    error: Optional[str] = None

class DocumentResponse(DocumentBase):
    """Model for document response"""
    id: str
    ownerId: str
    fileType: str
    fileSize: int
    uploadedAt: datetime
    processingStatus: str
    chunkCount: Optional[int] = None
    vectorIds: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DocumentUpload(BaseModel):
    """Model for document upload"""
    name: str
    description: Optional[str] = None
    # The actual file will be handled by Form and UploadFile

class DocumentProcessingStatus(BaseModel):
    """Model for document processing status update"""
    processingStatus: str
    chunkCount: Optional[int] = None
    vectorIds: Optional[List[str]] = None