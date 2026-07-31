"""替换旧 API 文件为新版本"""
import shutil
import sys
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors='replace')

api_dir = Path(__file__).parent.parent / "server" / "api"

# 要替换的文件列表
replacements = [
    ("standards.py", "standards_v2.py"),
    ("phenology.py", "phenology_v2.py"),
    ("screening.py", "screening_v2.py"),
    ("parcels.py", "parcels_v2.py"),
    ("reports.py", "reports_v2.py"),
]

print("=== 开始替换 API 文件 ===\n")

for old_file, new_file in replacements:
    old_path = api_dir / old_file
    new_path = api_dir / new_file
    backup_path = api_dir / f"{old_file}.bak"

    if not new_path.exists():
        print(f"[SKIP] {new_file} 不存在，跳过")
        continue

    # 备份旧文件
    if old_path.exists():
        shutil.copy2(old_path, backup_path)
        print(f"[OK] 备份: {old_file} -> {old_file}.bak")

    # 删除旧文件
    if old_path.exists():
        old_path.unlink()
        print(f"[OK] 删除: {old_file}")

    # 重命名新文件
    new_path.rename(old_path)
    print(f"[OK] 重命名: {new_file} -> {old_file}")
    print()

print("=== 替换完成 ===\n")
print("备份文件保存在 server/api/*.bak")
print("如需恢复，可以手动将 .bak 文件重命名回原文件名")
print()
print("下一步：")
print("  1. 重新初始化数据库: python scripts/init_database.py")
print("  2. 重启服务器: python server/main.py")
print("  3. 测试 API: http://localhost:8000/docs")
