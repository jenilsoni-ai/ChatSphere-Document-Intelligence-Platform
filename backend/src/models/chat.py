from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[Dict[str, Any]]] = None

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chatbotId: str
    userId: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = []

class SavedSession(BaseModel):
    id: str
    chatbotId: str
    userId: str
    messages: List[ChatMessage] = []

# Request models
class ChatSessionCreate(BaseModel):
    chatbotId: str

class MessageCreate(BaseModel):
    content: str

# Response models
class ChatSessionResponse(BaseModel):
    id: str
    chatbotId: str
    createdAt: datetime
    updatedAt: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None