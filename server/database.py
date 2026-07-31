"""数据库连接与会话管理"""
from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool

# 数据库配置
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
DATABASE_DIR = Path(__file__).parent.parent / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

if DATABASE_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/tianyan.db"
    # SQLite 特殊配置：使用 StaticPool 避免多线程问题
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # 生产环境改为 False
    )
elif DATABASE_TYPE == "postgresql":
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/tianyan"
    )
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
else:
    raise ValueError(f"Unsupported DATABASE_TYPE: {DATABASE_TYPE}")

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类
Base = declarative_base()


def get_db() -> Session:
    """
    数据库会话依赖注入（FastAPI Depends）

    用法：
        @app.get("/api/users")
        def list_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型（确保 Base.metadata 包含所有表）
    from server.models import (
        user, dataset, project, analysis_task,
        gee_credential, iserver_service, golden_standard
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"[database] 数据库初始化完成: {DATABASE_URL}")

    # 创建默认管理员账号（如果不存在）
    db = SessionLocal()
    try:
        from server.models.user import User
        from server.utils.password import hash_password

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
            print("[database] 默认管理员账号已创建: admin / admin123")
    except Exception as e:
        print(f"[database] 创建管理员账号失败: {e}")
    finally:
        db.close()


def drop_all():
    """删除所有表（危险操作，仅用于开发测试）"""
    Base.metadata.drop_all(bind=engine)
    print("[database] 所有表已删除")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_db()
    elif len(sys.argv) > 1 and sys.argv[1] == "drop":
        confirm = input("确认删除所有表？(yes/no): ")
        if confirm.lower() == "yes":
            drop_all()
    else:
        print("用法:")
        print("  python server/database.py init  # 初始化数据库")
        print("  python server/database.py drop  # 删除所有表")
