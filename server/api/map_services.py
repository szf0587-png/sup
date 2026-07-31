"""地图服务API路由 - iServer地图服务集成

提供地图服务列表、瓦片URL、图层管理等功能，替代OSM底图
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from server.api.auth import get_current_user
from server.models.user import User
from server.integrations import iserver_client
from server.config import ISERVER_BASE

router = APIRouter(prefix="/api/map-services", tags=["map-services"])


# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------

class MapServiceInfo(BaseModel):
    """地图服务信息"""
    service_name: str
    service_url: str
    maps: list[str]
    description: Optional[str] = None


class TileLayerConfig(BaseModel):
    """瓦片图层配置（供前端Leaflet使用）"""
    tile_url: str = Field(..., description="WMTS瓦片URL模板")
    service_name: str
    map_name: str
    attribution: str = Field(default="SuperMap iServer", description="版权信息")
    min_zoom: int = Field(default=3, description="最小缩放级别")
    max_zoom: int = Field(default=11, description="最大缩放级别")
    bounds: Optional[list[list[float]]] = Field(None, description="地图范围[[south,west],[north,east]]")


# ---------------------------------------------------------------------------
# 地图服务路由
# ---------------------------------------------------------------------------

@router.get("/list", summary="列出所有地图服务")
async def list_map_services(
    current_user: User = Depends(get_current_user),
):
    """
    列出iServer上所有可用的地图服务

    返回示例：
    ```json
    {
      "services": [
        {
          "service_name": "luonan-base",
          "service_url": "http://localhost:8090/iserver/services/map-luonan-base/rest",
          "maps": ["洛南县底图", "洛南县影像"],
          "description": "洛南县基础底图服务"
        }
      ]
    }
    ```
    """
    try:
        # 调用iServer REST API获取服务列表
        session = iserver_client._get_session()
        response = session.get(f"{ISERVER_BASE}/iserver/services.json", timeout=10)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="无法连接iServer")

        data = response.json()
        services = []

        # 过滤出地图服务
        for service in data:
            service_name = service.get("name", "")
            if service_name.startswith("map-"):
                # 服务目录可能是 map-China100/rest；元数据接口只接受已发布服务名。
                published_name = service_name.split("/", 1)[0]
                clean_name = published_name[4:]

                # 获取该服务的详细信息
                map_info = iserver_client.get_map_service(clean_name)
                maps = []

                if map_info:
                    if isinstance(map_info, list):
                        maps = [m if isinstance(m, str) else m.get("name", "") for m in map_info]
                    elif isinstance(map_info, dict):
                        maps_data = map_info.get("maps", [])
                        maps = [m if isinstance(m, str) else m.get("name", "") for m in maps_data]

                services.append({
                    "service_name": clean_name,
                    "service_url": f"{ISERVER_BASE}/iserver/services/map-{clean_name}/rest",
                    "maps": maps,
                    "description": service.get("description"),
                })

        return {
            "status": "success",
            "count": len(services),
            "services": services,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地图服务列表失败: {str(e)}")


@router.get("/{service_name}", summary="获取地图服务详情")
async def get_map_service_info(
    service_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取指定地图服务的详细信息

    参数：
    - service_name: 地图服务名称（不含 "map-" 前缀）

    返回：
    - 地图列表、范围、坐标系等元数据
    """
    result = iserver_client.get_map_service(service_name)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"地图服务 '{service_name}' 不存在或不可访问"
        )

    return {
        "status": "success",
        "service_name": service_name,
        "data": result,
    }


