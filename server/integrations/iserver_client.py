"""iServer REST API 客户端 — 线程安全 Session + Token 认证 + Manager 发布 API"""
from __future__ import annotations

import threading
import time
import os
from math import cos, radians
from typing import Any
import requests
from server.config import ISERVER_BASE, ISERVER_USER, ISERVER_PASSWORD

_lock = threading.Lock()
_session: requests.Session | None = None
_token: str | None = None
_token_expires: float = 0.0


# ---------------------------------------------------------------------------
# 认证
# ---------------------------------------------------------------------------

def _refresh_token() -> str | None:
    """获取或刷新 iServer Token（有效期 120 分钟，提前 60s 续期）"""
    global _token, _token_expires
    if _token and time.time() < _token_expires - 60:
        return _token
    if not (ISERVER_USER and ISERVER_PASSWORD):
        return None
    try:
        r = requests.post(
            f"{ISERVER_BASE}/iserver/services/security/tokens.json",
            json={
                "username": ISERVER_USER,
                "password": ISERVER_PASSWORD,
                "clientType": "HTTP",
                "expiration": 120,
            },
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            tok = data.get("token")
            if tok:
                _token = tok
                _token_expires = time.time() + 120 * 60
                return _token
        print(f"[iserver] Token 响应非 200: {r.status_code}")
    except Exception as e:
        print(f"[iserver] Token 刷新失败: {e}")
    return None


def _get_session() -> requests.Session:
    """返回全局唯一 Session，每次更新 Token header（线程安全）"""
    global _session
    with _lock:
        if _session is None:
            _session = requests.Session()
            # Local iServer deployments must not inherit a malformed Windows
            # NETRC/proxy configuration from the user's shell environment.
            # Opt in explicitly when a remote deployment needs environment
            # proxy settings.
            _session.trust_env = os.getenv("ISERVER_TRUST_ENV", "0").lower() in {"1", "true", "yes"}
            _session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json",
            })
        token = _refresh_token()
        if token:
            _session.headers.update({"token": token})
            _session.auth = None
        elif ISERVER_USER and ISERVER_PASSWORD:
            _session.auth = (ISERVER_USER, ISERVER_PASSWORD)
    return _session


def reset_session() -> None:
    """强制重建 Session（认证变更后调用）"""
    global _session, _token, _token_expires
    with _lock:
        _session = None
        _token = None
        _token_expires = 0.0


def geojson_to_supermap_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    """Convert GeoJSON geometry to the geometry contract used by iServer REST."""
    if not isinstance(geometry, dict):
        raise ValueError("geometry must be a GeoJSON object")
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if geometry_type == "Point" and len(coordinates) >= 2:
        return {"type": "POINT", "parts": [1], "points": [{"x": coordinates[0], "y": coordinates[1]}]}

    if geometry_type == "LineString":
        rings = [coordinates]
        supermap_type = "LINE"
    elif geometry_type == "MultiLineString":
        rings = coordinates
        supermap_type = "LINE"
    elif geometry_type == "Polygon":
        rings = coordinates
        supermap_type = "REGION"
    elif geometry_type == "MultiPolygon":
        rings = [ring for polygon in coordinates for ring in polygon]
        supermap_type = "REGION"
    else:
        raise ValueError(f"unsupported GeoJSON geometry type: {geometry_type}")

    points = []
    parts = []
    for ring in rings:
        if not ring:
            continue
        parts.append(len(ring))
        points.extend({"x": point[0], "y": point[1]} for point in ring)
    if not points:
        raise ValueError("geometry contains no coordinates")
    return {"type": supermap_type, "parts": parts, "points": points}


def supermap_to_geojson_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    """Convert iServer REST geometry to a GeoJSON geometry for API consumers."""
    if not geometry:
        return {}
    geometry_type = str(geometry.get("type", "")).upper()
    if geometry_type in {"POINT", "POINTM", "POINTZ"}:
        point = (geometry.get("points") or [{}])[0]
        return {"type": "Point", "coordinates": [point.get("x"), point.get("y")]}

    parts = geometry.get("parts") or []
    points = geometry.get("points") or []
    lines = []
    cursor = 0
    for part_size in parts:
        part = points[cursor: cursor + int(part_size)]
        cursor += int(part_size)
        lines.append([[point.get("x"), point.get("y")] for point in part])
    if not lines and points:
        lines = [[[point.get("x"), point.get("y")] for point in points]]

    if geometry_type in {"LINE", "LINEM", "LINEZ"}:
        if len(lines) == 1:
            return {"type": "LineString", "coordinates": lines[0]}
        return {"type": "MultiLineString", "coordinates": lines}
    if geometry_type in {"REGION", "REGIONM", "REGIONZ"}:
        return {"type": "Polygon", "coordinates": lines}
    return geometry


