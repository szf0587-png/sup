"""Project-scoped management for the current user's published iServer assets."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.api.auth import get_current_user
from server.database import get_db
from server.integrations import iserver_client
from server.models.iserver_service import IServerService
from server.models.project import Project
from server.models.user import User
from server.schemas.iserver_asset import AssetImportRequest, AssetListResponse

router = APIRouter(prefix="/api/projects/{project_id}/iserver-assets", tags=["iserver-assets"])


def _owned_project(project_id: str, current_user: User, db: Session) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.is_deleted.is_(False))
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此项目")
    return project


def _asset_payload(asset: IServerService) -> dict:
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "service_name": asset.service_name,
        "service_type": asset.service_type,
        "datasource_name": asset.datasource_name,
        "dataset_name": asset.dataset_name,
        "service_url": asset.service_url,
        "is_active": asset.is_active,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }


@router.get("", response_model=AssetListResponse, summary="列出当前项目的 iServer 数据")
def list_project_assets(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project(project_id, current_user, db)
    assets = (
        db.query(IServerService)
        .filter(
            IServerService.project_id == project_id,
            IServerService.user_id == current_user.id,
            IServerService.is_deleted.is_(False),
        )
        .order_by(IServerService.updated_at.desc())
        .all()
    )
    return {
        "project_id": project_id,
        "total": len(assets),
        "assets": [_asset_payload(asset) for asset in assets],
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="登记当前项目的 iServer 数据")
@router.post("/import", response_model=dict, status_code=status.HTTP_201_CREATED, summary="导入当前项目的 iServer 数据")
def import_project_asset(
    project_id: str,
    request: AssetImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project(project_id, current_user, db)
    duplicate = (
        db.query(IServerService)
        .filter(
            IServerService.project_id == project_id,
            IServerService.user_id == current_user.id,
            IServerService.service_name == request.service_name,
            IServerService.is_deleted.is_(False),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="项目中已存在同名 iServer 数据")

    asset = IServerService(
        id=f"service_{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        project_id=project_id,
        service_name=request.service_name,
        service_type=request.service_type,
        datasource_name=request.datasource_name,
        dataset_name=request.dataset_name,
        service_url=request.service_url,
        service_config=request.service_config,
        is_active=True,
        is_deleted=False,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"status": "registered", "asset": _asset_payload(asset)}


@router.get("/{asset_id}/metadata", summary="获取 iServer 数据元数据")
def get_project_asset_metadata(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = _get_owned_asset(project_id, asset_id, current_user, db)
    datasets = iserver_client.list_data_datasets(asset.datasource_name)
    return {
        "asset": _asset_payload(asset),
        "datasets": datasets,
        "source": "iserver" if datasets else "unavailable",
    }


@router.get("/{asset_id}/preview", summary="预览 iServer 数据")
def preview_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = _get_owned_asset(project_id, asset_id, current_user, db)
    if asset.service_type not in {"data", "feature"}:
        return {"asset": _asset_payload(asset), "preview": None, "message": "该服务类型暂无要素预览"}
    preview = iserver_client.get_data_service(asset.datasource_name, asset.dataset_name, max_features=100)
    if preview is None:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="iServer 数据预览不可用")
    return {"asset": _asset_payload(asset), "preview": preview}


@router.delete("/{asset_id}", summary="删除项目中的 iServer 数据")
def delete_project_asset(
    project_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = _get_owned_asset(project_id, asset_id, current_user, db)
    if not iserver_client.delete_service(asset.service_name):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="iServer 服务删除失败，未修改本地记录")

    asset.is_deleted = True
    asset.is_active = False
    db.commit()
    return {"status": "deleted", "asset_id": asset.id}


def _get_owned_asset(project_id: str, asset_id: str, current_user: User, db: Session) -> IServerService:
    _owned_project(project_id, current_user, db)
    asset = (
        db.query(IServerService)
        .filter(
            IServerService.id == asset_id,
            IServerService.project_id == project_id,
            IServerService.user_id == current_user.id,
            IServerService.is_deleted.is_(False),
        )
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="iServer 数据不存在或无权访问")
    return asset
