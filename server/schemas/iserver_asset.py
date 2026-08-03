"""Request and response models for project-scoped iServer assets."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AssetImportRequest(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=160)
    service_type: str = Field("data", pattern="^(data|map|feature|3d)$")
    datasource_name: str = Field(..., min_length=1, max_length=160)
    dataset_name: str = Field(..., min_length=1, max_length=160)
    service_url: Optional[str] = None
    service_config: Optional[dict[str, Any]] = None


class AssetItem(BaseModel):
    id: str
    project_id: str
    service_name: str
    service_type: str
    datasource_name: str
    dataset_name: str
    service_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssetListResponse(BaseModel):
    project_id: str
    total: int
    assets: list[AssetItem]

