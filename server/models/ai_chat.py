"""Per-user AI provider settings and conversation history."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from server.database import Base


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_configs"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    model = Column(String, nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIMessage(Base):
    __tablename__ = "ai_messages"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
