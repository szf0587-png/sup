# 天眼寻珍·苍穹 v4.2 环境基线

更新时间：2026-08-03  
适用范围：M0-M3（运行基线、三维地形、认证贯通、项目级 iServer 数据中心）

## 已验证环境

| 项目 | 版本/值 |
|---|---|
| 操作系统 | Windows 11 64-bit（10.0.26200） |
| Python | 3.13.12 |
| FastAPI | 0.141.1 |
| SQLAlchemy | 2.0.51 |
| Uvicorn | 0.52.1 |
| Pydantic | 2.12.4 |
| HTTPX | 0.28.1 |
| pytest | 9.1.1 |
| Node.js | v24.15.0 |
| 应用版本 | 4.2.0 |

## 安装与启动

```powershell
$env:NETRC = 'C:\Users\<user>\.codex\nonexistent-netrc'
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

登录入口：`http://127.0.0.1:8000/login.html`  
项目数据中心：`http://127.0.0.1:8000/data-center.html`

## 验证命令

```powershell
python -m pytest tests -q
node --test tests/js/*.test.cjs
python -m compileall -q server scripts tests
```

当前基线测试结果：Python 21 passed，Node 6 passed。仓库 `scripts/test_*.py` 中存在旧式导入即执行脚本，直接运行 `python -m pytest -q` 会把这些脚本当测试收集；交付验证应使用 `python -m pytest tests -q`，后续应将脚本改为显式入口。

## 外部运行时边界

- iServer 地址、账号和密码只从 `ISERVER_BASE`、`ISERVER_USER`、`ISERVER_PASSWORD` 读取。
- 本轮未宣称真实 iServer/SCT 在线，三维页面会显示 SCT、Cesium 在线地形或椭球降级的实际状态。
- SuperMap3D 运行库应由现场环境提供或放在 `frontend/vendor/supermap3d/`，不把官方大型安装包打入作品压缩包。