def _fetch_json_resource(resource_url: str | None) -> dict[str, Any]:
    if not resource_url:
        raise ValueError("iServer response did not include a resource URL")
    url = resource_url if resource_url.endswith(".json") else f"{resource_url}.json"
    response = _get_session().get(url, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"iServer result fetch failed ({response.status_code}): {response.text[:300]}")
    return response.json()


def _spatial_analysis_base_url() -> str:
    response = _get_session().get(f"{ISERVER_BASE}/iserver/services.json", timeout=10)
    response.raise_for_status()
    payload = response.json()
    services = payload if isinstance(payload, list) else payload.get("services", [])
    for service in services:
        name = service.get("name", "")
        component = service.get("componentType", "")
        if "spatialAnalysis" in name or component == "SpatialAnalystImpl":
            return f"{ISERVER_BASE}/iserver/services/{name.rstrip('/') }"
    raise RuntimeError("no published Spatial Analyst service was found")


def list_native_spatial_operations() -> dict[str, list[dict[str, Any]]]:
    """Discover the raw operation resources actually published by Spatial Analyst."""
    base_url = f"{_spatial_analysis_base_url().rstrip('/')}/spatialanalyst"
    session = _get_session()
    geometry_response = session.get(f"{base_url}/geometry.json", timeout=20)
    datasets_response = session.get(f"{base_url}/datasets.json", timeout=30)
    geometry_response.raise_for_status()
    datasets_response.raise_for_status()

    geometry = []
    for resource in geometry_response.json() or []:
        path = resource.get("path")
        name = resource.get("name")
        if path and name:
            geometry.append({"id": f"geometry:{name}", "name": name, "path": path, "scope": "geometry"})

    grouped: dict[str, dict[str, Any]] = {}
    for dataset in datasets_response.json() or []:
        dataset_name = dataset.get("name")
        for resource in dataset.get("childResourceInfos") or []:
            name = resource.get("name")
            path = resource.get("path")
            if not (dataset_name and name and path):
                continue
            item = grouped.setdefault(
                name,
                {"id": f"dataset:{name}", "name": name, "scope": "dataset", "datasets": []},
            )
            item["datasets"].append({"name": dataset_name, "path": path})
    return {"geometry_operations": geometry, "dataset_operations": sorted(grouped.values(), key=lambda item: item["name"])}


def execute_native_spatial_operation(
    operation_id: str,
    parameters: dict[str, Any],
    dataset_path: str | None = None,
) -> dict[str, Any]:
    """Execute one discovered Spatial Analyst resource with its native REST payload."""
    catalog = list_native_spatial_operations()
    endpoint = None
    for operation in catalog["geometry_operations"]:
        if operation["id"] == operation_id:
            endpoint = operation["path"]
            break
    if endpoint is None:
        for operation in catalog["dataset_operations"]:
            if operation["id"] != operation_id:
                continue
            for dataset in operation["datasets"]:
                if dataset["path"] == dataset_path:
                    endpoint = dataset_path
                    break
            break
    if endpoint is None:
        raise ValueError("operation or dataset resource is not published by the current iServer")

    url = endpoint if endpoint.endswith(".json") else f"{endpoint}.json"
    response = _get_session().post(url, json=parameters, timeout=90)
    if response.status_code not in (200, 201, 202):
        raise RuntimeError(f"iServer native operation failed ({response.status_code}): {response.text[:500]}")
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text}


def _geometry_centroid_latitude(geometry: dict[str, Any]) -> float:
    converted = geojson_to_supermap_geometry(geometry)
    points = converted.get("points", [])
    if not points:
        return 0.0
    return sum(float(point["y"]) for point in points) / len(points)


