"""数据库初始化脚本 - 独立运行检查所有模型是否正确定义"""
import sys
from pathlib import Path

# 设置输出编码为 UTF-8（Windows 环境）
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== 数据库模型导入测试 ===\n")

# 测试导入所有模型
try:
    print("1. 导入 Base 和 engine...")
    from server.database import Base, engine, SessionLocal
    print("   ✓ 数据库连接配置导入成功\n")

    print("2. 导入 User 模型...")
    from server.models.user import User
    print(f"   ✓ User 表名: {User.__tablename__}")

    print("3. 导入 Dataset 模型...")
    from server.models.dataset import Dataset
    print(f"   ✓ Dataset 表名: {Dataset.__tablename__}")

    print("4. 导入 Project 模型...")
    from server.models.project import Project
    print(f"   ✓ Project 表名: {Project.__tablename__}")

    print("5. 导入 AnalysisTask 模型...")
    from server.models.analysis_task import AnalysisTask
    print(f"   ✓ AnalysisTask 表名: {AnalysisTask.__tablename__}")

    print("6. 导入 GEECredential 模型...")
    from server.models.gee_credential import GEECredential
    print(f"   ✓ GEECredential 表名: {GEECredential.__tablename__}")

    print("7. 导入 IServerService 模型...")
    from server.models.iserver_service import IServerService
    print(f"   ✓ IServerService 表名: {IServerService.__tablename__}")

    print("8. 导入 GoldenStandard 模型...")
    from server.models.golden_standard import GoldenStandard
    print(f"   ✓ GoldenStandard 表名: {GoldenStandard.__tablename__}")

    print("\n9. 导入密码工具...")
    from server.utils.password import hash_password, verify_password
    print("   ✓ 密码工具导入成功")

    print("\n=== 所有模型导入成功 ===\n")

    # 创建所有表
    print("10. 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("   ✓ 数据库表创建完成\n")

    # 创建默认管理员账号
    print("11. 创建默认管理员账号...")
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                id="user_admin",
                username="admin",
                email="admin@local",
                password_hash=hash_password("admin123"),
                display_name="系统管理员",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("   ✓ 管理员账号已创建: admin / admin123")
        else:
            print("   ℹ 管理员账号已存在")
    finally:
        db.close()

    print("\n=== 数据库初始化完成 ===")

except ImportError as e:
    print(f"\n✗ 导入错误: {e}")
    print("\n可能的原因:")
    print("  - 缺少依赖包（运行: pip install sqlalchemy bcrypt）")
    print("  - 模型文件语法错误")
    sys.exit(1)

except Exception as e:
    print(f"\n✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
