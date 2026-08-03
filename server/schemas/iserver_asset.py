"""Request and response models for project-scoped iServer assets."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AssetImportRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1, max_length=160)


class AssetItem(BaseModel):
    id: str
    project_id: str
    service_name: str
    service_type: str
    datasource_name: str
    dataset_name: str
    service_url: Optional[str]
    is_active: bool
    lifecycle_status: str
    published_at: Optional[datetime]
    unpublished_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssetListResponse(BaseModel):
    project_id: str
    total: int
    assets: list[AssetItem]
