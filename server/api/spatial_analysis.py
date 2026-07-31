"""空间分析API路由 - iServer空间分析服务封装

提供地形分析、密度分析、栅格叠加、插值分析等高级空间分析功能
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any, Optional

from server.api.auth import get_current_user
from server.models.user import User
from server.integrations import iserver_client

router = APIRouter(prefix="/api/spatial-analysis", tags=["spatial-analysis"])


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class TerrainSlopeRequest(BaseModel):
    """地形坡度分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="DEM数据集名称")
    slope_type: str = Field("DEGREE", description="坡度类型: DEGREE 或 PERCENT_RISE")
    z_factor: float = Field(1.0, description="高程单位转换因子")


class TerrainAspectRequest(BaseModel):
    """地形坡向分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="DEM数据集名称")


class TerrainHillshadeRequest(BaseModel):
    """山体阴影分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="DEM数据集名称")
    azimuth: float = Field(315.0, description="光源方位角（0-360度）")
    altitude: float = Field(45.0, description="光源高度角（0-90度）")


class KernelDensityRequest(BaseModel):
    """核密度分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="点数据集名称")
    search_radius: float = Field(..., description="搜索半径（米）")
    cell_size: Optional[float] = Field(None, description="栅格像元大小（米）")
    population_field: Optional[str] = Field(None, description="权重字段名")


class PointDensityRequest(BaseModel):
    """点密度分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="点数据集名称")
    cell_size: float = Field(..., description="栅格像元大小（米）")
    search_radius: float = Field(..., description="搜索半径（米）")
    population_field: Optional[str] = Field(None, description="权重字段名")


class ReclassItem(BaseModel):
    """重分类规则"""
    min: float
    max: float
    new_value: int


class WeightedOverlayLayer(BaseModel):
    """加权叠加图层"""
    dataset: str = Field(..., description="栅格数据集名称")
    weight: float = Field(..., description="权重（0-1）")
    reclass_table: list[ReclassItem] = Field(default_factory=list, description="重分类表")


class WeightedOverlayRequest(BaseModel):
    """加权叠加分析请求"""
    datasource: str = Field(..., description="数据源名称")
    layers: list[WeightedOverlayLayer] = Field(..., description="叠加图层列表")
    output_dataset: Optional[str] = Field(None, description="输出数据集名称")


class InterpolationIDWRequest(BaseModel):
    """IDW插值分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="点数据集名称")
    z_field: str = Field(..., description="高程/值字段名")
    cell_size: float = Field(..., description="栅格像元大小")
    power: float = Field(2.0, description="距离幂次")
    search_radius: Optional[float] = Field(None, description="搜索半径")


class InterpolationKrigingRequest(BaseModel):
    """Kriging插值分析请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="点数据集名称")
    z_field: str = Field(..., description="高程/值字段名")
    cell_size: float = Field(..., description="栅格像元大小")
    variogram_type: str = Field("SPHERICAL", description="变异函数类型")


class NativeSpatialOperationRequest(BaseModel):
    """Pass-through request for a discovered iServer Spatial Analyst operation."""
    operation_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    dataset_path: Optional[str] = None


@router.get("/native-catalog", summary="发现已发布的原生空间分析算子")
async def native_catalog():
    try:
        return iserver_client.list_native_spatial_operations()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"无法读取 iServer 原生算子目录: {exc}") from exc


