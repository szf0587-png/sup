"""三维服务API路由 - iServer 3D服务集成

提供三维场景列表、地形服务、模型上传等功能
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

from server.api.auth import get_current_user
from server.models.user import User
from server.integrations import iserver_client
from server.config import ISERVER_BASE, DATA_DIR

router = APIRouter(prefix="/api/3d-services", tags=["3d-services"])


def _normalise_service_name(value: str) -> str:
    """iServer service catalog may return ``name/rest``; URLs need the id only."""
    return (value or "").split("/", 1)[0].strip()


def _clean_scene_name(service_name: str) -> str:
    name = _normalise_service_name(service_name)
    for prefix in ("3D-", "realspace-"):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _realspace_url(service_name: str) -> str:
    return f"{ISERVER_BASE}/iserver/services/{_normalise_service_name(service_name)}/rest/realspace"


def _json_get(session, url: str, timeout: int = 8):
    response = session.get(url if url.endswith(".json") else f"{url}.json", timeout=timeout)
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _service_catalog(session) -> list[dict]:
    payload = _json_get(session, f"{ISERVER_BASE}/iserver/services", timeout=10) or []
    services = payload if isinstance(payload, list) else payload.get("services", [])
    return [
        item for item in services
        if isinstance(item, dict)
        and (_normalise_service_name(item.get("name", "")).startswith("3D-")
             or _normalise_service_name(item.get("name", "")).startswith("realspace-"))
    ]


def _resolve_service(session, scene_name: str) -> tuple[str, str]:
    requested = _normalise_service_name(scene_name)
    for item in _service_catalog(session):
        raw_name = item.get("name", "")
        service_name = _normalise_service_name(raw_name)
        if requested in {service_name, _clean_scene_name(service_name)}:
            return service_name, _clean_scene_name(service_name)
    for candidate in (requested, f"3D-{requested}", f"realspace-{requested}"):
        if _json_get(session, f"{_realspace_url(candidate)}", timeout=5) is not None:
            return candidate, _clean_scene_name(candidate)
    raise HTTPException(status_code=404, detail=f"三维服务 '{scene_name}' 不存在")


def _resource_items(payload: object, collection_key: str) -> list[dict]:
    """Normalize iServer resource catalogs across list and singleton responses.

    iServer returns an array when a catalog contains multiple resources, but
    returns the resource object itself when only one scene or dataset exists.
    Keeping that distinction out of the route logic prevents a valid one-item
    catalog from being reported as empty.
    """
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    nested = payload.get(collection_key)
    if isinstance(nested, list):
        return [item for item in nested if isinstance(item, dict)]
    if isinstance(nested, dict):
        return [nested]

    if payload.get("name") or payload.get("path"):
        return [payload]
    return []


def _scene_catalog(session, service_name: str) -> list[dict]:
    payload = _json_get(session, f"{_realspace_url(service_name)}/scenes") or []
    return _resource_items(payload, "scenes")


def _data_catalog(session, service_name: str) -> list[dict]:
    payload = _json_get(session, f"{_realspace_url(service_name)}/datas") or []
    return _resource_items(payload, "datas")


def _scene_resource_name(item: dict) -> str:
    return item.get("name") or item.get("sceneName") or "默认场景"


def _scene_url(service_name: str, scene_name: str) -> str:
    return f"{_realspace_url(service_name)}/scenes/{quote(scene_name, safe='')}"


def _terrain_data_url(service_name: str, layers: object) -> Optional[str]:
    """Build the iServer SCT endpoint for the terrain layer in a scene."""
    if not isinstance(layers, list):
        return None
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        is_terrain = (
            layer.get("layer3DType") == "TerrainFileLayer"
            or layer.get("cacheType") == "TIN"
            or layer.get("type") == "TerrainFileLayer"
            or layer.get("cache_type") == "TIN"
        )
        data_name = layer.get("dataName") or layer.get("data_name") or layer.get("name")
        if is_terrain and data_name:
            return f"{_realspace_url(service_name)}/datas/{quote(str(data_name), safe='@')}"
    return None


def _normalise_bounds(value: object) -> Optional[dict[str, float]]:
    """Normalize iServer/SCT bounds to west/south/east/north."""
    if not isinstance(value, dict):
        return None
    candidates = (
        ("west", "south", "east", "north"),
        ("left", "bottom", "right", "top"),
        ("minX", "minY", "maxX", "maxY"),
    )
    for west_key, south_key, east_key, north_key in candidates:
        if all(key in value for key in (west_key, south_key, east_key, north_key)):
            try:
                west = float(value[west_key])
                south = float(value[south_key])
                east = float(value[east_key])
                north = float(value[north_key])
            except (TypeError, ValueError):
                continue
            if west < east and south < north:
                return {"west": west, "south": south, "east": east, "north": north}
    nested = value.get("bounds")
    return _normalise_bounds(nested) if nested is not value else None


def _sct_bounds(layer: dict) -> Optional[dict[str, float]]:
    """Read bounds from an SCT file when iServer omits layer bounds."""
    direct = _normalise_bounds(layer.get("bounds"))
    if direct:
        return direct
    config_path = layer.get("dataConfigPath")
    if not config_path:
        return None
    path = Path(str(config_path))
    if not path.is_file() or path.suffix.lower() != ".sct":
        return None
    try:
        # SCT metadata commonly declares GB18030, which ElementTree cannot
        # parse directly from a binary stream on this runtime.
        root = ET.fromstring(path.read_bytes().decode("gb18030"))
        values = {}
        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1]
            if name in {"Left", "Bottom", "Right", "Top"}:
                values[name.lower()] = float((element.text or "").strip())
        return _normalise_bounds({
            "left": values.get("left"),
            "bottom": values.get("bottom"),
            "right": values.get("right"),
            "top": values.get("top"),
        })
    except (ET.ParseError, OSError, TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------

class SceneInfo(BaseModel):
    """三维场景信息"""
    scene_name: str
    scene_url: str
    terrain_available: bool
    layers: list[str]
    description: Optional[str] = None


class TerrainConfig(BaseModel):
    """地形服务配置"""
    scene_name: str
    terrain_url: Optional[str] = None
    dem_source: str
    resolution: str
    cache_format: str = "sct"


# ---------------------------------------------------------------------------
# 三维场景管理
# ---------------------------------------------------------------------------

@router.get("/scenes/list", summary="列出所有三维场景")
async def list_3d_scenes(
    current_user: User = Depends(get_current_user),
):
    """
    列出iServer上所有可用的三维场景服务

    返回：
    - 场景名称
    - 场景URL
    - 可用图层
    - 地形服务状态

    应用场景：
    - 前端场景选择器
    - 三维地图初始化
    """
    try:
        session = iserver_client._get_session()
        response = session.get(f"{ISERVER_BASE}/iserver/services.json", timeout=10)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="无法连接iServer")

        scenes = []
        for service in _service_catalog(session):
            service_name = _normalise_service_name(service.get("name", ""))
            scene_url = _realspace_url(service_name)
            scene_catalog = _scene_catalog(session, service_name)
            data_catalog = _data_catalog(session, service_name)
            scene_items = []
            layers = []
            for item in scene_catalog:
                scene_item_name = _scene_resource_name(item)
                scene_item_url = _scene_url(service_name, scene_item_name)
                scene_data = _json_get(session, scene_item_url, timeout=8) or {}
                scene_layers = scene_data.get("layers", []) if isinstance(scene_data, dict) else []
                layers.extend(scene_layers)
                scene_items.append({
                    "name": scene_item_name,
                    "url": scene_item_url,
                    "camera": scene_data.get("camera") if isinstance(scene_data, dict) else None,
                })
            terrain_available = any(
                layer.get("layer3DType") == "TerrainFileLayer"
                or layer.get("cacheType") == "TIN"
                for layer in layers if isinstance(layer, dict)
            )
            scenes.append({
                "scene_name": _clean_scene_name(service_name),
                "service_name": service_name,
                "scene_url": scene_url,
                "terrain_available": terrain_available,
                "layers": layers,
                "scenes": scene_items,
                "datasets": [
                    {"name": item.get("name"), "url": item.get("path"), "type": item.get("resourceType")}
                    for item in data_catalog if isinstance(item, dict)
                ],
                "description": service.get("description"),
            })

        return {
            "status": "success",
            "count": len(scenes),
            "scenes": scenes,
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "degraded",
            "count": 0,
            "scenes": [],
            "reason": f"iServer 不可用，暂时无法读取三维场景: {str(e)}",
        }


@router.get("/scenes/{scene_name}", summary="获取三维场景详情")
async def get_3d_scene_info(
    scene_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取指定三维场景的详细信息

    返回：
    - 场景元数据
    - 图层列表
    - 地形服务URL
    - 初始视角
    """
    try:
        session = iserver_client._get_session()

        actual_service_name, clean_name = _resolve_service(session, scene_name)
        scene_catalog = _scene_catalog(session, actual_service_name)
        selected_scene_name = _scene_resource_name(scene_catalog[0]) if scene_catalog else "默认场景"
        for item in scene_catalog:
            if _scene_resource_name(item) == scene_name:
                selected_scene_name = scene_name
                break
        scene_data = _json_get(session, _scene_url(actual_service_name, selected_scene_name), timeout=10) or {}
        if not scene_data:
            raise HTTPException(status_code=404, detail=f"三维服务 '{scene_name}' 没有可读取的场景")
        layers = scene_data.get("layers", []) if isinstance(scene_data, dict) else []

        return {
            "status": "success",
            "scene_name": clean_name,
            "scene_resource": selected_scene_name,
            "service_name": actual_service_name,
            "scene_url": _realspace_url(actual_service_name),
            "scene_resource_url": _scene_url(actual_service_name, selected_scene_name),
            "terrain_available": any(
                layer.get("layer3DType") == "TerrainFileLayer" or layer.get("cacheType") == "TIN"
                for layer in layers if isinstance(layer, dict)
            ),
            "layers": layers,
            "data": scene_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景信息失败: {str(e)}")


@router.get("/scenes/{scene_name}/config", summary="获取前端三维场景配置")
async def get_3d_scene_config(
    scene_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取适用于前端WebGL（Cesium/SuperMap iClient3D）的场景配置

    返回示例：
    ```json
    {
      "scene_url": "http://localhost:8090/iserver/services/3D-luonan/rest/realspace",
      "terrain_url": "http://localhost:8090/iserver/services/3D-luonan/rest/realspace/datas/DatasetDEM",
      "layers": [
        {"name": "影像图层", "type": "imagery", "url": "..."},
        {"name": "矢量数据", "type": "vector", "url": "..."}
      ],
      "initial_view": {
        "longitude": 110.15,
        "latitude": 34.09,
        "height": 50000,
        "heading": 0,
        "pitch": -90
      }
    }
    ```

    前端使用（Cesium）：
    ```javascript
    const config = await fetch('/api/3d-services/scenes/luonan/config').then(r => r.json());

    const viewer = new Cesium.Viewer('cesiumContainer', {
        terrainProvider: new Cesium.CesiumTerrainProvider({
            url: config.terrain_url
        })
    });

    viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(
            config.initial_view.longitude,
            config.initial_view.latitude,
            config.initial_view.height
        ),
        orientation: {
            heading: Cesium.Math.toRadians(config.initial_view.heading),
            pitch: Cesium.Math.toRadians(config.initial_view.pitch),
            roll: 0
        }
    });
    ```
    """
    # 获取场景信息
    scene_info_response = await get_3d_scene_info(scene_name, current_user)
    service_name = scene_info_response["service_name"]

    scene_url = scene_info_response["scene_url"]
    scene_resource_url = scene_info_response["scene_resource_url"]
    scene_data = scene_info_response.get("data") or {}
    camera = scene_data.get("camera") or {}
    from server.config import CASE_STUDY

    initial_view = {
        "longitude": camera.get("longitude", CASE_STUDY["center_lon"]),
        "latitude": camera.get("latitude", CASE_STUDY["center_lat"]),
        "height": camera.get("altitude", 18000),
        "heading": camera.get("heading", 0),
        "pitch": -45 if camera.get("tilt", 0) == 0 else -30,
    }
    layers = []
    terrain_bounds = None
    for layer in scene_info_response.get("layers", []):
        if not isinstance(layer, dict):
            continue
        layers.append({
            "name": layer.get("name") or layer.get("caption"),
            "type": layer.get("layer3DType") or layer.get("cacheType") or "3D layer",
            "visible": layer.get("visible", True),
            "queryable": layer.get("queryable", False),
            "cache_type": layer.get("cacheType"),
            "data_name": layer.get("dataName"),
        })
        if terrain_bounds is None and (
            layer.get("layer3DType") == "TerrainFileLayer" or layer.get("cacheType") == "TIN"
        ):
            terrain_bounds = _sct_bounds(layer)

    return {
        "scene_name": scene_info_response["scene_name"],
        "scene_resource": scene_info_response["scene_resource"],
        "service_name": service_name,
        "scene_url": scene_url,
        "scene_resource_url": scene_resource_url,
        "terrain_url": _terrain_data_url(service_name, scene_info_response.get("layers", [])),
        "terrain_provider": "SuperMapTerrainProvider (SCT)",
        "terrain_available": scene_info_response.get("terrain_available", False),
        "layers": layers,
        "terrain_bounds": terrain_bounds,
        "initial_view": initial_view,
        "attribution": "SuperMap iServer Realspace",
        "note": "SCT 地形作为 Realspace TerrainFileLayer 由 iClient3D 加载，不是 Cesium terrain endpoint。",
    }


# ---------------------------------------------------------------------------
# 地形服务
# ---------------------------------------------------------------------------

@router.get("/terrain/{scene_name}/info", summary="获取地形服务信息")
async def get_terrain_info(
    scene_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取地形服务的详细信息

    返回：
    - 地形URL
    - 分辨率
    - 缓存格式（.sct）
    - 范围
    """
    try:
        session = iserver_client._get_session()

        service_name, clean_name = _resolve_service(session, scene_name)
        scene_catalog = _scene_catalog(session, service_name)
        scene_resource = _scene_resource_name(scene_catalog[0]) if scene_catalog else "默认场景"
        scene_url = _scene_url(service_name, scene_resource)
        scene_data = _json_get(session, scene_url, timeout=8) or {}
        layers = scene_data.get("layers", []) if isinstance(scene_data, dict) else []
        terrain_layers = [
            layer for layer in layers
            if isinstance(layer, dict)
            and (layer.get("layer3DType") == "TerrainFileLayer" or layer.get("cacheType") == "TIN")
        ]
        if terrain_layers:
            terrain_bounds = None
            for layer in terrain_layers:
                terrain_bounds = _sct_bounds(layer)
                if terrain_bounds:
                    break
            return {
                "status": "success",
                "scene_name": clean_name,
                "scene_resource": scene_resource,
                "terrain_available": True,
                "realspace_url": _realspace_url(service_name),
                "scene_url": scene_url,
                "terrain_url": _terrain_data_url(service_name, terrain_layers),
                "terrain_layers": terrain_layers,
                "terrain_bounds": terrain_bounds,
                "cache_format": "sct",
                "note": "SCT 已作为 Realspace TerrainFileLayer 发布，由 iClient3D Realspace 加载。",
            }

        raise HTTPException(
            status_code=404,
            detail=f"场景 '{scene_name}' 的地形服务不可用。请确保：\n"
                   "1. 在iDesktopX中对DEM数据右键 → 生成缓存(.sct)\n"
                   "2. 将缓存发布到iServer 3D服务"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地形信息失败: {str(e)}")


@router.get("/terrain/{scene_name}/diagnostics", summary="诊断三维地形渲染链路")
async def get_terrain_diagnostics(
    scene_name: str,
    current_user: User = Depends(get_current_user),
):
    """Return an explicit rendering contract for the frontend terrain controller.

    The regular scene endpoint is intentionally permissive so the 3D page can
    still open when iServer has no terrain. This endpoint keeps that fallback
    visible by returning the selected provider and a human-readable reason.
    """
    try:
        session = iserver_client._get_session()
        service_name, clean_name = _resolve_service(session, scene_name)
        scene_catalog = _scene_catalog(session, service_name)
        scene_resource = _scene_resource_name(scene_catalog[0]) if scene_catalog else "默认场景"
        scene_url = _scene_url(service_name, scene_resource)
        scene_data = _json_get(session, scene_url, timeout=8) or {}
        layers = scene_data.get("layers", []) if isinstance(scene_data, dict) else []
        terrain_layers = [
            layer for layer in layers
            if isinstance(layer, dict)
            and (layer.get("layer3DType") == "TerrainFileLayer" or layer.get("cacheType") == "TIN")
        ]

        if not terrain_layers:
            return {
                "status": "degraded",
                "available": False,
                "provider_type": "ellipsoid",
                "scene_name": clean_name,
                "service_name": service_name,
                "scene_resource": scene_resource,
                "terrain_url": None,
                "layer_name": None,
                "bounds": None,
                "reason": "iServer 场景未返回 TerrainFileLayer/TIN 图层",
            }

        terrain_layer = terrain_layers[0]
        terrain_url = _terrain_data_url(service_name, terrain_layers)
        bounds = next((_sct_bounds(layer) for layer in terrain_layers if _sct_bounds(layer)), None)
        if not terrain_url:
            return {
                "status": "degraded",
                "available": False,
                "provider_type": "ellipsoid",
                "scene_name": clean_name,
                "service_name": service_name,
                "scene_resource": scene_resource,
                "terrain_url": None,
                "layer_name": terrain_layer.get("dataName") or terrain_layer.get("name"),
                "bounds": bounds,
                "reason": "地形图层存在，但没有可用的 iServer SCT 数据 URL",
            }

        return {
            "status": "success",
            "available": True,
            "provider_type": "sct",
            "scene_name": clean_name,
            "service_name": service_name,
            "scene_resource": scene_resource,
            "terrain_url": terrain_url,
            "layer_name": terrain_layer.get("dataName") or terrain_layer.get("name"),
            "bounds": bounds,
            "reason": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "degraded",
            "available": False,
            "provider_type": "ellipsoid",
            "scene_name": scene_name,
            "terrain_url": None,
            "layer_name": None,
            "bounds": None,
            "reason": f"地形诊断失败：{str(e)[:200]}",
        }


# ---------------------------------------------------------------------------
# 三维模型上传
# ---------------------------------------------------------------------------

@router.post("/models/upload", summary="上传三维模型")
async def upload_3d_model(
    file: UploadFile = File(...),
    model_name: Optional[str] = None,
    scene_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    上传三维模型文件（.osgb / .s3mb / .obj）

    步骤：
    1. 上传模型文件
    2. 保存到用户目录
    3. （可选）发布到iServer 3D场景

    支持的格式：
    - .osgb: OSGB倾斜摄影模型
    - .s3mb: SuperMap S3M模型
    - .obj: OBJ模型（需配套材质）

    注意：
    - 大型模型建议先在Desktop中处理（优化、切片）
    - 发布到iServer需要配置模型服务
    """
    if not model_name:
        model_name = file.filename

    # 验证文件格式
    allowed_extensions = [".osgb", ".s3mb", ".obj", ".dae", ".fbx"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型格式: {file_ext}。支持格式: {', '.join(allowed_extensions)}"
        )

    try:
        # 保存模型文件
        model_dir = DATA_DIR / "models" / str(current_user.id)
        model_dir.mkdir(parents=True, exist_ok=True)

        model_id = uuid.uuid4().hex[:8]
        model_path = model_dir / f"{model_id}_{Path(file.filename).name}"

        content = await file.read()
        model_path.write_bytes(content)

        return {
            "status": "success",
            "message": f"模型上传成功: {file.filename}",
            "model_id": model_id,
            "model_name": model_name,
            "model_path": str(model_path),
            "file_size_mb": round(len(content) / (1024 * 1024), 2),
            "format": file_ext,
            "note": "模型已保存，如需发布到iServer请使用iDesktopX或调用发布API",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


# ---------------------------------------------------------------------------
# Desktop地形缓存生成指南
# ---------------------------------------------------------------------------

@router.get("/terrain/generation-guide", summary="获取地形缓存生成指南")
async def get_terrain_generation_guide(
    current_user: User = Depends(get_current_user),
):
    """
    返回在SuperMap iDesktopX中生成地形缓存的详细步骤

    返回：
    - 操作步骤
    - 参数建议
    - 常见问题
    """
    return {
        "title": "SuperMap iDesktopX 地形缓存生成指南",
        "steps": [
            {
                "step": 1,
                "title": "打开DEM数据",
                "description": "在iDesktopX中打开包含DEM栅格数据集的工作空间",
            },
            {
                "step": 2,
                "title": "生成缓存",
                "description": "右键DEM数据集 → 生成缓存 → 选择输出路径和格式(.sct)",
                "parameters": {
                    "cache_type": "地形缓存",
                    "output_format": "SCT（SuperMap Cache Terrain）",
                    "tile_size": "推荐 256x256",
                    "compression": "建议开启压缩以减小文件大小",
                },
            },
            {
                "step": 3,
                "title": "配置缓存参数",
                "description": "设置缓存级别（Level 0-18），根据DEM分辨率和应用需求选择",
                "recommendations": {
                    "县级范围": "Level 0-14（覆盖到街道级别）",
                    "市级范围": "Level 0-12",
                    "省级范围": "Level 0-10",
                },
            },
            {
                "step": 4,
                "title": "生成缓存",
                "description": "点击确定开始生成，等待完成（大型DEM可能需要较长时间）",
            },
            {
                "step": 5,
                "title": "发布到iServer",
                "description": "在iDesktopX中：服务发布 → 三维服务 → 添加地形图层 → 选择.sct文件 → 发布",
            },
            {
                "step": 6,
                "title": "验证服务",
                "description": "访问 http://localhost:8090/iserver/services/3D-xxx/rest/realspace/terrain 验证地形服务是否可用",
            },
        ],
        "common_issues": [
            {
                "issue": "缓存生成速度慢",
                "solution": "降低缓存级别上限，或只针对重点区域生成高级别缓存",
            },
            {
                "issue": "地形显示不平滑",
                "solution": "检查DEM数据质量，可以在Desktop中先做平滑处理",
            },
            {
                "issue": "iServer地形服务404",
                "solution": "确认.sct文件路径正确，iServer进程有权限访问该路径",
            },
        ],
        "performance_tips": [
            "使用SSD存储.sct缓存文件以提高加载速度",
            "对于大范围DEM，可以分区域生成多个.sct缓存",
            "定期清理不再使用的缓存文件以释放磁盘空间",
        ],
    }
