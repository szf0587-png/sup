"""测试数据集管理功能集成"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== 测试数据集管理功能集成 ===\n")

try:
    print("1. 导入 FastAPI 应用...")
    from server.main import app
    print("   ✓ 应用导入成功\n")

    print("2. 检查数据集相关路由...")
    dataset_routes = [route for route in app.routes if '/api/datasets' in str(route.path)]
    print(f"   ✓ 数据集相关路由数量: {len(dataset_routes)}")
    for route in dataset_routes:
        if hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"     - {methods:20} {route.path}")
    print()

    print("3. 测试数据集模型导入...")
    from server.models.dataset import Dataset
    print("   ✓ Dataset 模型导入成功\n")

    print("4. 测试文件上传工具...")
    from server.utils.file_upload import (
        detect_dataset_type,
        get_file_extension,
        get_user_data_directory,
    )
    print("   ✓ 文件上传工具导入成功")

    # 测试文件类型检测
    assert detect_dataset_type("test.geojson") == "vector"
    assert detect_dataset_type("test.tif") == "raster"
    assert get_file_extension("test.GeoJSON") == ".geojson"
    print("   ✓ 文件类型检测正常\n")

    print("5. 检查数据目录...")
    from server.config import DATA_DIR
    data_path = Path(DATA_DIR)
    print(f"   ✓ 数据目录: {data_path}")
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
        print("   ✓ 数据目录已创建")
    else:
        print("   ✓ 数据目录已存在")
    print()

    print("6. 测试用户数据目录创建...")
    test_user_dir = get_user_data_directory("test_user", data_path)
    print(f"   ✓ 测试用户目录: {test_user_dir}")
    print()

    print("=== 所有测试通过 ===\n")
    print("🎉 数据集管理功能已成功集成到 FastAPI 应用！\n")
    print("下一步操作：")
    print("  1. 重启服务器: python server/main.py")
    print("  2. 访问 API 文档: http://localhost:8000/docs")
    print("  3. 测试数据集上传功能")
    print()
    print("API 端点：")
    print("  - POST   /api/datasets/upload     上传数据集")
    print("  - GET    /api/datasets            列出我的数据集")
    print("  - GET    /api/datasets/{id}       获取数据集详情")
    print("  - PUT    /api/datasets/{id}       更新数据集")
    print("  - DELETE /api/datasets/{id}       删除数据集")
    print("  - GET    /api/datasets/admin/all  管理员查看所有数据集")
    print()

except ImportError as e:
    print(f"\n✗ 导入错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
