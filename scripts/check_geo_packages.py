"""检查地理空间数据处理包的安装情况"""
import sys

print("=== 检查地理空间数据处理包 ===\n")

packages_to_check = {
    "fiona": "矢量数据处理（Shapefile, GeoJSON 等）",
    "rasterio": "栅格数据处理（GeoTIFF 等）",
    "gdal": "GDAL 核心库（osgeo.gdal）",
    "geopandas": "地理数据框架（基于 pandas）",
    "shapely": "几何对象处理",
    "pyproj": "坐标系转换",
}

installed = []
missing = []

for package, description in packages_to_check.items():
    try:
        if package == "gdal":
            from osgeo import gdal
            version = gdal.__version__
            print(f"✓ {package:15} - {description} (v{version})")
            installed.append(package)
        else:
            mod = __import__(package)
            version = getattr(mod, "__version__", "unknown")
            print(f"✓ {package:15} - {description} (v{version})")
            installed.append(package)
    except ImportError:
        print(f"✗ {package:15} - {description} [未安装]")
        missing.append(package)

print(f"\n已安装: {len(installed)} 个")
print(f"未安装: {len(missing)} 个")

if missing:
    print("\n建议安装缺失的包：")
    print(f"  pip install {' '.join(missing)}")
else:
    print("\n所有地理空间数据处理包已安装！")

# 测试 fiona 能否读取 Shapefile
if "fiona" in installed:
    print("\n=== 测试 fiona 功能 ===")
    try:
        import fiona
        print(f"✓ fiona 版本: {fiona.__version__}")
        print(f"✓ fiona 支持的驱动: {', '.join(fiona.supported_drivers.keys())}")
    except Exception as e:
        print(f"✗ fiona 测试失败: {e}")

# 测试 rasterio 能否读取栅格
if "rasterio" in installed:
    print("\n=== 测试 rasterio 功能 ===")
    try:
        import rasterio
        print(f"✓ rasterio 版本: {rasterio.__version__}")
    except Exception as e:
        print(f"✗ rasterio 测试失败: {e}")