# ---------------------------------------------------------------------------
# 基础健康检查
# ---------------------------------------------------------------------------

def check_iserver() -> bool:
    """验证 iServer 是否可达并已授权"""
    try:
        r = _get_session().get(f"{ISERVER_BASE}/iserver/services.json", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_realspace_services() -> list[dict]:
    """列出可用的三维场景服务（realspace / 3D-*）"""
    try:
        r = _get_session().get(f"{ISERVER_BASE}/iserver/services.json", timeout=10)
        if r.status_code != 200:
            return []

        payload = r.json()
        services = payload if isinstance(payload, list) else payload.get("services", [])
        scenes: list[dict] = []

        for service in services:
            service_name = service.get("name", "")
            if not service_name:
                continue
            published_name = service_name.split("/", 1)[0]
            if published_name.startswith("3D-") or published_name.startswith("realspace-"):
                clean_name = published_name.replace("3D-", "", 1).replace("realspace-", "", 1)
                scenes.append({
                    "scene_name": clean_name,
                    "service_name": published_name,
                    "scene_url": f"{ISERVER_BASE}/iserver/services/{published_name}/rest/realspace",
                    "terrain_available": True,
                    "description": service.get("description"),
                })
        return scenes
    except Exception:
        return []


def list_basemap_services() -> list[dict]:
    """列出可用的二维底图服务（map-*）"""
    try:
        r = _get_session().get(f"{ISERVER_BASE}/iserver/services.json", timeout=10)
        if r.status_code != 200:
            return []

        payload = r.json()
        services = payload if isinstance(payload, list) else payload.get("services", [])
        basemaps: list[dict] = []

        for service in services:
            service_name = service.get("name", "")
            if not service_name or not service_name.startswith("map-"):
                continue

            # The service catalog uses names such as ``map-China100/rest``.
            # Keep only the published service id before asking for map metadata.
            published_name = service_name.split("/", 1)[0]
            clean_name = published_name.replace("map-", "", 1)
            info = get_map_service(clean_name)
            maps: list[str] = []
            if isinstance(info, list):
                maps = [m if isinstance(m, str) else m.get("name", "") for m in info]
            elif isinstance(info, dict):
                maps_data = info.get("maps", [])
                maps = [m if isinstance(m, str) else m.get("name", "") for m in maps_data]

            if not maps:
                continue

            target_map = maps[0]
            tile_url = get_map_tile_url(clean_name, target_map)
            if not tile_url:
                continue

            basemaps.append({
                "id": f"iserver-{clean_name}",
                "name": service.get("description") or clean_name,
                "service_name": clean_name,
                "map_name": target_map,
                "available_maps": maps[:5],
                "service_url": f"{ISERVER_BASE}/iserver/services/map-{clean_name}/rest",
                "tile_url": tile_url,
                "attribution": "SuperMap iServer",
                "type": "iserver",
                "source": "iserver",
                # China100 returns valid cached map content from levels 3-11.
                # zxyTileImage is iServer's Web Mercator z/x/y cache contract.
                "min_zoom": 3,
                "max_zoom": 11,
            })

        basemaps.sort(key=lambda item: ("luonan" not in item["service_name"].lower(), item["service_name"]))
        return basemaps
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 地图服务
# ---------------------------------------------------------------------------

def get_map_service(service_name: str) -> dict | None:
    """获取地图服务元数据（地图列表、范围、坐标系）"""
    try:
        r = _get_session().get(
            f"{ISERVER_BASE}/iserver/services/map-{service_name}/rest/maps.json",
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def get_map_tile_url(service_name: str, map_name: str, layer_idx: int = 0) -> str | None:
    """返回 WMTS 瓦片模板 URL，可直接在 Leaflet/iClient 中使用"""
    info = get_map_service(service_name)
    if not info:
        return None
    maps = info if isinstance(info, list) else info.get("maps", [])
    if not maps:
        return None
    name = map_name
    if not name:
        name = maps[0] if isinstance(maps[0], str) else maps[0].get("name", map_name)
    elif name not in [m if isinstance(m, str) else m.get("name", "") for m in maps]:
        name = maps[0] if isinstance(maps[0], str) else maps[0].get("name", map_name)
    return (
        f"{ISERVER_BASE}/iserver/services/map-{service_name}/rest/maps"
        f"/{name}/zxyTileImage.png?z={{z}}&x={{x}}&y={{y}}&width=256&height=256"
    )


# ---------------------------------------------------------------------------
# 数据服务 — 要素查询
# ---------------------------------------------------------------------------

def get_data_service(datasource_name: str, dataset_name: str, max_features: int = 100) -> dict | None:
    """查询数据服务中的要素（GET 全量，POST 带条件）"""
    try:
        qualified_name = dataset_name if ":" in dataset_name else f"{datasource_name}:{dataset_name}"
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults.json",
            json={
                "datasetNames": [qualified_name],
                "maxFeatures": max_features,
                "returnFeatureWithFieldCaption": True,
                "getFeatureMode": "GET_BY_BOUNDS",
            },
            timeout=15,
        )
        if r.status_code in (200, 201):
            return _feature_result_to_geojson(r.json(), max_features)
    except Exception:
        pass
    return None


def _feature_result_to_geojson(payload: dict[str, Any], max_features: int) -> dict:
    """Resolve iServer feature resources into the GeoJSON returned to browsers."""
    result = _fetch_json_resource(payload.get("newResourceLocation")) if payload.get("newResourceLocation") else payload
    raw_features = list(result.get("features") or []) if isinstance(result, dict) else []
    feature_uris = list(result.get("featureUriList") or []) if isinstance(result, dict) else []
    for uri in feature_uris[:max_features]:
        raw_features.append(_fetch_json_resource(uri))

    features = []
    for raw_feature in raw_features[:max_features]:
        if not isinstance(raw_feature, dict):
            continue
        geometry = supermap_to_geojson_geometry(raw_feature.get("geometry") or {})
        if not geometry:
            continue
        properties = raw_feature.get("properties") if isinstance(raw_feature.get("properties"), dict) else {}
        if not properties:
            properties = dict(zip(raw_feature.get("fieldNames") or [], raw_feature.get("fieldValues") or []))
        feature = {"type": "Feature", "properties": properties, "geometry": geometry}
        if raw_feature.get("ID") is not None:
            feature["id"] = raw_feature["ID"]
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
        "totalFeatures": int((result or {}).get("totalCount", len(features))),
    }


