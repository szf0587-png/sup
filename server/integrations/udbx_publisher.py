"""UDBX 发布器 — GeoJSON → UDBX → iServer Data Service

使用 iobjectspy.conversion.import_geojson 导入，手动 Feature-level 写入作为备用。
"""
from __future__ import annotations

import json
from pathlib import Path


def geojson_to_udbx(
    geojson_path: Path,
    udbx_path: Path,
    dataset_name: str = "results",
) -> bool:
    """将 GeoJSON FeatureCollection 导入 UDBX。"""
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON not found: {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"Expected FeatureCollection, got {data.get('type')}")
    features = data.get("features", [])
    if not features:
        raise ValueError("Empty GeoJSON")

    print(f"[udbx] Validated: {len(features)} features, geom={features[0]['geometry']['type']}")

    # 优先使用 iobjectspy.conversion.import_geojson
    try:
        from iobjectspy import conversion
        from iobjectspy.data import DatasourceConnectionInfo, create_datasource

        udbx_path.parent.mkdir(parents=True, exist_ok=True)
        if not udbx_path.exists():
            conn = DatasourceConnectionInfo(str(udbx_path))
            ds = create_datasource(conn)
            if ds:
                ds.close()

        result = conversion.import_geojson(str(geojson_path), str(udbx_path))
        if result:
            print(f"[udbx] import_geojson OK → {udbx_path}")
            return True
        else:
            print("[udbx] import_geojson returned False, trying manual")
    except Exception as e:
        print(f"[udbx] import_geojson failed ({e}), trying manual import")

    # 备用：逐要素写入
    return _manual_import(geojson_path, udbx_path, dataset_name, features)


def _manual_import(geojson_path, udbx_path, dataset_name, features) -> bool:
    """备用方案：手动创建数据集并逐要素写入。"""
    try:
        from iobjectspy.data import (
            DatasourceConnectionInfo, DatasetVectorInfo,
            open_datasource, create_datasource,
            Feature, GeoPoint, GeoRegion, GeoLine,
        )
        from iobjectspy import conversion

        conn_info = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn_info) if udbx_path.exists() else create_datasource(conn_info)
        if ds is None:
            print("[udbx] Cannot open/create datasource")
            return False

        # 先用 import_geojson 的完整流程再试一次（传入 output_dataset_name）
        try:
            result = conversion.import_geojson(
                str(geojson_path), str(udbx_path),
                output_dataset_name=dataset_name,
            )
            if result:
                print(f"[udbx] import_geojson retry OK → {dataset_name}")
                ds.close()
                return True
        except Exception:
            pass

        # 逐要素写入
        geom_type = features[0]["geometry"]["type"]
        type_map = {"Point": "POINT", "MultiPoint": "POINT",
                     "LineString": "LINE", "MultiLineString": "LINE",
                     "Polygon": "REGION", "MultiPolygon": "REGION"}
        ds_type = type_map.get(geom_type, "POINT")

        dv_info = DatasetVectorInfo(dataset_name, ds_type)
        dv = ds.create_dataset(dv_info)
        if dv is None:
            ds.close()
            return False

        count = 0
        for feat in features:
            geom = feat["geometry"]
            coords = geom["coordinates"]
            fprops = feat.get("properties", {})
            f = Feature()

            if geom_type in ("Point", "MultiPoint"):
                c = coords[0] if geom_type == "MultiPoint" else coords
                f.geometry = GeoPoint(c[0], c[1])
            elif geom_type in ("Polygon", "MultiPolygon"):
                # 修复：MultiPolygon 应提取第一个 Polygon 的外环
                if geom_type == "MultiPolygon":
                    ring = coords[0][0] if coords and coords[0] else []
                else:
                    ring = coords[0] if coords else []
                f.geometry = GeoRegion([(c[0], c[1]) for c in ring])
            elif geom_type in ("LineString", "MultiLineString"):
                c = coords if geom_type == "LineString" else coords[0]
                f.geometry = GeoLine([(c[0], c[1]) for c in c])

            for k, v in fprops.items():
                f.set_value(k, v)
            dv.append(f)
            count += 1

        dv.close()
        ds.close()
        print(f"[udbx] Manual: {count} features → {dataset_name}")
        return True
    except Exception as e:
        print(f"[udbx] Manual import failed: {e}")
        return False


def _list_datasets(udbx_path: Path) -> list[str]:
    """列出 UDBX 中所有数据集名称"""
    try:
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource
        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)
        if ds is None:
            return []
        names = [d.name for d in ds.datasets]
        ds.close()
        return names
    except Exception:
        return []


def read_features_from_udbx(udbx_path: Path, dataset_name: str, max_n: int = 100) -> list[dict]:
    """从 UDBX 读取要素用于验证。

    import_geojson 会自动给数据集加后缀 (_P/_L/_R)，此函数做模糊匹配。
    Recordset API: move_next() + has_next() + get_geometry() + get_value(field_name)
    """
    try:
        from iobjectspy.data import DatasourceConnectionInfo, open_datasource
        conn = DatasourceConnectionInfo(str(udbx_path))
        ds = open_datasource(conn)
        if ds is None:
            return []

        # 模糊匹配数据集名 (import_geojson 会加 _P/_L/_R 后缀)
        all_names = [d.name for d in ds.datasets]
        matched = None
        for name in all_names:
            if name == dataset_name or name.startswith(dataset_name):
                matched = name
                break
        if matched is None and all_names:
            matched = all_names[0]  # fallback: use first dataset

        dv = ds[matched] if matched else None
        if dv is None:
            ds.close()
            return []

        feats = []
        fis = dv.field_infos
        rs = dv.query()
        n = 0
        while rs.has_next() and n < max_n:
            rs.move_next()
            g = rs.get_geometry()
            geom_str = str(g) if g is not None else "(binary geometry)"
            props = {}
            for fi in fis:
                try:
                    props[fi.name] = rs.get_value(fi.name)
                except Exception:
                    pass
            feats.append({"geometry": geom_str, "properties": props})
            n += 1
        rs.close(); dv.close(); ds.close()
        return feats
    except Exception as e:
        print(f"[udbx] Read failed: {e}")
        return []


def publish_to_iserver(udbx_path: Path, dataset_name: str, service_name: str | None = None) -> dict:
    """
    通过 iServer Manager REST API 将 UDBX 自动发布为数据服务。

    Args:
        udbx_path: UDBX 文件路径
        dataset_name: 数据集名称（用于验证）
        service_name: 服务名（默认使用 dataset_name）

    Returns:
        {"status": "published" | "already_exists" | "error", "service_url": str, ...}
    """
    from server.integrations import iserver_client

    if service_name is None:
        service_name = dataset_name

    result = iserver_client.publish_udbx_as_data_service(
        udbx_path=str(udbx_path),
        service_name=service_name,
        datasource_alias=f"{service_name}_ds",
    )

    # 为向后兼容保留旧格式的 instructions 字段
    if result["status"] in ("published", "already_exists"):
        result["instructions"] = f"已通过 Manager API 自动发布为 {result['service_name']}"
    else:
        result["instructions"] = (
            f"自动发布失败（{result.get('detail', 'unknown')}），"
            f"请手动通过 iDesktopX 发布或检查 iServer 日志"
        )

    return result
