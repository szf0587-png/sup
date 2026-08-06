"""User-isolated chat service using OpenAI-compatible provider APIs."""
from __future__ import annotations

import base64
import hashlib
import uuid
from urllib.parse import urlparse

import requests
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.ai_chat import AIConversation, AIMessage, AIProviderConfig
from server.models.user import User

SYSTEM_PROMPT = "You are a land-resource assessment decision agent. Use only the supplied workbench evidence when making a recommendation. State missing data or unfinished analysis clearly. Do not invent scores, spatial facts, or regulatory conclusions. Give a concise next action, rationale, and confidence limitation."


def _cipher() -> Fernet:
    import os
    source = os.getenv("CHAT_ENCRYPTION_KEY", "local-development-key-change-before-deployment")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(source.encode("utf-8")).digest()))


def _validate_base_url(base_url: str) -> str:
    value = base_url.rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise HTTPException(status_code=422, detail="AI provider URL must use HTTPS")
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise HTTPException(status_code=422, detail="Local AI provider URLs are not allowed")
    return value


class AIChatService:
    def __init__(self, db: Session, user: User):
        self.db, self.user = db, user

    def save_provider(self, provider: str, base_url: str, model: str, api_key: str) -> AIProviderConfig:
        if not api_key.strip():
            raise HTTPException(status_code=422, detail="API Key is required")
        config = self.db.query(AIProviderConfig).filter_by(user_id=self.user.id, provider=provider).first()
        if not config:
            config = AIProviderConfig(id=f"aip_{uuid.uuid4().hex[:16]}", user_id=self.user.id, provider=provider)
            self.db.add(config)
        config.base_url, config.model = _validate_base_url(base_url), model.strip()
        config.encrypted_api_key = _cipher().encrypt(api_key.strip().encode("utf-8")).decode("ascii")
        config.is_active = True
        self.db.commit(); self.db.refresh(config)
        return config

    def list_providers(self) -> list[dict]:
        configs = self.db.query(AIProviderConfig).filter_by(user_id=self.user.id, is_active=True).order_by(AIProviderConfig.provider).all()
        return [{"provider": c.provider, "base_url": c.base_url, "model": c.model, "key_configured": True} for c in configs]

    def create_conversation(self, title: str) -> AIConversation:
        item = AIConversation(id=f"chat_{uuid.uuid4().hex[:16]}", user_id=self.user.id, title=(title.strip() or "新对话")[:100])
        self.db.add(item); self.db.commit(); self.db.refresh(item)
        return item

    def list_conversations(self) -> list[AIConversation]:
        return self.db.query(AIConversation).filter_by(user_id=self.user.id).order_by(AIConversation.updated_at.desc()).all()

    def _conversation(self, conversation_id: str) -> AIConversation:
        item = self.db.query(AIConversation).filter_by(id=conversation_id, user_id=self.user.id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return item

    def messages(self, conversation_id: str) -> list[AIMessage]:
        self._conversation(conversation_id)
        return self.db.query(AIMessage).filter_by(conversation_id=conversation_id).order_by(AIMessage.created_at).all()

    def send_message(self, conversation_id: str, content: str, provider: str, context: str = "") -> AIMessage:
        conversation = self._conversation(conversation_id)
        config = self.db.query(AIProviderConfig).filter_by(user_id=self.user.id, provider=provider, is_active=True).first()
        if not config:
            raise HTTPException(status_code=422, detail="Configure this provider API Key before sending a message")
        content = content.strip()
        if not content:
            raise HTTPException(status_code=422, detail="Message is required")
        history = self.messages(conversation_id)[-12:]
        user_message = AIMessage(id=f"msg_{uuid.uuid4().hex[:16]}", conversation_id=conversation.id, role="user", content=content)
        decision_context = context.strip()[:12000]
        system_content = SYSTEM_PROMPT + (f"\n\nCURRENT WORKBENCH EVIDENCE:\n{decision_context}" if decision_context else "")
        payload = {"model": config.model, "messages": [{"role": "system", "content": system_content}] + [{"role": m.role, "content": m.content} for m in history] + [{"role": "user", "content": content}], "temperature": 0.3}
        try:
            key = _cipher().decrypt(config.encrypted_api_key.encode("ascii")).decode("utf-8")
            response = requests.post(f"{config.base_url}/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=45)
            response.raise_for_status(); data = response.json(); answer = data["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, ValueError, KeyError, IndexError) as error:
            raise HTTPException(status_code=502, detail=f"AI provider request failed: {str(error)[:160]}") from error
        usage = data.get("usage") or {}
        assistant = AIMessage(id=f"msg_{uuid.uuid4().hex[:16]}", conversation_id=conversation.id, role="assistant", content=answer, provider=config.provider, model=config.model, prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"))
        self.db.add_all([user_message, assistant]); self.db.commit(); self.db.refresh(assistant)
        return assistant
