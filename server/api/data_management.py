"""数据管理API路由 - 数据集元数据、属性表、导入导出

提供完整的数据管理功能，包括字段管理、属性表CRUD、多格式导入导出
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, Any
import json
import uuid
from pathlib import Path

from server.api.auth import get_current_user
from server.models.user import User
from server.config import DATA_DIR

router = APIRouter(prefix="/api/data-management", tags=["data-management"])


# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------

class FieldInfo(BaseModel):
    """字段信息"""
    name: str
    type: str  # TEXT, INTEGER, DOUBLE, DATE, BOOLEAN
    length: Optional[int] = None
    required: bool = False
    default_value: Optional[Any] = None


class DatasetMetadata(BaseModel):
    """数据集元数据"""
    name: str
    type: str  # POINT, LINE, REGION, TEXT
    record_count: int
    bounds: Optional[dict] = None
    coordinate_system: Optional[str] = None
    fields: list[FieldInfo]


class AddFieldRequest(BaseModel):
    """添加字段请求"""
    datasource: str
    dataset: str
    field_name: str
    field_type: str = Field(..., description="TEXT/INTEGER/DOUBLE/DATE/BOOLEAN")
    field_length: int = Field(254, description="字段长度（TEXT类型）")
    default_value: Optional[Any] = None


class ImportRequest(BaseModel):
    """数据导入请求"""
    format: str = Field(..., description="geojson/csv/excel")
    target_datasource: str = Field(..., description="目标数据源名称")
    target_dataset: Optional[str] = Field(None, description="目标数据集名称（自动生成）")
    encoding: str = Field("utf-8", description="文件编码")


class ExportRequest(BaseModel):
    """数据导出请求"""
    datasource: str
    dataset: str
    format: str = Field(..., description="geojson/shapefile/excel/csv")
    sql_filter: Optional[str] = Field(None, description="SQL过滤条件")


# ---------------------------------------------------------------------------
# 数据集元数据路由
# ---------------------------------------------------------------------------

@router.get("/datasets/{datasource}/{dataset}/metadata", summary="获取数据集元数据")
async def get_dataset_metadata(
    datasource: str,
    dataset: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取数据集的完整元数据信息

    包含：
    - 数据集名称和类型
    - 记录数量
    - 空间范围
    - 坐标系
    - 字段列表（名称、类型、长度）

    应用场景：
    - 数据浏览器
    - 属性表设计
    - 数据质量检查
    """
    try:
        # 使用iobjectspy读取数据集元数据
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource

        # 假设datasource是UDBX路径或别名
        # 实际项目中需要从数据库查询用户的数据源配置
        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{datasource}.udbx"

        if not udbx_path.exists():
            raise HTTPException(status_code=404, detail=f"数据源 '{datasource}' 不存在")

        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)

        if ds is None:
            raise HTTPException(status_code=500, detail="无法打开数据源")

        # 获取数据集
        dv = ds[dataset]
        if dv is None:
            ds.close()
            raise HTTPException(status_code=404, detail=f"数据集 '{dataset}' 不存在")

        # 读取元数据
        metadata = {
            "name": dv.name,
            "type": str(dv.type).split(".")[-1],  # POINT, LINE, REGION等
            "record_count": dv.record_count,
            "bounds": {
                "left": dv.bounds.left,
                "bottom": dv.bounds.bottom,
                "right": dv.bounds.right,
                "top": dv.bounds.top,
            } if dv.bounds else None,
            "coordinate_system": str(dv.prj_coordsys) if dv.prj_coordsys else None,
            "fields": [],
        }

        # 读取字段信息
        for field_info in dv.field_infos:
            metadata["fields"].append({
                "name": field_info.name,
                "type": str(field_info.type).split(".")[-1],
                "length": field_info.max_length if hasattr(field_info, "max_length") else None,
                "required": field_info.is_required if hasattr(field_info, "is_required") else False,
            })

        ds.close()

        return {
            "status": "success",
            "metadata": metadata,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取元数据失败: {str(e)}")


@router.get("/datasets/{datasource}/list", summary="列出数据源中的所有数据集")
async def list_datasets_in_datasource(
    datasource: str,
    current_user: User = Depends(get_current_user),
):
    """
    列出指定数据源中的所有数据集

    返回：
    - 数据集名称列表
    - 每个数据集的类型和记录数
    """
    try:
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{datasource}.udbx"

        if not udbx_path.exists():
            raise HTTPException(status_code=404, detail=f"数据源 '{datasource}' 不存在")

        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)

        if ds is None:
            raise HTTPException(status_code=500, detail="无法打开数据源")

        datasets = []
        for dv in ds.datasets:
            datasets.append({
                "name": dv.name,
                "type": str(dv.type).split(".")[-1],
                "record_count": dv.record_count,
            })

        ds.close()

        return {
            "status": "success",
            "datasource": datasource,
            "count": len(datasets),
            "datasets": datasets,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出数据集失败: {str(e)}")


# ---------------------------------------------------------------------------
# 字段管理路由
# ---------------------------------------------------------------------------

@router.post("/fields/add", summary="添加字段")
async def add_field_to_dataset(
    request: AddFieldRequest,
    current_user: User = Depends(get_current_user),
):
    """
    向数据集添加新字段

    应用场景：
    - 扩展属性结构
    - 添加计算字段
    - 数据迁移准备

    支持的字段类型：
    - TEXT: 文本（需指定length）
    - INTEGER: 整数
    - DOUBLE: 浮点数
    - DATE: 日期
    - BOOLEAN: 布尔值
    """
    try:
        from iobjectspy.data import (
            DatasourceConnectionInfo, open_datasource,
            FieldInfo as IFieldInfo, FieldType
        )

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{request.datasource}.udbx"

        if not udbx_path.exists():
            raise HTTPException(status_code=404, detail="数据源不存在")

        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)

        if ds is None:
            raise HTTPException(status_code=500, detail="无法打开数据源")

        dv = ds[request.dataset]
        if dv is None:
            ds.close()
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 映射字段类型
        type_map = {
            "TEXT": FieldType.TEXT,
            "INTEGER": FieldType.INT32,
            "DOUBLE": FieldType.DOUBLE,
            "DATE": FieldType.DATETIME,
            "BOOLEAN": FieldType.BOOLEAN,
        }

        if request.field_type not in type_map:
            ds.close()
            raise HTTPException(
                status_code=400,
                detail=f"不支持的字段类型: {request.field_type}"
            )

        # 创建字段信息
        field_info = IFieldInfo(
            name=request.field_name,
            type=type_map[request.field_type]
        )

        if request.field_type == "TEXT":
            field_info.max_length = request.field_length

        # 添加字段
        success = dv.field_infos.add(field_info)

        ds.close()

        if not success:
            raise HTTPException(status_code=500, detail="添加字段失败")

        return {
            "status": "success",
            "message": f"成功添加字段 '{request.field_name}'",
            "field_name": request.field_name,
            "field_type": request.field_type,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加字段失败: {str(e)}")


# ---------------------------------------------------------------------------
# 属性表查询路由
# ---------------------------------------------------------------------------

@router.get("/records/{datasource}/{dataset}", summary="查询属性表记录")
async def get_records(
    datasource: str,
    dataset: str,
    page: int = 1,
    page_size: int = 100,
    sql_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    分页查询数据集的属性表记录

    参数：
    - page: 页码（从1开始）
    - page_size: 每页记录数（最大1000）
    - sql_filter: SQL WHERE子句（可选）

    返回：
    - 记录列表（GeoJSON Feature格式）
    - 总记录数
    - 分页信息

    应用场景：
    - 属性表浏览器
    - 数据导出预览
    - 批量编辑准备
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于0")

    if page_size > 1000:
        raise HTTPException(status_code=400, detail="每页最大1000条记录")

    try:
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{datasource}.udbx"

        if not udbx_path.exists():
            raise HTTPException(status_code=404, detail="数据源不存在")

        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)

        if ds is None:
            raise HTTPException(status_code=500, detail="无法打开数据源")

        dv = ds[dataset]
        if dv is None:
            ds.close()
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 查询记录
        if sql_filter:
            rs = dv.query(sql_filter)
        else:
            rs = dv.query()

        # 获取总记录数
        total_count = dv.record_count

        # 跳过前面的记录（分页）
        skip_count = (page - 1) * page_size
        current = 0

        while current < skip_count and rs.has_next():
            rs.move_next()
            current += 1

        # 读取当前页记录
        records = []
        read_count = 0

        while rs.has_next() and read_count < page_size:
            rs.move_next()
            geometry = rs.get_geometry()

            properties = {}
            for field_info in dv.field_infos:
                try:
                    properties[field_info.name] = rs.get_value(field_info.name)
                except Exception:
                    properties[field_info.name] = None

            records.append({
                "type": "Feature",
                "geometry": json.loads(geometry.to_json()) if geometry else None,
                "properties": properties,
                "id": properties.get("SMID"),
            })

            read_count += 1

        rs.close()
        ds.close()

        return {
            "type": "FeatureCollection",
            "features": records,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询记录失败: {str(e)}")


# ---------------------------------------------------------------------------
# 数据导入路由
# ---------------------------------------------------------------------------

@router.post("/import/geojson", summary="导入GeoJSON")
async def import_geojson(
    file: UploadFile = File(...),
    target_datasource: str = None,
    target_dataset: str = None,
    current_user: User = Depends(get_current_user),
):
    """
    导入GeoJSON文件到数据集

    步骤：
    1. 上传GeoJSON文件
    2. 解析并验证
    3. 导入到UDBX数据源
    4. 发布到iServer（可选）

    返回：
    - 导入的要素数量
    - 新数据集名称
    - iServer服务URL（如果发布）
    """
    try:
        # 保存上传文件
        upload_dir = DATA_DIR / "uploads" / str(current_user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_path = upload_dir / f"{uuid.uuid4()}.geojson"
        content = await file.read()
        temp_path.write_bytes(content)

        # 解析GeoJSON
        data = json.loads(content.decode("utf-8"))

        if data.get("type") != "FeatureCollection":
            temp_path.unlink()
            raise HTTPException(status_code=400, detail="只支持FeatureCollection格式")

        features = data.get("features", [])
        if not features:
            temp_path.unlink()
            raise HTTPException(status_code=400, detail="GeoJSON为空")

        # 确定目标数据源和数据集
        if not target_datasource:
            target_datasource = f"user_{current_user.id}_ds"

        if not target_dataset:
            target_dataset = f"import_{uuid.uuid4().hex[:8]}"

        # 导入到UDBX
        from server.integrations.udbx_publisher import geojson_to_udbx

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{target_datasource}.udbx"
        udbx_path.parent.mkdir(parents=True, exist_ok=True)

        success = geojson_to_udbx(
            geojson_path=temp_path,
            udbx_path=udbx_path,
            dataset_name=target_dataset,
        )

        if not success:
            temp_path.unlink()
            raise HTTPException(status_code=500, detail="导入UDBX失败")

        # 清理临时文件
        temp_path.unlink()

        return {
            "status": "success",
            "message": f"成功导入 {len(features)} 个要素",
            "feature_count": len(features),
            "datasource": target_datasource,
            "dataset": target_dataset,
            "udbx_path": str(udbx_path),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/import/csv", summary="导入CSV（带坐标）")
async def import_csv(
    file: UploadFile = File(...),
    lon_field: str = "longitude",
    lat_field: str = "latitude",
    target_datasource: str = None,
    target_dataset: str = None,
    current_user: User = Depends(get_current_user),
):
    """
    导入CSV文件（包含经纬度坐标）

    要求：
    - CSV必须包含经纬度字段
    - 第一行为字段名
    - UTF-8编码

    参数：
    - lon_field: 经度字段名（默认"longitude"）
    - lat_field: 纬度字段名（默认"latitude"）
    """
    try:
        import csv
        import io

        # 读取CSV
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        # 转换为GeoJSON
        features = []
        for row in reader:
            if lon_field not in row or lat_field not in row:
                raise HTTPException(
                    status_code=400,
                    detail=f"CSV缺少坐标字段: {lon_field}, {lat_field}"
                )

            try:
                lon = float(row[lon_field])
                lat = float(row[lat_field])
            except ValueError:
                continue  # 跳过无效坐标

            # 创建Feature
            properties = {k: v for k, v in row.items() if k not in [lon_field, lat_field]}

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": properties,
            })

        if not features:
            raise HTTPException(status_code=400, detail="没有有效的坐标数据")

        # 保存为临时GeoJSON
        geojson_data = {
            "type": "FeatureCollection",
            "features": features,
        }

        upload_dir = DATA_DIR / "uploads" / str(current_user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_path = upload_dir / f"{uuid.uuid4()}.geojson"
        temp_path.write_text(json.dumps(geojson_data, ensure_ascii=False), encoding="utf-8")

        # 导入UDBX
        from server.integrations.udbx_publisher import geojson_to_udbx

        if not target_datasource:
            target_datasource = f"user_{current_user.id}_ds"

        if not target_dataset:
            target_dataset = f"csv_import_{uuid.uuid4().hex[:8]}"

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{target_datasource}.udbx"
        udbx_path.parent.mkdir(parents=True, exist_ok=True)

        success = geojson_to_udbx(
            geojson_path=temp_path,
            udbx_path=udbx_path,
            dataset_name=target_dataset,
        )

        temp_path.unlink()

        if not success:
            raise HTTPException(status_code=500, detail="导入UDBX失败")

        return {
            "status": "success",
            "message": f"成功导入 {len(features)} 个点要素",
            "feature_count": len(features),
            "datasource": target_datasource,
            "dataset": target_dataset,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV导入失败: {str(e)}")


# ---------------------------------------------------------------------------
# 数据导出路由
# ---------------------------------------------------------------------------

@router.post("/export/geojson", summary="导出为GeoJSON")
async def export_to_geojson(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    """
    将数据集导出为GeoJSON格式

    返回下载URL或文件内容
    """
    try:
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource

        udbx_path = DATA_DIR / "users" / str(current_user.id) / f"{request.datasource}.udbx"

        if not udbx_path.exists():
            raise HTTPException(status_code=404, detail="数据源不存在")

        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)

        if ds is None:
            raise HTTPException(status_code=500, detail="无法打开数据源")

        dv = ds[request.dataset]
        if dv is None:
            ds.close()
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 查询要素
        if request.sql_filter:
            rs = dv.query(request.sql_filter)
        else:
            rs = dv.query()

        # 转换为GeoJSON
        features = []
        while rs.has_next():
            rs.move_next()
            geometry = rs.get_geometry()

            properties = {}
            for field_info in dv.field_infos:
                try:
                    properties[field_info.name] = rs.get_value(field_info.name)
                except Exception:
                    properties[field_info.name] = None

            features.append({
                "type": "Feature",
                "geometry": json.loads(geometry.to_json()) if geometry else None,
                "properties": properties,
            })

        rs.close()
        ds.close()

        geojson_data = {
            "type": "FeatureCollection",
            "features": features,
        }

        # 保存文件
        export_dir = DATA_DIR / "exports" / str(current_user.id)
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{request.dataset}_{uuid.uuid4().hex[:8]}.geojson"
        export_path = export_dir / filename

        export_path.write_text(
            json.dumps(geojson_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return {
            "status": "success",
            "message": f"成功导出 {len(features)} 个要素",
            "feature_count": len(features),
            "download_url": f"/api/data-management/download/{filename}",
            "filename": filename,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