@router.get("/{service_name}/tile-config", summary="获取瓦片图层配置")
async def get_tile_layer_config(
    service_name: str,
    map_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    获取Leaflet瓦片图层配置（供前端直接使用）

    参数：
    - service_name: 地图服务名称
    - map_name: 地图名称（可选，默认使用第一个地图）

    返回示例：
    ```json
    {
      "tile_url": "http://localhost:8090/iserver/services/map-luonan/rest/maps/洛南县/zxyTileImage.png?z={z}&x={x}&y={y}&width=256&height=256",
      "service_name": "luonan",
      "map_name": "洛南县",
      "attribution": "SuperMap iServer",
      "min_zoom": 3,
      "max_zoom": 11,
      "bounds": [[33.5, 109.5], [34.5, 110.5]]
    }
    ```

    前端使用（Leaflet）：
    ```javascript
    const config = await fetch('/api/map-services/luonan/tile-config').then(r => r.json());
    L.tileLayer(config.tile_url, {
        attribution: config.attribution,
        minZoom: config.min_zoom,
        maxZoom: config.max_zoom,
        bounds: config.bounds ? L.latLngBounds(config.bounds) : null
    }).addTo(map);
    ```
    """
    # 获取地图服务信息
    map_info = iserver_client.get_map_service(service_name)

    if not map_info:
        raise HTTPException(
            status_code=404,
            detail=f"地图服务 '{service_name}' 不存在"
        )

    # 解析地图列表
    maps = []
    bounds = None

    if isinstance(map_info, list):
        maps = [m if isinstance(m, str) else m.get("name", "") for m in map_info]
    elif isinstance(map_info, dict):
        maps_data = map_info.get("maps", [])
        maps = [m if isinstance(m, str) else m.get("name", "") for m in maps_data]

        # 尝试提取地图范围
        if maps_data and isinstance(maps_data[0], dict):
            first_map = maps_data[0]
            if "bounds" in first_map:
                b = first_map["bounds"]
                # iServer bounds格式: {"left": x1, "bottom": y1, "right": x2, "top": y2}
                bounds = [
                    [b.get("bottom"), b.get("left")],
                    [b.get("top"), b.get("right")]
                ]

    if not maps:
        raise HTTPException(
            status_code=404,
            detail=f"地图服务 '{service_name}' 中没有可用的地图"
        )

    # 确定使用的地图名称
    target_map = map_name if map_name else maps[0]

    if map_name and map_name not in maps:
        raise HTTPException(
            status_code=404,
            detail=f"地图 '{map_name}' 在服务 '{service_name}' 中不存在。可用地图: {', '.join(maps)}"
        )

    # 生成瓦片URL
    tile_url = iserver_client.get_map_tile_url(service_name, target_map)

    if not tile_url:
        raise HTTPException(
            status_code=500,
            detail="生成瓦片URL失败"
        )

    return {
        "tile_url": tile_url,
        "service_name": service_name,
        "map_name": target_map,
        "available_maps": maps,
        "attribution": f"SuperMap iServer - {service_name}",
        "min_zoom": 3,
        "max_zoom": 11,
        "bounds": bounds,
    }


@router.get("/{service_name}/maps", summary="列出地图服务中的所有地图")
async def list_maps_in_service(
    service_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    列出指定地图服务中的所有地图

    用于前端地图切换功能
    """
    map_info = iserver_client.get_map_service(service_name)

    if not map_info:
        raise HTTPException(
            status_code=404,
            detail=f"地图服务 '{service_name}' 不存在"
        )

    maps = []

    if isinstance(map_info, list):
        maps = [
            {
                "name": m if isinstance(m, str) else m.get("name", ""),
                "description": m.get("description") if isinstance(m, dict) else None,
            }
            for m in map_info
        ]
    elif isinstance(map_info, dict):
        maps_data = map_info.get("maps", [])
        maps = [
            {
                "name": m if isinstance(m, str) else m.get("name", ""),
                "description": m.get("description") if isinstance(m, dict) else None,
                "bounds": m.get("bounds") if isinstance(m, dict) else None,
            }
            for m in maps_data
        ]

    return {
        "status": "success",
        "service_name": service_name,
        "count": len(maps),
        "maps": maps,
    }


# ---------------------------------------------------------------------------
# 底图推荐
# ---------------------------------------------------------------------------

@router.get("/recommendations/basemaps", summary="推荐底图配置")
async def get_basemap_recommendations(
    current_user: User = Depends(get_current_user),
):
    """
    返回推荐的底图配置（iServer + 备用OSM）

    前端可以根据此配置自动切换底图：
    1. 优先使用iServer地图服务（离线、定制）
    2. 如果iServer不可用，回退到OSM（需要外网）
    """
    basemaps = []

    # 检查iServer是否可用
    iserver_available = iserver_client.check_iserver()

    if iserver_available:
        # 获取所有地图服务
        try:
            session = iserver_client._get_session()
            response = session.get(f"{ISERVER_BASE}/iserver/services.json", timeout=5)

            if response.status_code == 200:
                data = response.json()

                for service in data:
                    service_name = service.get("name", "")
                    if service_name.startswith("map-"):
                        clean_name = service_name.split("/", 1)[0][4:]
                        tile_url = iserver_client.get_map_tile_url(clean_name, "")

                        if tile_url:
                            basemaps.append({
                                "id": f"iserver-{clean_name}",
                                "name": f"iServer - {clean_name}",
                                "type": "iserver",
                                "tile_url": tile_url,
                                "attribution": "SuperMap iServer",
                                "available": True,
                            })
        except Exception as e:
            print(f"[map_services] 获取iServer地图服务失败: {e}")

    # 添加OSM备用底图
    basemaps.append({
        "id": "osm-standard",
        "name": "OpenStreetMap（备用）",
        "type": "osm",
        "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        "available": True,
        "note": "需要外网连接",
    })

    return {
        "status": "success",
        "iserver_available": iserver_available,
        "basemaps": basemaps,
        "recommendation": basemaps[0]["id"] if basemaps else "osm-standard",
    }
