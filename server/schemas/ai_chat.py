from pydantic import BaseModel, Field

class ProviderRequest(BaseModel):
    provider: str = Field(..., pattern=r"^[a-z0-9_-]{2,32}$")
    base_url: str = Field(..., max_length=300)
    model: str = Field(..., min_length=1, max_length=120)
    api_key: str = Field(..., min_length=8, max_length=500)
class ConversationRequest(BaseModel): title: str = Field(default="新对话", max_length=100)
class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    provider: str = Field(..., pattern=r"^[a-z0-9_-]{2,32}$")
    context: str = Field(default="", max_length=12000)
def conversation_payload(item): return {"id": item.id, "title": item.title, "created_at": item.created_at, "updated_at": item.updated_at}
def message_payload(item): return {"id": item.id, "role": item.role, "content": item.content, "provider": item.provider, "model": item.model, "created_at": item.created_at}
