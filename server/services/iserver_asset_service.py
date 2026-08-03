"""Ownership-safe lifecycle operations for project-scoped iServer assets."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.config import DATA_DIR
from server.integrations import iserver_client
from server.models.dataset import Dataset
from server.models.iserver_service import IServerService
from server.models.project import Project
from server.models.user import User


_PUBLISHABLE_SUFFIXES = {".geojson", ".json", ".udbx"}
_SUPPORTED_CRS = {"EPSG:4326", "EPSG:3857"}


class IServerAssetService:
    """Coordinates local asset records with iServer without exposing its credentials."""

    def __init__(self, db: Session, current_user: User, client=iserver_client):
        self.db = db
        self.current_user = current_user
        self.client = client

    def import_dataset(self, project_id: str, dataset_id: str) -> IServerService:
        project = self._owned_project(project_id)
        dataset = self._owned_dataset(project, dataset_id)
        self._validate_publishable_dataset(dataset)
        resource_name = self.resource_name(self.current_user.id, project.id, dataset.name)

        duplicate = self.db.query(IServerService).filter(
            IServerService.service_name == resource_name,
            IServerService.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An iServer resource with this generated name already exists")

        asset = IServerService(
            id=f"service_{uuid.uuid4().hex[:12]}",
            user_id=self.current_user.id,
            project_id=project.id,
            dataset_id=dataset.id,
            service_name=resource_name,
            service_type="data",
            datasource_name=resource_name,
            dataset_name=dataset.name,
            is_active=False,
            is_deleted=False,
            lifecycle_status="imported",
        )
        self.db.add(asset)
        dataset.iserver_service_id = asset.id
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def publish(self, project_id: str, asset_id: str) -> IServerService:
        asset = self._owned_asset(project_id, asset_id)
        dataset = self._asset_dataset(asset)
        result = self.client.publish_dataset_file(
            str(Path(DATA_DIR) / dataset.file_path), asset.service_name, asset.datasource_name
        )
        if result.get("status") not in {"published", "already_exists"}:
            self._record_failure(asset, "publish_failed", result.get("detail") or result.get("status") or "iServer publication failed")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=asset.last_error)

        asset.lifecycle_status = "published"
        asset.is_active = True
        asset.service_url = result.get("service_url") or asset.service_url
        asset.published_at = datetime.now(timezone.utc)
        asset.unpublished_at = None
        asset.last_error = None
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def unpublish(self, project_id: str, asset_id: str) -> IServerService:
        asset = self._owned_asset(project_id, asset_id)
        if asset.lifecycle_status != "published":
            asset.lifecycle_status = "unpublished"
            asset.is_active = False
            asset.unpublished_at = datetime.now(timezone.utc)
            asset.last_error = None
            self.db.commit()
            self.db.refresh(asset)
            return asset

        result = self.client.unpublish_service(asset.service_name)
        if result.get("status") not in {"unpublished", "not_found"}:
            self._record_failure(asset, "unpublish_failed", result.get("detail") or result.get("status") or "iServer unpublish failed")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=asset.last_error)

        asset.lifecycle_status = "unpublished"
        asset.is_active = False
        asset.unpublished_at = datetime.now(timezone.utc)
        asset.last_error = None
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def preview(self, project_id: str, asset_id: str) -> dict:
        asset = self._owned_asset(project_id, asset_id)
        if asset.lifecycle_status != "published":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset must be published before it can be previewed")
        preview = self.client.get_data_service(asset.datasource_name, asset.dataset_name, max_features=100)
        if preview is None:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="iServer preview is unavailable")
        return preview

    def metadata(self, project_id: str, asset_id: str) -> dict:
        asset = self._owned_asset(project_id, asset_id)
        dataset = self._asset_dataset(asset, required=False)
        local_metadata = {
            "dataset_id": dataset.id,
            "dataset_type": dataset.dataset_type,
            "crs": dataset.crs,
            "bounds": dataset.bounds,
            "extra_metadata": dataset.extra_metadata,
        } if dataset else None
        if asset.lifecycle_status != "published":
            return {"source": "local", "metadata": local_metadata, "datasets": []}
        datasets = self.client.list_data_datasets(asset.datasource_name)
        return {"source": "iserver" if datasets else "local", "metadata": local_metadata, "datasets": datasets}

    def delete(self, project_id: str, asset_id: str) -> IServerService:
        asset = self._owned_asset(project_id, asset_id)
        requires_remote_delete = asset.lifecycle_status == "published" or (asset.dataset_id is None and asset.is_active)
        if requires_remote_delete:
            result = self.client.unpublish_service(asset.service_name)
            if result.get("status") not in {"unpublished", "not_found"}:
                self._record_failure(asset, "delete_failed", result.get("detail") or result.get("status") or "iServer delete failed")
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=asset.last_error)

        asset.is_deleted = True
        asset.is_active = False
        asset.lifecycle_status = "deleted"
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def _owned_project(self, project_id: str) -> Project:
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == self.current_user.id,
            Project.is_deleted.is_(False),
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def _owned_dataset(self, project: Project, dataset_id: str) -> Dataset:
        dataset = self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == self.current_user.id,
            Dataset.is_deleted.is_(False),
        ).first()
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        if dataset.id not in (project.dataset_ids or []):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Dataset is not assigned to this project")
        return dataset

    def _owned_asset(self, project_id: str, asset_id: str) -> IServerService:
        self._owned_project(project_id)
        asset = self.db.query(IServerService).filter(
            IServerService.id == asset_id,
            IServerService.project_id == project_id,
            IServerService.user_id == self.current_user.id,
            IServerService.is_deleted.is_(False),
        ).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="iServer asset not found")
        return asset

    def _asset_dataset(self, asset: IServerService, required: bool = True) -> Dataset | None:
        if not asset.dataset_id:
            if required:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset is not linked to an uploaded dataset")
            return None
        dataset = self.db.query(Dataset).filter(
            Dataset.id == asset.dataset_id,
            Dataset.user_id == self.current_user.id,
            Dataset.is_deleted.is_(False),
        ).first()
        if not dataset and required:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    def _validate_publishable_dataset(self, dataset: Dataset) -> None:
        suffix = Path(dataset.file_path).suffix.lower()
        if dataset.dataset_type != "vector" or suffix not in _PUBLISHABLE_SUFFIXES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Only GeoJSON or UDBX vector datasets can be published")
        if (dataset.crs or "").upper() not in _SUPPORTED_CRS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Dataset CRS must be EPSG:4326 or EPSG:3857")

    def _record_failure(self, asset: IServerService, lifecycle_status: str, detail: str) -> None:
        asset.lifecycle_status = lifecycle_status
        asset.is_active = False
        asset.last_error = detail[:500]
        self.db.commit()
        self.db.refresh(asset)

    @staticmethod
    def resource_name(user_id: str, project_id: str, dataset_name: str) -> str:
        def clean(value: str, limit: int) -> str:
            value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
            return (value[:limit] or "asset").rstrip("_")

        return f"u_{clean(user_id, 8)}_p_{clean(project_id, 8)}_{clean(dataset_name, 96)}"