def list_data_datasets(datasource_name: str) -> list[str]:
    """Return datasets exposed by one published iServer data service."""
    try:
        response = _get_session().get(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/datasources/{datasource_name}/datasets.json",
            timeout=15,
        )
        if response.status_code != 200:
            return []
        payload = response.json()
        datasets = payload if isinstance(payload, list) else payload.get("datasetNames", payload.get("datasets", []))
        return [item if isinstance(item, str) else item.get("name", "") for item in datasets if item]
    except Exception:
        return []


def query_features_by_geometry(
    datasource_name: str,
    dataset_name: str,
    geometry: dict,
    spatial_relation: str = "INTERSECT",
    max_features: int = 500,
) -> dict | None:
    """
    空间查询：找出与输入几何相交（或指定关系）的要素。

    The data-service response is a temporary resource.  Fetch the resource and
    its feature URIs before returning so callers always receive real features.
    """
    try:
        qualified_name = dataset_name if ":" in dataset_name else f"{datasource_name}:{dataset_name}"
        relation = spatial_relation.upper()
        if relation == "INTERSECTS":
            relation = "INTERSECT"
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults.json",
            json={
                "datasetNames": [qualified_name],
                "getFeatureMode": "SPATIAL",
                "spatialQueryMode": relation,
                "geometry": geojson_to_supermap_geometry(geometry),
            },
            timeout=20,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"iServer spatial query failed ({r.status_code}): {r.text[:300]}")
        task = r.json()
        resource_url = task.get("newResourceLocation")
        result = _fetch_json_resource(resource_url) if resource_url else task
        feature_uris = result.get("featureUriList", []) if isinstance(result, dict) else []
        features = []
        for uri in feature_uris[:max_features]:
            feature = _fetch_json_resource(uri)
            if isinstance(feature, dict):
                raw_geometry = feature.get("geometry")
                if raw_geometry:
                    feature = {**feature, "geometry": supermap_to_geojson_geometry(raw_geometry)}
                features.append(feature)
        return {
            "feature_count": int((result or {}).get("totalCount", len(feature_uris))),
            "features": features,
            "feature_uris": feature_uris[:max_features],
            "resource_url": resource_url,
            "source": f"iserver:data-{datasource_name}",
        }
    except Exception as exc:
        raise RuntimeError(f"iServer spatial query failed: {exc}") from exc


