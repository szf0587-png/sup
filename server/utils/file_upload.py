"""文件上传和元数据提取工具"""
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import uuid


def get_user_data_directory(user_id: str, base_dir: Path) -> Path:
    """
    获取用户数据目录路径

    Args:
        user_id: 用户ID
        base_dir: 基础数据目录

    Returns:
        用户数据目录路径
    """
    user_dir = base_dir / "users" / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_dataset_type_directory(user_id: str, dataset_type: str, base_dir: Path) -> Path:
    """
    获取数据集类型目录（vector/raster/gee_cache）

    Args:
        user_id: 用户ID
        dataset_type: 数据集类型
        base_dir: 基础数据目录

    Returns:
        数据集类型目录路径
    """
    type_dir = get_user_data_directory(user_id, base_dir) / dataset_type
    type_dir.mkdir(parents=True, exist_ok=True)
    return type_dir


def save_uploaded_file(
    file_content: bytes,
    filename: str,
    user_id: str,
    dataset_type: str,
    base_dir: Path
) -> Tuple[str, int]:
    """
    保存上传的文件到用户目录

    Args:
        file_content: 文件内容
        filename: 原始文件名
        user_id: 用户ID
        dataset_type: 数据集类型 (vector/raster)
        base_dir: 基础数据目录

    Returns:
        (相对路径, 文件大小)
    """
    # 生成唯一文件名（保留原始扩展名）
    file_ext = Path(filename).suffix
    unique_filename = f"{uuid.uuid4().hex[:12]}{file_ext}"

    # 获取目标目录
    target_dir = get_dataset_type_directory(user_id, dataset_type, base_dir)
    target_path = target_dir / unique_filename

    # 保存文件
    with open(target_path, 'wb') as f:
        f.write(file_content)

    file_size = len(file_content)

    # 返回相对路径
    relative_path = f"users/{user_id}/{dataset_type}/{unique_filename}"
    return relative_path, file_size


def extract_vector_metadata(file_path: Path) -> Dict[str, Any]:
    """
    提取矢量数据元数据（边界、CRS、字段信息）

    Args:
        file_path: 文件路径

    Returns:
        元数据字典 {crs, bounds, fields, feature_count}
    """
    try:
        import fiona
        from fiona.crs import CRS

        with fiona.open(file_path) as src:
            # 提取 CRS
            crs = None
            if src.crs:
                crs = CRS(src.crs).to_string()

            # 提取边界
            bounds = list(src.bounds) if src.bounds else None

            # 提取字段信息
            fields = []
            if src.schema and 'properties' in src.schema:
                for field_name, field_type in src.schema['properties'].items():
                    fields.append({
                        'name': field_name,
                        'type': field_type
                    })

            # 要素数量
            feature_count = len(src)

            return {
                'crs': crs,
                'bounds': bounds,
                'fields': fields,
                'feature_count': feature_count,
                'geometry_type': src.schema.get('geometry', 'Unknown')
            }

    except ImportError:
        # fiona 未安装，返回基础信息
        return {
            'crs': None,
            'bounds': None,
            'error': 'fiona not installed, cannot extract metadata'
        }
    except Exception as e:
        return {
            'crs': None,
            'bounds': None,
            'error': str(e)
        }


def extract_raster_metadata(file_path: Path) -> Dict[str, Any]:
    """
    提取栅格数据元数据（边界、CRS、波段信息）

    Args:
        file_path: 文件路径

    Returns:
        元数据字典 {crs, bounds, bands, width, height}
    """
    try:
        import rasterio

        with rasterio.open(file_path) as src:
            # 提取 CRS
            crs = src.crs.to_string() if src.crs else None

            # 提取边界
            bounds = list(src.bounds) if src.bounds else None

            # 提取波段信息
            bands = []
            for i in range(1, src.count + 1):
                band_stats = src.statistics(i)
                bands.append({
                    'band_number': i,
                    'dtype': str(src.dtypes[i - 1]),
                    'min': band_stats.min if band_stats else None,
                    'max': band_stats.max if band_stats else None,
                    'mean': band_stats.mean if band_stats else None,
                })

            return {
                'crs': crs,
                'bounds': bounds,
                'bands': bands,
                'width': src.width,
                'height': src.height,
                'band_count': src.count,
                'nodata': src.nodata,
            }

    except ImportError:
        # rasterio 未安装，返回基础信息
        return {
            'crs': None,
            'bounds': None,
            'error': 'rasterio not installed, cannot extract metadata'
        }
    except Exception as e:
        return {
            'crs': None,
            'bounds': None,
            'error': str(e)
        }


def extract_geojson_metadata(file_path: Path) -> Dict[str, Any]:
    """
    提取 GeoJSON 元数据（边界、字段信息）

    Args:
        file_path: 文件路径

    Returns:
        元数据字典 {crs, bounds, fields, feature_count}
    """
    try:
        import json

        with open(file_path, 'r', encoding='utf-8') as f:
            geojson = json.load(f)

        # GeoJSON 默认 CRS 是 WGS84
        crs = "EPSG:4326"

        # 计算边界
        bounds = None
        features = geojson.get('features', [])
        if features:
            all_coords = []
            for feature in features:
                geom = feature.get('geometry', {})
                coords = geom.get('coordinates', [])
                all_coords.extend(_flatten_coordinates(coords))

            if all_coords:
                lons = [c[0] for c in all_coords]
                lats = [c[1] for c in all_coords]
                bounds = [min(lons), min(lats), max(lons), max(lats)]

        # 提取字段信息
        fields = []
        if features and features[0].get('properties'):
            for key, value in features[0]['properties'].items():
                fields.append({
                    'name': key,
                    'type': type(value).__name__
                })

        return {
            'crs': crs,
            'bounds': bounds,
            'fields': fields,
            'feature_count': len(features),
            'geometry_type': features[0]['geometry']['type'] if features else 'Unknown'
        }

    except Exception as e:
        return {
            'crs': "EPSG:4326",
            'bounds': None,
            'error': str(e)
        }


def _flatten_coordinates(coords):
    """递归展平坐标列表"""
    result = []
    if isinstance(coords, (list, tuple)):
        if len(coords) == 2 and isinstance(coords[0], (int, float)):
            # 这是一个坐标点 [lon, lat]
            return [coords]
        for item in coords:
            result.extend(_flatten_coordinates(item))
    return result


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）"""
    return Path(filename).suffix.lower()


def detect_dataset_type(filename: str) -> str:
    """
    根据文件扩展名检测数据集类型

    Args:
        filename: 文件名

    Returns:
        'vector' 或 'raster'
    """
    ext = get_file_extension(filename)

    vector_extensions = {'.geojson', '.json', '.shp', '.kml', '.gpkg', '.gdb'}
    raster_extensions = {'.tif', '.tiff', '.geotiff', '.img', '.jpg', '.png'}

    if ext in vector_extensions:
        return 'vector'
    elif ext in raster_extensions:
        return 'raster'
    else:
        # 默认为 vector
        return 'vector'