@router.post("/native-execute", summary="执行原生空间分析算子")
async def execute_native_operation(
    request: NativeSpatialOperationRequest,
    current_user: User = Depends(get_current_user),
):
    del current_user
    try:
        result = iserver_client.execute_native_spatial_operation(
            request.operation_id,
            request.parameters,
            request.dataset_path,
        )
        return {"status": "success", "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 地形分析路由
# ---------------------------------------------------------------------------

@router.post("/terrain/slope", summary="地形坡度分析")
async def analyze_slope(
    request: TerrainSlopeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    DEM坡度分析 - 计算地表坡度（度或百分比）

    应用场景：
    - 核桃种植适宜性评价（适宜坡度15-25°）
    - 水土保持分析
    - 建设用地选址
    """
    result = iserver_client.terrain_slope(
        datasource=request.datasource,
        dataset=request.dataset,
        slope_type=request.slope_type,
        z_factor=request.z_factor,
    )

    if not result:
        raise HTTPException(status_code=500, detail="坡度分析失败，请检查iServer服务和数据集")

    if not result.get("succeed"):
        raise HTTPException(
            status_code=500,
            detail=f"坡度分析失败: {result.get('error', 'unknown error')}"
        )

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "坡度分析完成",
        "result": result,
    }


@router.post("/terrain/aspect", summary="地形坡向分析")
async def analyze_aspect(
    request: TerrainAspectRequest,
    current_user: User = Depends(get_current_user),
):
    """
    DEM坡向分析 - 计算地表朝向（0-360度）

    应用场景：
    - 日照分析（南坡光照充足）
    - 风向影响评估
    - 小气候研究
    """
    result = iserver_client.terrain_aspect(
        datasource=request.datasource,
        dataset=request.dataset,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="坡向分析失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "坡向分析完成",
        "result": result,
    }


@router.post("/terrain/hillshade", summary="山体阴影分析")
async def analyze_hillshade(
    request: TerrainHillshadeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    山体阴影分析 - 生成地形晕渲图

    应用场景：
    - 地图制图（地形可视化）
    - 地形特征识别
    - 三维场景准备
    """
    result = iserver_client.terrain_hillshade(
        datasource=request.datasource,
        dataset=request.dataset,
        azimuth=request.azimuth,
        altitude=request.altitude,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="山体阴影分析失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "山体阴影分析完成",
        "result": result,
    }


# ---------------------------------------------------------------------------
# 密度分析路由
# ---------------------------------------------------------------------------

@router.post("/density/kernel", summary="核密度分析")
async def analyze_kernel_density(
    request: KernelDensityRequest,
    current_user: User = Depends(get_current_user),
):
    """
    核密度分析 - 计算点要素的空间密度分布

    应用场景：
    - 历史核桃种植点密度分析
    - 热点区域识别
    - 空间聚集模式分析

    推荐参数：
    - search_radius: 1000-5000米（根据研究尺度）
    - cell_size: 100-500米（影响输出精度）
    """
    result = iserver_client.kernel_density(
        datasource=request.datasource,
        dataset=request.dataset,
        search_radius=request.search_radius,
        cell_size=request.cell_size,
        population_field=request.population_field,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="核密度分析失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "核密度分析完成",
        "result": result,
        "tip": "结果为栅格数据集，值越大表示密度越高",
    }


@router.post("/density/point", summary="点密度分析")
async def analyze_point_density(
    request: PointDensityRequest,
    current_user: User = Depends(get_current_user),
):
    """
    点密度分析 - 计算单位面积内的点数量

    应用场景：
    - 种植密度统计
    - 设施分布密度
    - 人口密度估算
    """
    result = iserver_client.point_density(
        datasource=request.datasource,
        dataset=request.dataset,
        cell_size=request.cell_size,
        search_radius=request.search_radius,
        population_field=request.population_field,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="点密度分析失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "点密度分析完成",
        "result": result,
    }


# ---------------------------------------------------------------------------
# 栅格叠加分析路由
# ---------------------------------------------------------------------------

@router.post("/overlay/weighted", summary="栅格加权叠加")
async def analyze_weighted_overlay(
    request: WeightedOverlayRequest,
    current_user: User = Depends(get_current_user),
):
    """
    栅格加权叠加分析 - 多因子综合评价

    应用场景：
    - **核桃种植适宜性综合评价**（坡度 40% + 坡向 30% + 土壤 30%）
    - 选址决策
    - 多准则评估

    使用步骤：
    1. 准备多个评价因子栅格（坡度、坡向、土壤等）
    2. 对每个栅格进行重分类（统一到相同等级，如1-10）
    3. 设置权重（总和为1.0）
    4. 执行加权叠加

    示例：
    ```json
    {
      "datasource": "luonan_ds",
      "layers": [
        {
          "dataset": "slope_reclass",
          "weight": 0.4,
          "reclass_table": [
            {"min": 0, "max": 15, "new_value": 3},
            {"min": 15, "max": 25, "new_value": 10},
            {"min": 25, "max": 35, "new_value": 5}
          ]
        },
        {
          "dataset": "aspect_reclass",
          "weight": 0.3
        },
        {
          "dataset": "soil_reclass",
          "weight": 0.3
        }
      ]
    }
    ```
    """
    # 验证权重总和
    total_weight = sum(layer.weight for layer in request.layers)
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"权重总和必须为1.0，当前为{total_weight}"
        )

    # 构造iServer API参数
    rasters = [
        {
            "dataset": layer.dataset,
            "reclassTable": [
                {"min": item.min, "max": item.max, "newValue": item.new_value}
                for item in layer.reclass_table
            ] if layer.reclass_table else []
        }
        for layer in request.layers
    ]
    weights = [layer.weight for layer in request.layers]

    result = iserver_client.weighted_overlay(
        datasource=request.datasource,
        rasters=rasters,
        weights=weights,
        output_dataset=request.output_dataset,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="加权叠加分析失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "加权叠加分析完成",
        "result": result,
        "tip": "结果值为各图层加权总和，值越高表示越适宜",
    }


# ---------------------------------------------------------------------------
# 插值分析路由
# ---------------------------------------------------------------------------

@router.post("/interpolation/idw", summary="IDW反距离权重插值")
async def interpolate_idw(
    request: InterpolationIDWRequest,
    current_user: User = Depends(get_current_user),
):
    """
    IDW插值 - 根据采样点生成连续表面

    应用场景：
    - 气温、降雨量空间分布
    - 土壤属性插值
    - 地下水位预测

    特点：
    - 简单快速
    - 适合均匀分布的采样点
    - 不能外推（结果范围在采样点范围内）
    """
    result = iserver_client.interpolation_idw(
        datasource=request.datasource,
        dataset=request.dataset,
        z_field=request.z_field,
        cell_size=request.cell_size,
        power=request.power,
        search_radius=request.search_radius,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="IDW插值失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "IDW插值完成",
        "result": result,
    }


@router.post("/interpolation/kriging", summary="Kriging克里金插值")
async def interpolate_kriging(
    request: InterpolationKrigingRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Kriging插值 - 基于空间自相关的最优插值

    应用场景：
    - 地质勘探
    - 土壤养分预测
    - 高精度气象插值

    特点：
    - 考虑空间自相关性
    - 提供预测误差估计
    - 适合不均匀分布的采样点
    - 计算较慢
    """
    result = iserver_client.interpolation_kriging(
        datasource=request.datasource,
        dataset=request.dataset,
        z_field=request.z_field,
        cell_size=request.cell_size,
        variogram_type=request.variogram_type,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="Kriging插值失败")

    return {
        "status": "success",
        "result_id": result.get("newResourceID"),
        "message": "Kriging插值完成",
        "result": result,
    }


# ---------------------------------------------------------------------------
# 分析任务状态查询
# ---------------------------------------------------------------------------

@router.get("/tasks/{task_id}", summary="查询分析任务状态")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    查询异步分析任务的执行状态

    注意：某些大数据量分析会异步执行，需要通过此接口轮询结果
    """
    # TODO: 实现任务状态查询（需要iServer任务管理接口）
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "任务状态查询功能待实现",
    }