# ---------------------------------------------------------------------------
# 数据编辑服务 — 要素增删改
# ---------------------------------------------------------------------------

def add_features(
    datasource_name: str,
    dataset_name: str,
    features: list[dict],
) -> dict | None:
    """
    向数据集添加新要素。

    Args:
        datasource_name: 数据源名称
        dataset_name: 数据集名称
        features: 要素列表，每个要素格式:
            {
                "geometry": {...},  # GeoJSON geometry
                "fieldNames": ["name", "type", "area"],
                "fieldValues": ["地块A", "核桃", 1000.5]
            }

    Returns:
        {"succeed": true, "featureCount": 3, ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults/add.json",
            json={
                "datasetName": dataset_name,
                "features": features,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] add features error: {e}")
    return None


def update_features(
    datasource_name: str,
    dataset_name: str,
    features: list[dict],
    ids: list[int],
) -> dict | None:
    """
    更新数据集中的要素。

    Args:
        datasource_name: 数据源名称
        dataset_name: 数据集名称
        features: 要素列表（同add_features格式）
        ids: 要更新的要素ID列表（与features对应）

    Returns:
        {"succeed": true, "featureCount": 2, ...} or None
    """
    try:
        r = _get_session().put(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults/update.json",
            json={
                "datasetName": dataset_name,
                "features": features,
                "IDs": ids,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] update features error: {e}")
    return None


def delete_features(
    datasource_name: str,
    dataset_name: str,
    ids: list[int],
) -> dict | None:
    """
    删除数据集中的要素。

    Args:
        datasource_name: 数据源名称
        dataset_name: 数据集名称
        ids: 要删除的要素ID列表

    Returns:
        {"succeed": true, "featureCount": 5, ...} or None
    """
    try:
        r = _get_session().delete(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults.json",
            json={
                "datasetName": dataset_name,
                "IDs": ids,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] delete features error: {e}")
    return None


def query_features_by_ids(
    datasource_name: str,
    dataset_name: str,
    ids: list[int],
) -> dict | None:
    """
    根据ID查询要素。

    Args:
        datasource_name: 数据源名称
        dataset_name: 数据集名称
        ids: 要素ID列表

    Returns:
        {"features": [...], ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults.json",
            json={
                "datasetNames": [dataset_name],
                "getFeatureMode": "ID",
                "IDs": ids,
            },
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] query by IDs error: {e}")
    return None


