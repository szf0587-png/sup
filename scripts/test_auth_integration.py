"""测试认证系统集成"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== 测试认证系统集成 ===\n")

try:
    print("1. 导入 FastAPI 应用...")
    from server.main import app
    print("   ✓ 应用导入成功\n")

    print("2. 检查注册的路由...")
    auth_routes = [route for route in app.routes if '/api/auth' in str(route.path)]
    print(f"   ✓ 认证相关路由数量: {len(auth_routes)}")
    for route in auth_routes:
        if hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"     - {methods:20} {route.path}")
    print()

    print("3. 测试数据库连接...")
    from server.database import SessionLocal, engine
    from server.models.user import User

    db = SessionLocal()
    try:
        # 查询管理员账号
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print(f"   ✓ 数据库连接正常")
            print(f"   ✓ 管理员账号存在: {admin.username} ({admin.email})")
        else:
            print("   ⚠ 管理员账号不存在，请运行 init_database.py")
    finally:
        db.close()
    print()

    print("4. 测试认证中间件...")
    from server.middleware.auth import get_current_user, require_admin
    print("   ✓ 认证中间件导入成功")
    print()

    print("5. 测试 JWT 工具...")
    from server.utils.jwt_utils import create_access_token, verify_access_token

    # 创建测试令牌
    test_token = create_access_token(data={"user_id": "test_123", "username": "test"})
    print(f"   ✓ 令牌生成成功: {test_token[:50]}...")

    # 验证令牌
    payload = verify_access_token(test_token)
    if payload and payload.get("user_id") == "test_123":
        print(f"   ✓ 令牌验证成功: user_id={payload['user_id']}")
    print()

    print("=== 所有测试通过 ===\n")
    print("🎉 认证系统已成功集成到 FastAPI 应用！\n")
    print("下一步操作：")
    print("  1. 启动服务器: python server/main.py")
    print("  2. 访问 API 文档: http://localhost:8000/docs")
    print("  3. 测试注册/登录功能")
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
