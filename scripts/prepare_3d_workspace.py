"""Prepare a SuperMap 3D workspace from local DEM/OSM files.

This script is meant to be run with the SuperMap bundled Python runtime.
It creates a SMWU workspace, creates or opens a UDBX datasource, imports the
Luonan DEM as a grid dataset, and can optionally import the Shaanxi OSM GPKG.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_PARENT = PROJECT_ROOT.parents[1]
DEFAULT_DATA_ROOT = REPO_PARENT / "data" / "3d"
DEFAULT_SUPERMAP_ROOT = Path("E:/SuperMap")
OSM_SENTINEL_DATASETS = {
    "gis_osm_roads_free",
    "gis_osm_buildings_a_free",
    "gis_osm_water_a_free",
    "gis_osm_landuse_a_free",
}


@dataclass
class PreparedPaths:
    data_root: Path
    output_dir: Path
    workspace: Path
    datasource: Path
    manifest: Path
    dem: Path
    osm_gpkg: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a SuperMap 3D workspace and import DEM/OSM sources."
    )
    parser.add_argument(
        "--supermap-root",
        default=os.environ.get("SUPERMAP_ROOT", str(DEFAULT_SUPERMAP_ROOT)),
        help="SuperMap iDesktop/iObjects root, default: E:/SuperMap",
    )
    parser.add_argument(
        "--data-root",
        default=os.environ.get("LAND3D_DATA_ROOT", str(DEFAULT_DATA_ROOT)),
        help="Local 3D data root, default: ../../data/3d from repository parent",
    )
    parser.add_argument("--workspace-name", default="luonan_3d")
    parser.add_argument("--datasource-alias", default="luonan_3d")
    parser.add_argument("--dem-dataset", default="luonan_cop30_dem")
    parser.add_argument(
        "--dem",
        default=None,
        help="DEM GeoTIFF path. Defaults to <data-root>/dem/luonan_cop30.tif",
    )
    parser.add_argument(
        "--osm-gpkg",
        default=None,
        help="OSM GeoPackage path. Defaults to <data-root>/osm/shaanxi-latest-free.gpkg/shaanxi.gpkg",
    )
    parser.add_argument(
        "--with-osm",
        action="store_true",
        help="Import the full Shaanxi OSM GPKG. This can take several minutes.",
    )
    parser.add_argument(
        "--no-pyramid",
        action="store_true",
        help="Skip DEM pyramid building. Faster, but weaker for desktop browsing.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the generated workspace/datasource files.",
    )
    return parser.parse_args()


def configure_iobjects_env(supermap_root: Path) -> None:
    bin_dir = supermap_root / "bin"
    jre_dir = supermap_root / "jre"
    python_lib = supermap_root / "support" / "PythonLib"
    iobjectspy_dir = supermap_root / "bin_python" / "iobjectspy" / "iobjectspy-py38_64"

    required = [bin_dir, jre_dir, python_lib, iobjectspy_dir]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing SuperMap runtime paths: " + "; ".join(missing))

    os.environ["JAVA_HOME"] = str(jre_dir)
    os.environ["JRE_HOME"] = str(jre_dir)

    path_parts = [
        str(bin_dir),
        str(jre_dir / "bin"),
        str(jre_dir / "bin" / "server"),
    ]
    os.environ["PATH"] = os.pathsep.join(path_parts + [os.environ.get("PATH", "")])

    for item in [str(python_lib), str(iobjectspy_dir)]:
        if item not in sys.path:
            sys.path.insert(0, item)


def build_paths(args: argparse.Namespace) -> PreparedPaths:
    data_root = Path(args.data_root).resolve()
    output_dir = data_root / "workspace"
    dem = Path(args.dem).resolve() if args.dem else data_root / "dem" / "luonan_cop30.tif"
    osm_gpkg = (
        Path(args.osm_gpkg).resolve()
        if args.osm_gpkg
        else data_root / "osm" / "shaanxi-latest-free.gpkg" / "shaanxi.gpkg"
    )
    workspace = output_dir / f"{args.workspace_name}.smwu"
    datasource = output_dir / f"{args.workspace_name}.udbx"
    manifest = output_dir / f"{args.workspace_name}.manifest.json"
    return PreparedPaths(data_root, output_dir, workspace, datasource, manifest, dem, osm_gpkg)


def remove_if_requested(paths: PreparedPaths, overwrite: bool) -> None:
    if not overwrite:
        return

    targets = [
        paths.workspace,
        paths.workspace.with_suffix(".smwu.lock"),
        paths.datasource,
        paths.datasource.with_suffix(".udd"),
        paths.manifest,
    ]
    root = paths.output_dir.resolve()
    for target in targets:
        resolved = target.resolve()
        if root not in resolved.parents and resolved != root:
            raise RuntimeError(f"Refusing to remove outside output dir: {resolved}")
        if resolved.exists():
            resolved.unlink()


def dataset_names(datasource: Any) -> list[str]:
    try:
        datasets = getattr(datasource, "datasets", [])
        return sorted(
            str(getattr(dataset, "name", dataset))
            for dataset in datasets
            if getattr(dataset, "name", dataset) is not None
        )
    except Exception:
        return []


def use_returned_workspace(current: Any, result: Any, action: str) -> Any:
    if result is False:
        raise RuntimeError(f"Failed to {action} workspace")
    if result is not None and result is not True:
        return result
    return current


def ensure_source_files(paths: PreparedPaths, with_osm: bool) -> None:
    if not paths.dem.exists():
        raise FileNotFoundError(f"DEM not found: {paths.dem}")
    if with_osm and not paths.osm_gpkg.exists():
        raise FileNotFoundError(f"OSM GPKG not found: {paths.osm_gpkg}")


def write_manifest(
    paths: PreparedPaths,
    args: argparse.Namespace,
    imported: dict[str, Any],
    datasets_after: list[str],
) -> None:
    manifest = {
        "workspace": str(paths.workspace),
        "datasource": str(paths.datasource),
        "datasource_alias": args.datasource_alias,
        "dem_dataset": args.dem_dataset,
        "osm_imported": bool(imported.get("osm")),
        "source_files": {
            "dem": str(paths.dem),
            "osm_gpkg": str(paths.osm_gpkg),
        },
        "datasets": datasets_after,
        "next_steps": [
            "Open the SMWU in SuperMap iDesktopX.",
            "Use the DEM grid dataset to build a terrain cache (SCT).",
            "Add OSM vector layers or converted building/model layers to a scene if needed.",
            "Publish the workspace or scene as a Realspace/3D service in iServer.",
            "Connect the published service URL in the platform 3D module.",
        ],
        "recommended_iserver_service": {
            "name": "3D-luonan",
            "rest_realspace": "http://127.0.0.1:8090/iserver/services/3D-luonan/rest/realspace",
        },
    }
    paths.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    args = parse_args()
    paths = build_paths(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    remove_if_requested(paths, args.overwrite)
    ensure_source_files(paths, args.with_osm)

    configure_iobjects_env(Path(args.supermap_root))

    from iobjectspy import conversion, data
    from iobjectspy.enums import EngineType, WorkspaceType

    workspace = data.Workspace()
    imported: dict[str, Any] = {"dem": False, "osm": False}
    try:
        ws_conn = data.WorkspaceConnectionInfo(
            server=str(paths.workspace),
            workspace_type=WorkspaceType.SMWU,
        )
        ds_conn = data.DatasourceConnectionInfo(
            server=str(paths.datasource),
            engine_type=EngineType.UDBX,
            alias=args.datasource_alias,
        )

        if paths.workspace.exists() and not args.overwrite:
            print(f"[workspace] open {paths.workspace}")
            workspace = use_returned_workspace(workspace, workspace.open(ws_conn), "open")
        else:
            print(f"[workspace] create {paths.workspace}")
            workspace = use_returned_workspace(workspace, workspace.create(ws_conn), "create")

        if paths.datasource.exists() and not args.overwrite:
            print(f"[datasource] open {paths.datasource}")
            datasource = workspace.open_datasource(ds_conn)
        else:
            print(f"[datasource] create {paths.datasource}")
            datasource = workspace.create_datasource(ds_conn)
        if datasource is None:
            raise RuntimeError(f"Failed to create/open datasource: {paths.datasource}")

        before = set(dataset_names(datasource))
        if args.dem_dataset in before and not args.overwrite:
            print(f"[dem] skip existing dataset {args.dem_dataset}")
        else:
            print(f"[dem] import {paths.dem} -> {args.dem_dataset}")
            conversion.import_tif(
                str(paths.dem),
                datasource,
                out_dataset_name=args.dem_dataset,
                is_import_as_grid=True,
                is_build_pyramid=not args.no_pyramid,
            )
            imported["dem"] = True

        if args.with_osm:
            current_names = set(dataset_names(datasource))
            if OSM_SENTINEL_DATASETS.issubset(current_names) and not args.overwrite:
                print("[osm] skip existing OSM datasets")
                imported["osm"] = "existing"
            else:
                print(f"[osm] import {paths.osm_gpkg}")
                conversion.import_gpkg(str(paths.osm_gpkg), datasource)
                imported["osm"] = True
        else:
            print("[osm] skipped. Re-run with --with-osm to import vectors.")

        if workspace.save() is False:
            print("[workspace] save returned False, trying save_as")
            if workspace.save_as(ws_conn) is False:
                raise RuntimeError(f"Failed to save workspace: {paths.workspace}")

        after = dataset_names(datasource)
        write_manifest(paths, args, imported, after)
        print("[done] workspace:", paths.workspace)
        print("[done] datasource:", paths.datasource)
        print("[done] manifest:", paths.manifest)
        if after:
            print("[done] datasets:", ", ".join(after))
        return 0
    finally:
        workspace.close()


if __name__ == "__main__":
    raise SystemExit(main())
