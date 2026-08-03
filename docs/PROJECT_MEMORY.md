# 天眼寻珍·苍穹 项目续接记忆

> 更新时间：2026-08-03
> 用途：更换 Codex/Terra 对话后，先阅读本文件，再阅读对应里程碑计划。本文是当前工作区状态的续接入口，不替代代码和测试。

## 1. 项目定位与用户目标

- 项目：基于 SuperMap GIS 的土地资源评估与可视化工作台，面向开发组比赛作品。
- 技术主线：FastAPI + SQLAlchemy + SQLite，原生 HTML/CSS/JavaScript，SuperMap iServer REST，3D 使用 SuperMap3D/Cesium 回退。
- 团队提出的四项改进：
  1. 项目数据管理页，管理当前用户在 iServer 中登记的数据。
  2. 三维场景真实显示并可切换地形图层。
  3. 展示站 -> 登录 -> 真实工作台，移除虚构页面入口。
  4. 按用户隔离的 AI 对话，并支持用户自带第三方 API Key。
- 当前已完成前 3 项的基础实现；M3 的上传、发布、取消发布代码和离线测试已完成，真实 iServer 验收仍待执行；AI 对话尚未实现。

## 2. 工作区与运行基线

- 仓库：`D:\supermap\supermap-land-resource-assessment`
- 应用版本：`4.2.0`
- 默认后端端口：`8000`。本机 `8000` 曾被另一个“天枢碳眼”服务占用，因此最近验证项目使用 `8010`。
- 最近可用入口：`http://127.0.0.1:8010/login.html`
- 默认开发账号：`admin / admin123`。仅用于本地演示，部署时必须修改。
- iServer 默认地址：`http://127.0.0.1:8090`。最近验证时没有监听进程，因此真实 SCT/Realspace 不可用。
- 推荐启动：

  ```powershell
  $env:NETRC = 'C:\Users\<user>\.codex\nonexistent-netrc'
  python -m uvicorn server.main:app --host 127.0.0.1 --port 8010
  ```

- 运行配置从环境变量读取：`ISERVER_BASE`、`ISERVER_USER`、`ISERVER_PASSWORD`、`FASTAPI_PORT`。不要把 iServer 密码或第三方 API Key 写入前端、日志或 Git。
- Windows 损坏的 `NETRC` 文件曾导致 requests 的 GBK 解码异常；iServer 客户端已关闭环境代理/netrc 继承，必要时仍可按上面命令显式设置无效路径。

## 3. 里程碑状态

| 里程碑 | 状态 | 当前结论 |
|---|---|---|
| M0 基线与版本统一 | 已完成 | 版本统一到 `4.2.0`，增加环境基线、迁移脚本和契约测试。 |
| M1 SCT 地形链路 | 基础实现完成 | 有地形诊断、TerrainController、开关和降级状态；真实 SCT 仍需运行中的 iServer、已发布 SCT 和 SuperMap3D 运行库。 |
| M2 展示站/认证/真实控制台 | 已完成 | `next` 仅接受同源白名单路径，展示站入口进入真实登录和真实控制台。 |
| M3 项目级 iServer 数据中心 | 代码完成，真实验收待执行 | 已有项目选择、数据上传复用、服务登记、发布/取消发布、GeoJSON 预览、删除和用户/项目隔离；离线测试及代码审查通过，需在 iServer 2026 上完成双用户生命周期验收。 |
| M4 真实评估证据链 | 未开始 | `data/manifest.json` 中洛南边界、DEM、约束、GEE 缓存仍为 `missing`；部分评估服务仍有模拟/随机降级路径。 |
| M5 多供应商 AI 助理 | 未开始 | 尚无 AI provider、会话、消息模型和页面；必须先完成密钥加密、SSRF 防护和用户隔离设计。 |
| M6 比赛提交与演示验收 | 未开始 | 需要真实数据、冷启动验证、截图/录像和最终提交目录。 |

完整路线：`docs/superpowers/plans/2026-08-03-competition-platform-roadmap.md`。

## 4. 已实现的关键接口和页面

### 3D 与地形

- `GET /api/3d-services/scenes/list`：iServer 离线时返回 `degraded`，不再让页面空白或直接 500。
- `GET /api/3d-services/terrain/{scene_name}/diagnostics`：返回 `available`、`provider_type`、`terrain_url`、`layer_name`、`bounds`、`reason`。
- `frontend/js/3d/terrain-controller.js`：显式替换 `viewer.terrainProvider`，地形开关不再误用普通场景图层开关。
- `frontend/map3d.html`：无 iServer/SuperMap3D 时显示“洛南县离线预览”和明确的降级状态，不宣称真实 SCT 已连接。

### 展示站与认证

- 展示站、`frontend/login.html` 和真实控制台页面已经连通。
- 允许的登录后目标：`/index.html`、`/data-center.html`、`/iserver-tools.html`、`/map3d.html`、`/golden_standard.html`。
- 外部 URL、协议相对 URL 和未知路径会回退到安全的 `/index.html`。

### 项目数据中心