def query_features_by_sql(
    datasource_name: str,
    dataset_name: str,
    sql_filter: str,
    max_features: int = 500,
) -> dict | None:
    """
    SQL查询要素（属性过滤）。

    Args:
        datasource_name: 数据源名称
        dataset_name: 数据集名称
        sql_filter: SQL WHERE子句（不含WHERE关键字），如: "area > 1000 AND type = '核桃'"
        max_features: 最大返回要素数

    Returns:
        {"features": [...], ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/data-{datasource_name}/rest/data/featureResults.json",
            json={
                "datasetNames": [dataset_name],
                "getFeatureMode": "SQL",
                "queryParameter": {
                    "attributeFilter": sql_filter,
                },
                "maxFeatures": max_features,
            },
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] SQL query error: {e}")
    return None


# ---------------------------------------------------------------------------
# 空间分析服务
# ---------------------------------------------------------------------------

def spatial_buffer(
    geometry: dict,
    buffer_distance_m: float = 1000.0,
) -> dict | None:
    """
    几何缓冲区分析，返回缓冲后的 GeoJSON 几何体。

    The published China100 spatial-analysis service is geographic (EPSG:4326).
    iServer's geometry buffer uses coordinate units, so metres are converted to
    a local degree approximation before submitting the real buffer operation.
    """
    try:
        latitude = _geometry_centroid_latitude(geometry)
        meters_per_degree = max(1.0, 111_320.0 * cos(radians(latitude)))
        distance_in_degrees = float(buffer_distance_m) / meters_per_degree
        r = _get_session().post(
            f"{_spatial_analysis_base_url()}/spatialanalyst/geometry/buffer.json",
            json={
                "sourceGeometry": geojson_to_supermap_geometry(geometry),
                "analystParameter": {
                    "endType": "ROUND",
                    "semicircleLineSegment": 12,
                    "leftDistance": {"value": distance_in_degrees},
                    "rightDistance": {"value": distance_in_degrees},
                },
            },
            timeout=30,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"iServer buffer failed ({r.status_code}): {r.text[:300]}")
        task = r.json()
        resource_url = task.get("newResourceLocation")
        result = _fetch_json_resource(resource_url) if resource_url else task
        raw_geometry = (result or {}).get("resultGeometry")
        if not raw_geometry:
            raise RuntimeError("iServer buffer returned no resultGeometry")
        return {
            "resultGeometry": supermap_to_geojson_geometry(raw_geometry),
            "rawGeometry": raw_geometry,
            "resource_url": resource_url,
            "distance_m": float(buffer_distance_m),
            "distance_mode": "local_degree_approximation",
            "source": "iserver:spatialAnalysis",
        }
    except Exception as exc:
        raise RuntimeError(f"iServer buffer failed: {exc}") from exc


def overlay_datasets(
    source_dataset: str,
    operate_dataset: str,
    source_datasource: str,
    operate_datasource: str,
    overlay_mode: str = "INTERSECT",
) -> dict | None:
    """
    两个数据集之间的矢量叠加分析（需要数据已发布为 iServer 数据集）。

    overlay_mode: INTERSECT / UNION / ERASE / CLIP / UPDATE / XOR
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatial-analysis/restjsr"
            f"/spatialanalyst/datasets/{source_datasource}:{source_dataset}/overlay.json",
            json={
                "operateDataset": operate_dataset,
                "operateDatasetAlias": operate_datasource,
                "operation": overlay_mode,
                "isAttributeRetained": True,
            },
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] overlay error: {e}")
    return None


# ---------------------------------------------------------------------------
# 地形分析服务（DEM）
# ---------------------------------------------------------------------------

def terrain_slope(
    datasource: str,
    dataset: str,
    slope_type: str = "DEGREE",
    z_factor: float = 1.0,
) -> dict | None:
    """
    DEM坡度分析。

    Args:
        datasource: 数据源名称
        dataset: DEM数据集名称
        slope_type: DEGREE（度）或 PERCENT_RISE（百分比）
        z_factor: 高程单位转换因子（默认1.0）

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/terrain/{dataset}/slope.json",
            json={
                "slopeType": slope_type,
                "zFactor": z_factor,
            },
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] slope analysis error: {e}")
    return None


def terrain_aspect(
    datasource: str,
    dataset: str,
) -> dict | None:
    """
    DEM坡向分析。

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/terrain/{dataset}/aspect.json",
            json={},
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] aspect analysis error: {e}")
    return None


def terrain_hillshade(
    datasource: str,
    dataset: str,
    azimuth: float = 315.0,
    altitude: float = 45.0,
) -> dict | None:
    """
    DEM山体阴影分析。

    Args:
        datasource: 数据源名称
        dataset: DEM数据集名称
        azimuth: 光源方位角（0-360度，0=北，90=东）
        altitude: 光源高度角（0-90度）

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/terrain/{dataset}/hillshade.json",
            json={
                "azimuth": azimuth,
                "altitude": altitude,
            },
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] hillshade error: {e}")
    return None


# ---------------------------------------------------------------------------
# 密度分析服务
# ---------------------------------------------------------------------------

def kernel_density(
    datasource: str,
    dataset: str,
    search_radius: float,
    cell_size: float | None = None,
    population_field: str | None = None,
) -> dict | None:
    """
    核密度分析（点数据集）。

    Args:
        datasource: 数据源名称
        dataset: 点数据集名称
        search_radius: 搜索半径（米）
        cell_size: 输出栅格像元大小（米），None则自动计算
        population_field: 权重字段名（None则每个点权重为1）

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        payload = {
            "searchRadius": search_radius,
        }
        if cell_size:
            payload["cellSize"] = cell_size
        if population_field:
            payload["populationField"] = population_field

        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/density/{dataset}/kerneldensity.json",
            json=payload,
            timeout=180,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] kernel density error: {e}")
    return None


