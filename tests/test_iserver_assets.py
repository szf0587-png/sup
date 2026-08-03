"""Tests for project-scoped iServer asset management."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from server.database import Base
from server.models.user import User
from server.models.project import Project
from server.models.iserver_service import IServerService
from server.api import iserver_assets
from server.main import app


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _user(user_id: str, username: str) -> User:
    return User(
        id=user_id,
        username=username,
        email=f"{username}@example.test",
        password_hash="hash",
        role="user",
        is_active=True,
    )


def test_list_project_assets_isolated_by_user(db):
    owner = _user("user_owner", "owner")
    other = _user("user_other", "other")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    db.add_all([
        owner,
        other,
        project,
        IServerService(
            id="service_owner",
            user_id=owner.id,
            project_id=project.id,
            service_name="data-owner",
            service_type="data",
            datasource_name="owner_ds",
            dataset_name="owner_layer",
            is_active=True,
        ),
        IServerService(
            id="service_other",
            user_id=other.id,
            project_id=project.id,
            service_name="data-other",
            service_type="data",
            datasource_name="other_ds",
            dataset_name="other_layer",
            is_active=True,
        ),
    ])
    db.commit()

    result = iserver_assets.list_project_assets(project.id, owner, db)

    assert [item["id"] for item in result["assets"]] == ["service_owner"]
    assert result["project_id"] == project.id


def test_delete_project_asset_requires_ownership(db, monkeypatch):
    owner = _user("user_owner", "owner")
    other = _user("user_other", "other")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    asset = IServerService(
        id="service_owner",
        user_id=owner.id,
        project_id=project.id,
        service_name="data-owner",
        service_type="data",
        datasource_name="owner_ds",
        dataset_name="owner_layer",
        is_active=True,
    )
    db.add_all([owner, other, project, asset])
    db.commit()

    with pytest.raises(HTTPException) as error:
        iserver_assets.delete_project_asset(project.id, asset.id, other, db)

    assert error.value.status_code == 403


def test_delete_project_asset_removes_remote_service_and_soft_deletes(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    asset = IServerService(
        id="service_owner",
        user_id=owner.id,
        project_id=project.id,
        service_name="data-owner",
        service_type="data",
        datasource_name="owner_ds",
        dataset_name="owner_layer",
        is_active=True,
    )
    db.add_all([owner, project, asset])
    db.commit()
    monkeypatch.setattr(iserver_assets.iserver_client, "delete_service", lambda name: name == "data-owner")

    result = iserver_assets.delete_project_asset(project.id, asset.id, owner, db)

    assert result["status"] == "deleted"
    db.refresh(asset)
    assert asset.is_deleted is True
    assert asset.is_active is False


def test_import_alias_is_exposed_for_submission_contract():
    paths = set(app.openapi()["paths"])
    assert "/api/projects/{project_id}/iserver-assets/import" in paths