- 页面：`frontend/data-center.html`、`frontend/data-center.css`、`frontend/data-center.js`。
- API 前缀：`/api/projects/{project_id}/iserver-assets`。
- 当前可用：
  - `GET` 列出当前用户当前项目资产。
  - `POST` 登记 iServer 服务；`POST .../import` 是同一逻辑的别名。
  - `GET .../{asset_id}/metadata` 获取元数据。
  - `GET .../{asset_id}/preview` 获取要素预览。
  - `DELETE .../{asset_id}` 先请求远端删除，成功后软删除本地登记。
- 所有查询同时按 `project_id` 和服务端解析的 `current_user.id` 过滤；不能信任客户端传入的 `user_id`。
- 已复用既有数据集上传 API，并提供 `import`、`publish`、`unpublish`、GeoJSON `preview`、元数据和软删除 API。资源名由完整用户、项目与数据集标识的确定性哈希命名；发布失败、重复清理和并发冲突均有可重试/409 处理。
- 当前机器没有 iServer，因此这些 API 仅通过客户端边界、迁移和前端契约测试验证；不得将其描述为已完成真实 iServer 发布验收。

## 5. 近期变更的主要文件

- 后端：`server/api/scene_3d.py`、`server/api/iserver_assets.py`、`server/schemas/iserver_asset.py`、`server/integrations/iserver_client.py`、`server/main.py`、`server/config.py`、`server/models/iserver_service.py`、`server/database.py`。
- 前端：`frontend/map3d.html`、`frontend/js/3d/terrain-controller.js`、`frontend/login.html`、`frontend/auth.js`、`frontend/index.html`、`frontend/iserver-tools.html`、`frontend/golden_standard.html`、`frontend/data-center.*`、`frontend/js/navigation.js`。
- 迁移与测试：`scripts/migrate_v42.py`、`tests/test_scene_3d.py`、`tests/test_iserver_assets.py`、`tests/test_iserver_client.py`、`tests/test_migrate_v42.py`、`tests/test_system_contract.py`、`tests/js/*.test.cjs`。
- 关键审查材料：`docs/DELIVERY_REVIEW_M0-M3_20260803.md`、`docs/ENVIRONMENT_BASELINE.md`、`docs/PROJECT_ANALYSIS_20260803.md`、`docs/3D_TERRAIN_DIAGNOSIS.md`。

## 6. 已知风险与不可宣称事项

1. 当前机器没有运行中的 iServer（`8090`）和 SuperMap3D 运行库，不能证明真实 SCT 已在浏览器中渲染；只能证明离线降级链路和诊断接口。
2. `data/manifest.json` 的洛南边界、乡镇、DEM、约束、GEE 缓存等仍缺失，不能把现有随机/模拟降级结果当作比赛正式评估证据。
3. `town_ranking.py`、`parcel_evaluation.py`、`greenhouse_detection.py` 仍需 M4 审查；尤其大棚检测仍存在骨架/降级路径。
4. M3 已实现项目资产上传、发布与取消发布闭环，但当前机器没有 iServer 2026。必须在真实服务上以两个测试用户执行上传、发布、GeoJSON 预览、取消发布和删除后，才能通过 M3 真实验收门槛。
5. 直接运行 `python -m pytest -q` 会误收集旧的 `scripts/test_*.py`；交付验证使用 `python -m pytest tests -q`。
6. 当前测试有 Pydantic/FastAPI 生命周期和 `datetime.utcnow()` 弃用警告，但没有失败；后续可单独清理，不应与功能验收混淆。
7. 部分旧文档由历史编码写入，PowerShell 读取时可能出现乱码；不要在没有确认编码的情况下批量重写旧文档。此次“回复末尾污染”是对话输出问题，不是代码状态。

## 7. 最近验证结果

最近验证：2026-08-04。

```text
python -m pytest tests -q                    -> 44 passed, 142 warnings
node --test tests/js/data-center.test.cjs    -> 2 passed
python -m compileall -q server scripts tests -> passed（2026-08-03）
```

未提交工作区是有意保留的当前开发状态；换对话后不要执行 `git reset --hard`、`git checkout --` 或批量清理未跟踪文件。

## 8. 换对话后的建议顺序

1. 先读本文件、`docs/DELIVERY_REVIEW_M0-M3_20260803.md` 和路线计划。
2. 在有 iServer 2026 的机器上先执行 M3 双用户生命周期验收，再验证 M1 的真实 SCT 渲染。
3. M3 和 M1 的真实服务验收通过后，进入 M4：导入合法、可发放的洛南案例数据，消除计分路径中的随机/模拟值，并生成可追溯报告。
4. M4 通过后再做 M5 AI：服务端加密用户 API Key，按用户隔离会话，限制 HTTPS 供应商和 SSRF，前端只展示掩码信息。
5. 最后执行 M6：冷启动部署、比赛目录校验、技术证据、至少三张截图和 20 分钟内演示录像。

## 9. 下一位代理的工作纪律

- 先检查 `git status`，保留现有用户改动。
- 每个里程碑先读计划中列出的文件，再编辑，再补测试和验证证据。
- 任何“在线”“真实 SCT”“评估完成”“AI 已接入”的文案都必须由实际运行环境或测试证据支持。
- 使用 `apply_patch` 修改文件；不要用脚本覆盖整个文件，也不要为了修编码问题批量改写无关文档。
- 完成一个里程碑后，把结果和剩余风险追加到本文件或新的日期日志，并同步路线计划中的状态。
