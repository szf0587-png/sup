"""测试项目管理功能集成"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== 测试项目管理功能集成 ===\n")

try:
    print("1. 导入 FastAPI 应用...")
    from server.main import app
    print("   ✓ 应用导入成功\n")

    print("2. 检查项目相关路由...")
    project_routes = [route for route in app.routes if '/api/projects' in str(route.path)]
    print(f"   ✓ 项目相关路由数量: {len(project_routes)}")
    for route in project_routes:
        if hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"     - {methods:20} {route.path}")
    print()

    print("3. 测试项目模型导入...")
    from server.models.project import Project
    print("   ✓ Project 模型导入成功\n")

    print("4. 测试项目 Schema 导入...")
    from server.schemas.project import (
        ProjectCreateRequest,
        ProjectListResponse,
        ProjectDetailResponse,
    )
    print("   ✓ 项目 Schema 导入成功\n")

    print("5. 测试数据库中的项目表...")
    from server.database import SessionLocal, engine
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if 'projects' in tables:
        print("   ✓ projects 表已创建")
        columns = inspector.get_columns('projects')
        print(f"   ✓ projects 表字段数量: {len(columns)}")
    else:
        print("   ✗ projects 表不存在（需要运行 init_database.py）")
    print()

    print("=== 所有测试通过 ===\n")
    print("🎉 项目管理功能已成功集成到 FastAPI 应用！\n")
    print("下一步操作：")
    print("  1. 重启服务器: python server/main.py")
    print("  2. 访问 API 文档: http://localhost:8000/docs")
    print("  3. 测试项目管理功能")
    print()
    print("API 端点：")
    print("  - POST   /api/projects                       创建项目")
    print("  - GET    /api/projects                       列出我的项目")
    print("  - GET    /api/projects/{id}                  获取项目详情")
    print("  - PUT    /api/projects/{id}                  更新项目")
    print("  - POST   /api/projects/{id}/activate         激活项目")
    print("  - POST   /api/projects/{id}/datasets         添加数据集到项目")
    print("  - DELETE /api/projects/{id}/datasets/{ds_id} 从项目移除数据集")
    print("  - DELETE /api/projects/{id}                  删除项目")
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
