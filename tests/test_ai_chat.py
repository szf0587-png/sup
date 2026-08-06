import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.database import Base
from server.models.user import User
from server.services.ai_chat_service import AIChatService


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def user(user_id: str) -> User:
    return User(id=user_id, username=user_id, email=f"{user_id}@example.test", password_hash="hash")


def test_provider_key_is_masked_and_isolated_by_user(db):
    owner, other = user("owner"), user("other")
    db.add_all([owner, other])
    db.commit()

    AIChatService(db, owner).save_provider("openai", "https://api.openai.com/v1", "gpt-4o-mini", "sk-test-secret")

    assert AIChatService(db, owner).list_providers() == [{
        "provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key_configured": True
    }]
    assert AIChatService(db, other).list_providers() == []


def test_conversation_access_is_isolated_by_user(db):
    owner, other = user("owner"), user("other")
    db.add_all([owner, other])
    db.commit()
    conversation = AIChatService(db, owner).create_conversation("项目咨询")

    with pytest.raises(HTTPException) as error:
        AIChatService(db, other).messages(conversation.id)

    assert error.value.status_code == 404


def test_chat_requires_a_configured_key(db):
    owner = user("owner")
    db.add(owner)
    db.commit()
    conversation = AIChatService(db, owner).create_conversation("项目咨询")

    with pytest.raises(HTTPException) as error:
        AIChatService(db, owner).send_message(conversation.id, "请介绍平台", "openai")

    assert error.value.status_code == 422
