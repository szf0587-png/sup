"""Tests for project-scoped iServer asset management."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from server.database import Base
from server.models.user import User
from server.models.project import Project
from server.models.dataset import Dataset
from server.models.iserver_service import IServerService
from server.api import iserver_assets
from server.main import app
from server.services.iserver_asset_service import IServerAssetService


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

    assert error.value.status_code in {403, 404}


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


def test_publish_and_unpublish_routes_are_exposed():
    paths = set(app.openapi()["paths"])

    assert "/api/projects/{project_id}/iserver-assets/{asset_id}/publish" in paths
    assert "/api/projects/{project_id}/iserver-assets/{asset_id}/unpublish" in paths


def _dataset(user_id: str, dataset_id: str = "dataset_owner", **overrides) -> Dataset:
    values = {
        "id": dataset_id,
        "user_id": user_id,
        "name": "County Boundary",
        "dataset_type": "vector",
        "file_path": "users/user_owner/vector/boundary.geojson",
        "file_size": 10,
        "crs": "EPSG:4326",
        "extra_metadata": {"feature_count": 1},
    }
    values.update(overrides)
    return Dataset(**values)


def test_import_builds_project_and_user_scoped_resource_name(db):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_owner"])
    dataset = _dataset(owner.id)
    db.add_all([owner, project, dataset])
    db.commit()

    asset = IServerAssetService(db, owner).import_dataset(project.id, dataset.id)

    assert asset.service_name == IServerAssetService.resource_name(owner.id, project.id, dataset.name)
    assert asset.dataset_id == dataset.id
    assert asset.lifecycle_status == "imported"
    assert asset.last_error is None


def test_resource_name_uses_full_identifiers_and_hashes_non_ascii_names():
    first = IServerAssetService.resource_name(
        "user_same_prefix_11111111", "project_same_prefix_11111111", "行政区划"
    )
    second = IServerAssetService.resource_name(
        "user_same_prefix_22222222", "project_same_prefix_22222222", "行政区划"
    )
    empty_name = IServerAssetService.resource_name(
        "user_same_prefix_11111111", "project_same_prefix_11111111", ""
    )

    assert first != second
    assert first != empty_name
    assert first.startswith("u_user_same_")
    assert "asset_" in first
    assert first.isascii()


def test_import_rejects_duplicate_generated_resource_name(db):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_a", "dataset_b"])
    first = _dataset(owner.id, "dataset_a", name="County Boundary")
    second = _dataset(owner.id, "dataset_b", name="County Boundary")
    db.add_all([owner, project, first, second])
    db.commit()
    service = IServerAssetService(db, owner)
    service.import_dataset(project.id, first.id)

    with pytest.raises(HTTPException) as error:
        service.import_dataset(project.id, second.id)

    assert error.value.status_code == 409


def test_import_converts_database_resource_name_race_to_conflict(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_owner"])
    dataset = _dataset(owner.id)
    db.add_all([owner, project, dataset])
    db.commit()
    monkeypatch.setattr(db, "commit", lambda: (_ for _ in ()).throw(IntegrityError("insert", {}, Exception("unique"))))

    with pytest.raises(HTTPException) as error:
        IServerAssetService(db, owner).import_dataset(project.id, dataset.id)

    assert error.value.status_code == 409


@pytest.mark.parametrize(
    "dataset_kwargs",
    [
        {"file_path": "users/user_owner/vector/boundary.kml"},
        {"crs": "EPSG:4490"},
    ],
)
def test_import_rejects_unsupported_formats_and_invalid_crs(db, dataset_kwargs):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_owner"])
    dataset = _dataset(owner.id, **dataset_kwargs)
    db.add_all([owner, project, dataset])
    db.commit()

    with pytest.raises(HTTPException) as error:
        IServerAssetService(db, owner).import_dataset(project.id, dataset.id)

    assert error.value.status_code == 422


@pytest.mark.parametrize("failure_status", ["iserver_unreachable", "publish_failed"])
def test_publish_records_failure_and_can_retry(db, monkeypatch, failure_status):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_owner"])
    dataset = _dataset(owner.id)
    db.add_all([owner, project, dataset])
    db.commit()
    service = IServerAssetService(db, owner)
    asset = service.import_dataset(project.id, dataset.id)

    monkeypatch.setattr(service.client, "publish_dataset_file", lambda *_: {"status": failure_status, "detail": "offline"})
    with pytest.raises(HTTPException) as error:
        service.publish(project.id, asset.id)

    assert error.value.status_code == 502
    db.refresh(asset)
    assert asset.lifecycle_status == "publish_failed"
    assert asset.last_error == "offline"

    monkeypatch.setattr(service.client, "publish_dataset_file", lambda *_: {"status": "published", "service_url": "http://iserver/data"})
    published = service.publish(project.id, asset.id)

    assert published.lifecycle_status == "published"
    assert published.service_url == "http://iserver/data"
    assert published.last_error is None
    assert published.published_at is not None


def test_publish_persists_remote_dataset_identifier_used_by_preview(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=["dataset_owner"])
    dataset = _dataset(owner.id)
    db.add_all([owner, project, dataset])
    db.commit()
    service = IServerAssetService(db, owner)
    asset = service.import_dataset(project.id, dataset.id)
    calls = []
    monkeypatch.setattr(service.client, "publish_dataset_file", lambda *_: {
        "status": "published", "service_url": "http://iserver/data", "dataset_name": "boundary_R"
    })
    monkeypatch.setattr(service.client, "get_data_service", lambda datasource, dataset_name, **_: calls.append((datasource, dataset_name)) or {"features": []})

    service.publish(project.id, asset.id)
    preview = service.preview(project.id, asset.id)

    assert asset.dataset_name == "boundary_R"
    assert preview == {"features": []}
    assert calls == [(asset.datasource_name, "boundary_R")]


def test_unpublish_updates_lifecycle_without_disclosing_credentials(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    asset = IServerService(
        id="service_owner",
        user_id=owner.id,
        project_id=project.id,
        service_name="u_user_own_p_project__county_boundary",
        service_type="data",
        datasource_name="u_user_own_p_project__county_boundary",
        dataset_name="County Boundary",
        lifecycle_status="published",
        is_active=True,
    )
    db.add_all([owner, project, asset])
    db.commit()
    service = IServerAssetService(db, owner)
    monkeypatch.setattr(service.client, "unpublish_service", lambda _: {"status": "unpublished"})

    result = service.unpublish(project.id, asset.id)

    assert result.lifecycle_status == "unpublished"
    assert result.unpublished_at is not None
    assert result.is_active is False


def test_unpublish_attempts_remote_cleanup_after_failed_publication(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    asset = IServerService(
        id="service_owner", user_id=owner.id, project_id=project.id,
        service_name="data-owner", service_type="data", datasource_name="owner_ds",
        dataset_name="owner_layer", lifecycle_status="publish_failed", is_active=False,
    )
    db.add_all([owner, project, asset])
    db.commit()
    service = IServerAssetService(db, owner)
    calls = []
    monkeypatch.setattr(service.client, "unpublish_service", lambda name: calls.append(name) or {"status": "not_found"})

    result = service.unpublish(project.id, asset.id)

    assert calls == [asset.service_name]
    assert result.lifecycle_status == "unpublished"


def test_delete_attempts_remote_cleanup_after_failed_publication(db, monkeypatch):
    owner = _user("user_owner", "owner")
    project = Project(id="project_owner", user_id=owner.id, name="Owner project", dataset_ids=[])
    asset = IServerService(
        id="service_owner", user_id=owner.id, project_id=project.id,
        service_name="data-owner", service_type="data", datasource_name="owner_ds",
        dataset_name="owner_layer", lifecycle_status="publish_failed", is_active=False,
    )
    db.add_all([owner, project, asset])
    db.commit()
    service = IServerAssetService(db, owner)
    calls = []
    monkeypatch.setattr(service.client, "unpublish_service", lambda name: calls.append(name) or {"status": "unpublished"})

    result = service.delete(project.id, asset.id)

    assert calls == [asset.service_name]
    assert result.is_deleted is True


@pytest.mark.parametrize("operation", ["preview", "publish", "delete"])
def test_guessed_asset_id_cannot_be_operated_by_another_user(db, operation):
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
    service = IServerAssetService(db, other)

    with pytest.raises(HTTPException) as error:
        getattr(service, operation)(project.id, asset.id)

    assert error.value.status_code in {403, 404}
