"""数据编辑API路由 - iServer数据服务编辑功能

提供要素的增删改查功能，支持在线编辑GIS数据
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Any

from server.api.auth import get_current_user
from server.models.user import User
from server.integrations import iserver_client

router = APIRouter(prefix="/api/data-editing", tags=["data-editing"])


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class Feature(BaseModel):
    """要素模型"""
    geometry: dict = Field(..., description="GeoJSON几何对象")
    properties: dict[str, Any] = Field(default_factory=dict, description="属性字典")


class AddFeaturesRequest(BaseModel):
    """添加要素请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="数据集名称")
    features: list[Feature] = Field(..., description="要素列表")


class UpdateFeaturesRequest(BaseModel):
    """更新要素请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="数据集名称")
    features: list[Feature] = Field(..., description="要素列表（更新后的数据）")
    ids: list[int] = Field(..., description="要素ID列表（与features对应）")


class DeleteFeaturesRequest(BaseModel):
    """删除要素请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="数据集名称")
    ids: list[int] = Field(..., description="要删除的要素ID列表")


class QueryByIDsRequest(BaseModel):
    """按ID查询请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="数据集名称")
    ids: list[int] = Field(..., description="要素ID列表")


class QueryBySQLRequest(BaseModel):
    """SQL查询请求"""
    datasource: str = Field(..., description="数据源名称")
    dataset: str = Field(..., description="数据集名称")
    sql_filter: str = Field(..., description="SQL WHERE子句（不含WHERE）")
    max_features: int = Field(500, description="最大返回数量")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _convert_feature_to_iserver_format(feature: Feature) -> dict:
    """将前端Feature转换为iServer API格式"""
    field_names = list(feature.properties.keys())
    field_values = list(feature.properties.values())

    return {
        "geometry": feature.geometry,
        "fieldNames": field_names,
        "fieldValues": field_values,
    }


def _convert_iserver_feature_to_geojson(iserver_feature: dict) -> dict:
    """将iServer要素转换为GeoJSON Feature"""
    properties = {}

    # 解析属性字段
    field_names = iserver_feature.get("fieldNames", [])
    field_values = iserver_feature.get("fieldValues", [])

    for name, value in zip(field_names, field_values):
        properties[name] = value

    return {
        "type": "Feature",
        "geometry": iserver_feature.get("geometry"),
        "properties": properties,
        "id": iserver_feature.get("ID"),
    }


# ---------------------------------------------------------------------------
# 要素增删改路由
# ---------------------------------------------------------------------------

@router.post("/features/add", summary="添加要素")
async def add_features(
    request: AddFeaturesRequest,
    current_user: User = Depends(get_current_user),
):
    """
    向数据集添加新要素

    应用场景：
    - 用户在地图上绘制新地块
    - 导入外部数据
    - 批量添加标注点

    请求示例：
    ```json
    {
      "datasource": "user_12345_ds",
      "dataset": "my_parcels",
      "features": [
        {
          "geometry": {
            "type": "Polygon",
            "coordinates": [[[110.0, 34.0], [110.1, 34.0], [110.1, 34.1], [110.0, 34.1], [110.0, 34.0]]]
          },
          "properties": {
            "name": "地块A",
            "crop_type": "核桃",
            "area": 1500.5,
            "owner": "张三"
          }
        }
      ]
    }
    ```
    """
    if not request.features:
        raise HTTPException(status_code=400, detail="要素列表不能为空")

    # 转换为iServer格式
    iserver_features = [
        _convert_feature_to_iserver_format(f) for f in request.features
    ]

    # 调用iServer API
    result = iserver_client.add_features(
        datasource_name=request.datasource,
        dataset_name=request.dataset,
        features=iserver_features,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="添加要素失败，请检查数据源和数据集是否存在"
        )

    if not result.get("succeed"):
        raise HTTPException(
            status_code=500,
            detail=f"添加要素失败: {result.get('error', 'unknown error')}"
        )

    return {
        "status": "success",
        "message": f"成功添加 {result.get('featureCount', len(request.features))} 个要素",
        "feature_count": result.get("featureCount"),
        "result": result,
    }


@router.put("/features/update", summary="更新要素")
async def update_features(
    request: UpdateFeaturesRequest,
    current_user: User = Depends(get_current_user),
):
    """
    更新数据集中的要素（几何和属性）

    应用场景：
    - 修改地块边界
    - 更新属性信息
    - 批量修正数据

    注意：
    - features和ids数组长度必须相同
    - ids中的ID必须存在于数据集中
    """
    if len(request.features) != len(request.ids):
        raise HTTPException(
            status_code=400,
            detail=f"要素数量({len(request.features)})与ID数量({len(request.ids)})不匹配"
        )

    if not request.features:
        raise HTTPException(status_code=400, detail="要素列表不能为空")

    # 转换为iServer格式
    iserver_features = [
        _convert_feature_to_iserver_format(f) for f in request.features
    ]

    # 调用iServer API
    result = iserver_client.update_features(
        datasource_name=request.datasource,
        dataset_name=request.dataset,
        features=iserver_features,
        ids=request.ids,
    )

    if not result:
        raise HTTPException(status_code=500, detail="更新要素失败")

    if not result.get("succeed"):
        raise HTTPException(
            status_code=500,
            detail=f"更新要素失败: {result.get('error', 'unknown error')}"
        )

    return {
        "status": "success",
        "message": f"成功更新 {result.get('featureCount', len(request.features))} 个要素",
        "feature_count": result.get("featureCount"),
        "updated_ids": request.ids,
        "result": result,
    }


@router.delete("/features/delete", summary="删除要素")
async def delete_features(
    request: DeleteFeaturesRequest,
    current_user: User = Depends(get_current_user),
):
    """
    删除数据集中的要素

    应用场景：
    - 删除错误数据
    - 清理过期记录
    - 批量删除

    注意：
    - 删除操作不可撤销！
    - 建议删除前先备份数据
    """
    if not request.ids:
        raise HTTPException(status_code=400, detail="要素ID列表不能为空")

    # 调用iServer API
    result = iserver_client.delete_features(
        datasource_name=request.datasource,
        dataset_name=request.dataset,
        ids=request.ids,
    )

    if not result:
        raise HTTPException(status_code=500, detail="删除要素失败")

    if not result.get("succeed"):
        raise HTTPException(
            status_code=500,
            detail=f"删除要素失败: {result.get('error', 'unknown error')}"
        )

    return {
        "status": "success",
        "message": f"成功删除 {len(request.ids)} 个要素",
        "deleted_ids": request.ids,
        "result": result,
    }


# ---------------------------------------------------------------------------
# 要素查询路由
# ---------------------------------------------------------------------------

@router.post("/features/query-by-ids", summary="按ID查询要素")
async def query_features_by_ids(
    request: QueryByIDsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    根据要素ID查询详细信息

    应用场景：
    - 编辑前获取要素详情
    - 批量查询特定要素
    """
    if not request.ids:
        raise HTTPException(status_code=400, detail="ID列表不能为空")

    result = iserver_client.query_features_by_ids(
        datasource_name=request.datasource,
        dataset_name=request.dataset,
        ids=request.ids,
    )

    if not result:
        raise HTTPException(status_code=500, detail="查询要素失败")

    # 转换为GeoJSON格式
    features = result.get("features", [])
    geojson_features = [
        _convert_iserver_feature_to_geojson(f) for f in features
    ]

    return {
        "type": "FeatureCollection",
        "features": geojson_features,
        "count": len(geojson_features),
    }


