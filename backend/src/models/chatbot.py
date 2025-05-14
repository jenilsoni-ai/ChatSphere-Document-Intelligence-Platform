from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AppearanceSettings(BaseModel):
    """Model for chatbot appearance settings"""
    primaryColor: str = "#007AFF"
    secondaryColor: str = "#F2F2F7"
    position: str = "bottom-right"
    chatTitle: str = "Chat with our AI"
    showBranding: bool = True
    initialMessage: Optional[str] = None

class ChatbotSettings(BaseModel):
    """Model for chatbot settings"""
    temperature: float = 0.7
    maxTokens: int = 1024
    model: str = "llama3-70b-8192"
    instructions: Optional[str] = None
    role: Optional[str] = None
    appearance: Optional[AppearanceSettings] = None

class ChatbotBase(BaseModel):
    """Base model for chatbot"""
    name: str
    description: Optional[str] = None
    settings: ChatbotSettings = Field(default_factory=ChatbotSettings)
    documents: List[str] = []

class ChatbotCreate(ChatbotBase):
    """Model for chatbot creation"""
    pass

class ChatbotUpdate(BaseModel):
    """Model for chatbot update"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ChatbotSettings] = None
    documents: Optional[List[str]] = None

class ChatbotResponse(ChatbotBase):
    """Model for chatbot response"""
    id: str
    ownerId: str
    createdAt: datetime
    updatedAt: datetime

class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str
    content: str

class PreviewRequest(BaseModel):
    """Model for preview request"""
    message: str
    settings: ChatbotSettings
    chatHistory: List[ChatMessage] = []
    documents: List[str] = Field(default_factory=list, description="List of document IDs to use for context")
    chatbotId: str

class ChatbotDocumentAssign(BaseModel):
    """Model for assigning documents to chatbot"""
    documentIds: List[str]

class Source(BaseModel):
    """Model for document sources"""
    documentId: str
    chunkId: str
    score: float

class PreviewResponse(BaseModel):
    """Model for preview response"""
    response: str
    sources: List[Dict[str, Any]] = []
    rag_status: Optional[str] = None