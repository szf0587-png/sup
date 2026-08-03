"""Project-scoped iServer asset lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from server.api.auth import get_current_user
from server.database import get_db
from server.integrations import iserver_client
from server.models.iserver_service import IServerService
from server.models.user import User
from server.schemas.iserver_asset import AssetImportRequest, AssetListResponse
from server.services.iserver_asset_service import IServerAssetService

router = APIRouter(prefix="/api/projects/{project_id}/iserver-assets", tags=["iserver-assets"])


def _asset_payload(asset: IServerService) -> dict:
    """Return public lifecycle data only, never Manager credentials or tokens."""
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "service_name": asset.service_name,
        "service_type": asset.service_type,
        "datasource_name": asset.datasource_name,
        "dataset_name": asset.dataset_name,
        "service_url": asset.service_url,
        "is_active": asset.is_active,
        "lifecycle_status": asset.lifecycle_status,
        "published_at": asset.published_at,
        "unpublished_at": asset.unpublished_at,
        "last_error": asset.last_error,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }


@router.get("", response_model=AssetListResponse)
def list_project_assets(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IServerAssetService(db, current_user)
    service._owned_project(project_id)
    assets = db.query(IServerService).filter(
        IServerService.project_id == project_id,
        IServerService.user_id == current_user.id,
        IServerService.is_deleted.is_(False),
    ).order_by(IServerService.updated_at.desc()).all()
    return {"project_id": project_id, "total": len(assets), "assets": [_asset_payload(asset) for asset in assets]}


@router.post("/import", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def import_project_asset(
    project_id: str,
    request: AssetImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = IServerAssetService(db, current_user).import_dataset(project_id, request.dataset_id)
    return {"status": "imported", "asset": _asset_payload(asset)}


@router.post("/{asset_id}/publish", response_model=dict)
def publish_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = IServerAssetService(db, current_user).publish(project_id, asset_id)
    return {"status": "published", "asset": _asset_payload(asset)}


@router.post("/{asset_id}/unpublish", response_model=dict)
def unpublish_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = IServerAssetService(db, current_user).unpublish(project_id, asset_id)
    return {"status": "unpublished", "asset": _asset_payload(asset)}


@router.get("/{asset_id}/metadata")
def get_project_asset_metadata(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IServerAssetService(db, current_user)
    asset = service._owned_asset(project_id, asset_id)
    return {"asset": _asset_payload(asset), **service.metadata(project_id, asset_id)}


@router.get("/{asset_id}/preview")
def preview_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IServerAssetService(db, current_user)
    asset = service._owned_asset(project_id, asset_id)
    return {"asset": _asset_payload(asset), "preview": service.preview(project_id, asset_id)}


@router.delete("/{asset_id}")
def delete_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = IServerAssetService(db, current_user).delete(project_id, asset_id)
    return {"status": "deleted", "asset_id": asset.id}


def _get_owned_asset(project_id: str, asset_id: str, current_user: User, db: Session) -> IServerService:
    """Compatibility helper retained for callers that imported the old API module."""
    return IServerAssetService(db, current_user)._owned_asset(project_id, asset_id)
