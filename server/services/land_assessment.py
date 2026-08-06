"""Land-resource assessment orchestration backed by published iServer data."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from server.config import DATA_DIR
from server.integrations import iserver_client
from server.services.spatial_analysis import (
    DEFAULT_CONSTRAINT_LAYERS,
    DEFAULT_ROAD_LAYERS,
    administrative_context,
    compute_buffer_stats,
    geometry_area_km2,
    overlay_constraint_stats,
    road_accessibility,
)


AVAILABLE_COMPONENTS = {"buffer", "water_constraint", "road_access", "admin_context", "land_summary"}


def _normalize_geometry(boundary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(boundary, dict):
        raise ValueError("boundary must be a GeoJSON object")
    if boundary.get("type") == "Feature":
        boundary = boundary.get("geometry") or {}
    elif boundary.get("type") == "FeatureCollection":
        features = boundary.get("features") or []
        boundary = (features[0] or {}).get("geometry") if features else {}
    if boundary.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("boundary must be Polygon or MultiPolygon")
    return boundary


def _merge_visualizations(*results: dict[str, Any]) -> dict[str, Any]:
    features = []
    for result in results:
        visualization = result.get("visualization") or {}
        features.extend(visualization.get("features") or [])
    return {"type": "FeatureCollection", "features": features}


def diagnose_land_component(
    component: str,
    boundary: dict[str, Any],
    target_use: str = "general",
    buffer_distance_m: float = 1000,
    constraint_datasets: Optional[list[str]] = None,
    accessibility_layers: Optional[list[dict[str, Any]]] = None,
    scene_name: Optional[str] = None,
    use_3d: bool = False,
) -> dict[str, Any]:
    """Execute exactly one real spatial operation and return its map geometry."""
    del target_use, scene_name, use_3d
    if component not in AVAILABLE_COMPONENTS:
        raise ValueError(f"unsupported assessment component: {component}")
    geometry = _normalize_geometry(boundary)

    if component == "buffer":
        result = compute_buffer_stats(geometry, buffer_distance_m)
    elif component == "water_constraint":
        result = overlay_constraint_stats(geometry, constraint_datasets)
    elif component == "road_access":
        result = road_accessibility(geometry, accessibility_layers)
    elif component == "admin_context":
        result = administrative_context(geometry)
    else:
        result = {
            "boundary_area_km2": round(geometry_area_km2(geometry), 3),
            "source": "calculated:geojson",
            "visualization": {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "geometry": geometry, "properties": {"operation": "land_summary"}}],
            },
            "note": "Boundary area is an approximate geographic area for planning display, not a cadastral measurement.",
        }

    return {
        "component": component,
        "status": "completed",
        "source": result.get("source"),
        "summary": {key: value for key, value in result.items() if key != "visualization"},
        "visualization": result.get("visualization", {"type": "FeatureCollection", "features": []}),
        "result": {component: result},
    }


def evaluate_land_resource(
    boundary: dict[str, Any],
    target_use: str = "general",
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    buffer_distance_m: float = 1000,
    constraint_datasets: Optional[list[str]] = None,
    accessibility_layers: Optional[list[dict[str, Any]]] = None,
    scene_name: Optional[str] = None,
    use_3d: bool = False,
    weights: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """Build an evidence package from the published layers, without proxy scores."""
    del scene_name, use_3d, weights
    geometry = _normalize_geometry(boundary)
    buffer = compute_buffer_stats(geometry, buffer_distance_m)
    water = overlay_constraint_stats(geometry, constraint_datasets)
    roads = road_accessibility(geometry, accessibility_layers)
    admin = administrative_context(geometry)
    run_id = f"land-{uuid.uuid4().hex[:10]}"
    result = {
        "run_id": run_id,
        "status": "completed",
        "data_mode": "iserver",
        "project_id": project_id,
        "user_id": user_id,
        "target_use": target_use,
        "overall_score": 0.0,
        "grade": "N/A",
        "decision": "Evidence package completed",
        "summary": "Water, road, administrative, and buffer evidence was queried from published iServer services. A suitability grade requires published land-use and DEM datasets.",
        "factors": [],
        "spatial": {
            "boundary_area_km2": round(geometry_area_km2(geometry), 3),
            "buffer": buffer,
            "water_constraint": water,
            "road_access": roads,
            "admin_context": admin,
        },
        "three_d": {"enabled": False, "scene_count": 0, "scenes": [], "source": "not_published"},
        "recommendations": [
            "Publish a land-use or land-cover layer before making a land-use suitability classification.",
            "Publish a projected DEM and terrain-analysis service before calculating slope or elevation constraints.",
            "Publish a Realspace service before enabling 3D verification.",
        ],
        "visualization": _merge_visualizations(buffer, water, roads, admin),
        "report_path": None,
    }
    snapshot_path = _write_snapshot(run_id, result)
    result["snapshot_path"] = str(snapshot_path)
    return result


def list_land_assessment_capabilities() -> dict[str, Any]:
    """Report only capabilities which are currently published by this iServer."""
    online = iserver_client.check_iserver()
    basemaps = iserver_client.list_basemap_services() if online else []
    china_datasets = iserver_client.list_data_datasets("China100") if online else []
    realspace_services = iserver_client.list_realspace_services() if online else []
    spatial_analyst = iserver_client.has_spatial_analyst_service() if online else False
    available = set(china_datasets)
    dem_available = any(name in available for name in {"GridToDEMCache", "DEM", "LuonanDEM"}) or any(
        bool(scene.get("terrain_available"))
        for scene in realspace_services
        if isinstance(scene, dict)
    )
    water_available = any(layer["dataset"] in available for layer in DEFAULT_CONSTRAINT_LAYERS)
    road_available = any(layer["dataset_name"] in available for layer in DEFAULT_ROAD_LAYERS)
    admin_available = "Province_R" in available
    tool_availability = {
        "land_summary": {"available": True, "reason": "使用当前边界进行本地面积统计"},
        "water_constraint": {"available": water_available, "reason": "需要已发布的 China100 水体数据服务"},
        "buffer": {"available": spatial_analyst, "reason": "需要已发布的 iServer Spatial Analyst 服务"},
        "road_access": {"available": road_available, "reason": "需要已发布的 China100 道路数据服务"},
        "admin_context": {"available": admin_available, "reason": "需要已发布的 China100 行政区数据服务"},
    }
    return {
        "iServer": online,
        "spatial_analyst": spatial_analyst,
        "basemaps": basemaps,
        "recommended_basemap": basemaps[0] if basemaps else None,
        "land_layers": {
            "water": [layer for layer in DEFAULT_CONSTRAINT_LAYERS if layer["dataset"] in available],
            "roads": [layer for layer in DEFAULT_ROAD_LAYERS if layer["dataset_name"] in available],
            "administrative": ([{"datasource": "China100", "dataset": "Province_R", "label": "Provinces"}] if admin_available else []),
        },
        "published_datasets": china_datasets,
        "dem_available": dem_available,
        "realspace_available": bool(realspace_services),
        "3d_scenes": realspace_services,
        "tool_availability": tool_availability,
        "unavailable": [
            item for item, enabled in {
                "DEM terrain analysis": dem_available,
                "land-use suitability classification": False,
                "3D Realspace verification": not bool(realspace_services),
            }.items() if not enabled
        ],
        "components": sorted(AVAILABLE_COMPONENTS),
    }


def load_land_assessment(run_id: str) -> dict[str, Any] | None:
    path = DATA_DIR / "snapshots" / f"land_{run_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_snapshot(run_id: str, result: dict[str, Any]) -> Path:
    directory = DATA_DIR / "snapshots"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"land_{run_id}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