def point_density(
    datasource: str,
    dataset: str,
    cell_size: float,
    search_radius: float,
    population_field: str | None = None,
) -> dict | None:
    """
    点密度分析。

    Args:
        datasource: 数据源名称
        dataset: 点数据集名称
        cell_size: 输出栅格像元大小（米）
        search_radius: 搜索半径（米）
        population_field: 权重字段名

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        payload = {
            "cellSize": cell_size,
            "searchRadius": search_radius,
        }
        if population_field:
            payload["populationField"] = population_field

        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/density/{dataset}/pointdensity.json",
            json=payload,
            timeout=180,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] point density error: {e}")
    return None


# ---------------------------------------------------------------------------
# 栅格叠加分析
# ---------------------------------------------------------------------------

def weighted_overlay(
    datasource: str,
    rasters: list[dict],
    weights: list[float],
    output_dataset: str | None = None,
) -> dict | None:
    """
    栅格加权叠加分析。

    Args:
        datasource: 数据源名称
        rasters: 栅格数据集列表，每项包含 {"dataset": "name", "reclassTable": [...]}
        weights: 对应权重列表（总和应为1.0）
        output_dataset: 输出数据集名称

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None

    Example:
        rasters = [
            {"dataset": "slope", "reclassTable": [{"min": 0, "max": 15, "newValue": 1}, ...]},
            {"dataset": "aspect", "reclassTable": [...]},
        ]
        weights = [0.4, 0.3, 0.3]
    """
    try:
        payload = {
            "overlayLayers": [
                {
                    "dataset": r["dataset"],
                    "weight": w,
                    "reclassTable": r.get("reclassTable", []),
                }
                for r, w in zip(rasters, weights)
            ],
        }
        if output_dataset:
            payload["resultDataset"] = output_dataset

        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/overlay/weightedoverlay.json",
            json=payload,
            timeout=240,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] weighted overlay error: {e}")
    return None


# ---------------------------------------------------------------------------
# 插值分析
# ---------------------------------------------------------------------------

def interpolation_idw(
    datasource: str,
    dataset: str,
    z_field: str,
    cell_size: float,
    power: float = 2.0,
    search_radius: float | None = None,
) -> dict | None:
    """
    IDW反距离权重插值。

    Args:
        datasource: 数据源名称
        dataset: 点数据集名称
        z_field: 高程/值字段名
        cell_size: 输出栅格像元大小
        power: 距离幂次（默认2.0）
        search_radius: 搜索半径（None则使用默认）

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        payload = {
            "zValueField": z_field,
            "cellSize": cell_size,
            "power": power,
        }
        if search_radius:
            payload["searchRadius"] = search_radius

        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/interpolation/{dataset}/idw.json",
            json=payload,
            timeout=180,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] IDW interpolation error: {e}")
    return None


def interpolation_kriging(
    datasource: str,
    dataset: str,
    z_field: str,
    cell_size: float,
    variogram_type: str = "SPHERICAL",
) -> dict | None:
    """
    Kriging克里金插值。

    Args:
        datasource: 数据源名称
        dataset: 点数据集名称
        z_field: 高程/值字段名
        cell_size: 输出栅格像元大小
        variogram_type: 变异函数类型（SPHERICAL/EXPONENTIAL/GAUSSIAN/LINEAR）

    Returns:
        {"succeed": true, "newResourceID": "xxx", ...} or None
    """
    try:
        payload = {
            "zValueField": z_field,
            "cellSize": cell_size,
            "variogramType": variogram_type,
        }

        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/services/spatialanalyst-{datasource}/restjsr"
            f"/spatialanalyst/interpolation/{dataset}/kriging.json",
            json=payload,
            timeout=240,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[iserver] Kriging interpolation error: {e}")
    return None


# ---------------------------------------------------------------------------
# Manager API — 自动发布 UDBX 为数据服务
# ---------------------------------------------------------------------------

