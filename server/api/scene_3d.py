"""三维服务API路由 - iServer 3D服务集成

提供三维场景列表、地形服务、模型上传等功能
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from pathlib import Path

from server.api.auth import get_current_user
from server.models.user import User
from server.integrations import iserver_client
from server.config import ISERVER_BASE, DATA_DIR

router = APIRouter(prefix="/api/3d-services", tags=["3d-services"])


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
    terrain_url: str
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

        data = response.json()
        scenes = []

        # 过滤三维场景服务
        for service in data:
            service_name = service.get("name", "")
            if service_name.startswith("3D-") or service_name.startswith("realspace-"):
                clean_name = service_name.replace("3D-", "").replace("realspace-", "")

                # 获取场景详细信息
                scene_url = f"{ISERVER_BASE}/iserver/services/{service_name}/rest/realspace"

                try:
                    scene_response = session.get(f"{scene_url}.json", timeout=5)
                    if scene_response.status_code == 200:
                        scene_data = scene_response.json()

                        scenes.append({
                            "scene_name": clean_name,
                            "scene_url": scene_url,
                            "terrain_available": "terrain" in str(scene_data).lower(),
                            "layers": scene_data.get("layers", []) if isinstance(scene_data, dict) else [],
                            "description": service.get("description"),
                        })
                except Exception:
                    # 如果获取详情失败，仍然添加基本信息
                    scenes.append({
                        "scene_name": clean_name,
                        "scene_url": scene_url,
                        "terrain_available": False,
                        "layers": [],
                        "description": service.get("description"),
                    })

        return {
            "status": "success",
            "count": len(scenes),
            "scenes": scenes,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取三维场景列表失败: {str(e)}")


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

        # 尝试不同的服务名称格式
        possible_names = [
            f"3D-{scene_name}",
            f"realspace-{scene_name}",
            scene_name,
        ]

        scene_data = None
        actual_service_name = None

        for service_name in possible_names:
            try:
                url = f"{ISERVER_BASE}/iserver/services/{service_name}/rest/realspace.json"
                response = session.get(url, timeout=5)

                if response.status_code == 200:
                    scene_data = response.json()
                    actual_service_name = service_name
                    break
            except Exception:
                continue

        if not scene_data:
            raise HTTPException(
                status_code=404,
                detail=f"三维场景 '{scene_name}' 不存在"
            )

        return {
            "status": "success",
            "scene_name": scene_name,
            "service_name": actual_service_name,
            "scene_url": f"{ISERVER_BASE}/iserver/services/{actual_service_name}/rest/realspace",
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
      "terrain_url": "http://localhost:8090/iserver/services/3D-luonan/rest/realspace/terrain",
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

    scene_url = f"{ISERVER_BASE}/iserver/services/{service_name}/rest/realspace"
    terrain_url = f"{scene_url}/terrain"

    # 从配置或数据库获取初始视角
    from server.config import CASE_STUDY

    return {
        "scene_url": scene_url,
        "terrain_url": terrain_url,
        "layers": [],  # TODO: 从场景数据解析图层
        "initial_view": {
            "longitude": CASE_STUDY["center_lon"],
            "latitude": CASE_STUDY["center_lat"],
            "height": 50000,
            "heading": 0,
            "pitch": -90,
        },
        "attribution": "SuperMap iServer 3D",
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

        # 尝试访问地形服务
        possible_names = [f"3D-{scene_name}", f"realspace-{scene_name}", scene_name]

        for service_name in possible_names:
            terrain_url = f"{ISERVER_BASE}/iserver/services/{service_name}/rest/realspace/terrain"

            try:
                response = session.get(f"{terrain_url}.json", timeout=5)

                if response.status_code == 200:
                    terrain_data = response.json()

                    return {
                        "status": "success",
                        "scene_name": scene_name,
                        "terrain_url": terrain_url,
                        "terrain_data": terrain_data,
                        "cache_format": "sct",
                        "note": "地形缓存需在SuperMap iDesktopX中生成",
                    }
            except Exception:
                continue

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
