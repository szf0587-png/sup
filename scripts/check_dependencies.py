"""检查依赖包安装情况"""
import sys

print("=== 检查多用户系统依赖包 ===\n")

required_packages = {
    "sqlalchemy": "数据库 ORM",
    "bcrypt": "密码加密",
    "jwt": "JWT 令牌（安装包名: pyjwt）",
}

missing_packages = []

for package, description in required_packages.items():
    try:
        __import__(package)
        print(f"✓ {package:15} - {description}")
    except ImportError:
        print(f"✗ {package:15} - {description} [未安装]")
        missing_packages.append(package)

print()

if missing_packages:
    print("缺少以下依赖包，请运行以下命令安装：\n")
    if "jwt" in missing_packages:
        missing_packages.remove("jwt")
        missing_packages.append("pyjwt")
    print(f"  pip install {' '.join(missing_packages)}")
    print()
    sys.exit(1)
else:
    print("所有依赖包已安装，可以运行数据库初始化脚本")
    print("\n运行: python scripts/init_database.py")