def publish_udbx_as_data_service(
    udbx_path: str,
    service_name: str,
    datasource_alias: str = "result_ds",
) -> dict:
    """
    通过 iServer Manager REST API 将本地 UDBX 注册为数据服务。

    流程:
    1. 确认 iServer 可达
    2. POST /iserver/manager/services.json 注册新数据服务
    3. 返回服务 URL

    注意: iServer 进程需要能访问 udbx_path 所在文件系统（本机路径或共享路径）。
    """
    if not check_iserver():
        return {"status": "iserver_unreachable", "service_url": None}

    import os
    abs_path = os.path.abspath(udbx_path)

    payload = {
        "component": {
            "type": "com.supermap.services.components.impl.DataServiceComponentImpl",
            "datasourceConnectionInfos": [
                {
                    "dataBase": abs_path,
                    "engineType": "UDB",
                    "alias": datasource_alias,
                    "readOnly": False,
                }
            ],
        },
        "interfaceTypeNames": [
            "com.supermap.services.rest.DataServiceResolver",
        ],
        "name": f"data-{service_name}",
        "enabled": True,
    }

    try:
        r = _get_session().post(
            f"{ISERVER_BASE}/iserver/manager/services.json",
            json=payload,
            timeout=30,
        )
        if r.status_code in (200, 201):
            service_url = f"{ISERVER_BASE}/iserver/services/data-{service_name}/rest/data"
            return {
                "status": "published",
                "service_name": f"data-{service_name}",
                "service_url": service_url,
                "response": r.json() if r.content else {},
            }
        # 409 表示同名服务已存在
        if r.status_code == 409:
            service_url = f"{ISERVER_BASE}/iserver/services/data-{service_name}/rest/data"
            return {
                "status": "already_exists",
                "service_name": f"data-{service_name}",
                "service_url": service_url,
            }
        return {
            "status": "publish_failed",
            "http_status": r.status_code,
            "detail": r.text[:400],
            "service_url": None,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "service_url": None}


def delete_service(service_name: str) -> bool:
    """删除已注册的 iServer 服务（重新发布前调用）"""
    try:
        r = _get_session().delete(
            f"{ISERVER_BASE}/iserver/manager/services/data-{service_name}.json",
            timeout=15,
        )
        return r.status_code in (200, 204, 404)
    except Exception:
        return False


def publish_dataset_file(dataset_path: str, service_name: str, datasource_alias: str) -> dict:
    """Publish a supported local dataset through the Manager API boundary.

    Credentials remain inside this module; callers only receive lifecycle-safe
    status, URL, and diagnostic information.
    """
    from pathlib import Path

    source = Path(dataset_path)
    suffix = source.suffix.lower()
    if not source.is_file():
        return {"status": "source_missing", "detail": "Uploaded dataset file is missing", "service_url": None}
    if suffix == ".udbx":
        publish_path = source
    elif suffix in {".geojson", ".json"}:
        try:
            from server.integrations.udbx_publisher import geojson_to_udbx

            publish_path = source.with_name(f"{service_name}.udbx")
            if not geojson_to_udbx(source, publish_path, service_name):
                return {"status": "source_prepare_failed", "detail": "Could not prepare uploaded GeoJSON for iServer", "service_url": None}
        except Exception as exc:
            return {"status": "source_prepare_failed", "detail": str(exc), "service_url": None}
    else:
        return {"status": "unsupported_format", "detail": "Only GeoJSON and UDBX datasets can be published", "service_url": None}

    try:
        from server.integrations.udbx_publisher import _list_datasets

        dataset_names = _list_datasets(publish_path)
    except Exception as exc:
        return {"status": "source_prepare_failed", "detail": str(exc), "service_url": None}
    if not dataset_names:
        return {"status": "source_prepare_failed", "detail": "Prepared UDBX contains no publishable dataset", "service_url": None}

    result = publish_udbx_as_data_service(str(publish_path), service_name, datasource_alias)
    result["dataset_name"] = dataset_names[0]
    return result


def unpublish_service(service_name: str) -> dict:
    """Remove a service without exposing Manager API credentials to callers."""
    if delete_service(service_name):
        return {"status": "unpublished"}
    return {"status": "unpublish_failed", "detail": "iServer did not confirm service removal"}
