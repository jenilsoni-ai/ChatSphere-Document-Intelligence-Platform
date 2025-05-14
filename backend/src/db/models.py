import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID  # Or use String if not using PostgreSQL UUID

from .session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Chatbot(Base):
    __tablename__ = 'chatbots'

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)  # Assuming Firebase UID as string
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # Add other fields based on ChatbotBase/ChatbotResponse Pydantic models if needed
    # e.g., settings (JSON?)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    conversations = relationship("Conversation", back_populates="chatbot")

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)  # Assuming Firebase UID as string
    chatbot_id = Column(String, ForeignKey('chatbots.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chatbot = relationship("Chatbot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False, index=True)
    # Assuming 'content' stores the message text
    content = Column(Text, nullable=False)
    # 'is_bot' field as used in analytics.py
    is_bot = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

# You might need to create these tables in your database.
# Consider using Alembic for migrations. 