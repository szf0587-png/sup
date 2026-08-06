from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from server.api.auth import get_current_user
from server.database import get_db
from server.models.user import User
from server.schemas.ai_chat import ConversationRequest, MessageRequest, ProviderRequest, conversation_payload, message_payload
from server.services.ai_chat_service import AIChatService

router = APIRouter(prefix="/api/ai", tags=["ai-chat"])

@router.get("/providers")
def providers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"providers": AIChatService(db, current_user).list_providers()}

@router.put("/providers")
def save_provider(request: ProviderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = AIChatService(db, current_user).save_provider(**request.model_dump())
    return {"provider": item.provider, "base_url": item.base_url, "model": item.model, "key_configured": True}

@router.get("/conversations")
def conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"conversations": [conversation_payload(item) for item in AIChatService(db, current_user).list_conversations()]}

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(request: ConversationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"conversation": conversation_payload(AIChatService(db, current_user).create_conversation(request.title))}

@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"messages": [message_payload(item) for item in AIChatService(db, current_user).messages(conversation_id)]}

@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(conversation_id: str, request: MessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"message": message_payload(AIChatService(db, current_user).send_message(conversation_id, **request.model_dump()))}