@router.post("/features/query-by-sql", summary="SQL属性查询")
async def query_features_by_sql(
    request: QueryBySQLRequest,
    current_user: User = Depends(get_current_user),
):
    """
    SQL属性查询（支持复杂条件）

    应用场景：
    - 筛选特定属性的要素
    - 范围查询（面积、时间等）
    - 组合条件查询

    SQL示例：
    - `area > 1000 AND crop_type = '核桃'`
    - `owner LIKE '张%'`
    - `created_date >= '2023-01-01' AND area BETWEEN 500 AND 2000`
    - `status IN ('active', 'pending')`

    注意：
    - 字符串值需要用单引号
    - 字段名区分大小写（取决于数据库）
    """
    result = iserver_client.query_features_by_sql(
        datasource_name=request.datasource,
        dataset_name=request.dataset,
        sql_filter=request.sql_filter,
        max_features=request.max_features,
    )

    if not result:
        raise HTTPException(status_code=500, detail="SQL查询失败")

    # 转换为GeoJSON格式
    features = result.get("features", [])
    geojson_features = [
        _convert_iserver_feature_to_geojson(f) for f in features
    ]

    return {
        "type": "FeatureCollection",
        "features": geojson_features,
        "count": len(geojson_features),
        "sql_filter": request.sql_filter,
    }


# ---------------------------------------------------------------------------
# 批量编辑辅助路由
# ---------------------------------------------------------------------------

@router.post("/features/batch-update-attribute", summary="批量更新属性")
async def batch_update_attribute(
    datasource: str,
    dataset: str,
    ids: list[int],
    field_name: str,
    new_value: Any,
    current_user: User = Depends(get_current_user),
):
    """
    批量更新指定要素的某个属性字段

    应用场景：
    - 批量修改作物类型
    - 批量更新状态字段
    - 批量校正数据

    示例：将ID为[1,2,3]的地块的crop_type改为"核桃"
    ```
    POST /api/data-editing/features/batch-update-attribute
    {
      "datasource": "user_ds",
      "dataset": "parcels",
      "ids": [1, 2, 3],
      "field_name": "crop_type",
      "new_value": "核桃"
    }
    ```
    """
    if not ids:
        raise HTTPException(status_code=400, detail="ID列表不能为空")

    # 先查询现有要素
    query_result = iserver_client.query_features_by_ids(
        datasource_name=datasource,
        dataset_name=dataset,
        ids=ids,
    )

    if not query_result or "features" not in query_result:
        raise HTTPException(status_code=404, detail="要素不存在")

    # 构造更新后的要素列表
    updated_features = []
    for feature in query_result["features"]:
        # 保持原有属性
        field_names = feature.get("fieldNames", [])
        field_values = feature.get("fieldValues", [])

        # 更新目标字段
        if field_name in field_names:
            idx = field_names.index(field_name)
            field_values[idx] = new_value
        else:
            # 如果字段不存在，添加新字段
            field_names.append(field_name)
            field_values.append(new_value)

        updated_features.append({
            "geometry": feature.get("geometry"),
            "fieldNames": field_names,
            "fieldValues": field_values,
        })

    # 执行更新
    result = iserver_client.update_features(
        datasource_name=datasource,
        dataset_name=dataset,
        features=updated_features,
        ids=ids,
    )

    if not result or not result.get("succeed"):
        raise HTTPException(status_code=500, detail="批量更新失败")

    return {
        "status": "success",
        "message": f"成功将 {len(ids)} 个要素的 '{field_name}' 字段更新为 '{new_value}'",
        "updated_count": len(ids),
        "field_name": field_name,
        "new_value": new_value,
    }
