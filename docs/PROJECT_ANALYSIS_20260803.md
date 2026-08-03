# 天眼寻珍·苍穹 — 仓库导入后细致分析报告

> 分析日期：2026-08-03
> 仓库：`https://github.com/Dehors-s/supermap-land-resource-assessment.git`
> 本地路径：`d:\supermap\supermap-land-resource-assessment`
> 用途：第 24 届 SuperMap 杯高校 GIS 大赛·开发者赛道参赛作品（v2.0，基于 v1.0「天眼寻珍」迭代）

---

## 一、仓库基本状态

| 检查项 | 结果 |
|---|---|
| 分支 | 仅 `main`，无其他分支 |
| 提交历史 | 仅 2 条：`f9d1c2b`(Initial commit) → `cb7691d`(v1) |
| 工作树 | clean，无未提交改动 |
| 仓库大小 | 486 KB（不含数据） |
| 代码规模 | Python ~13,235 行 / JS ~6,701 行 / HTML ~1,782 行 / CSS ~3,028 行，合计约 **2.5 万行** |

**关键结论**：仓库是"一揽子快照式提交"，仅 2 次提交即包含全部代码，**无法用提交历史证明开发演进过程**。这与《开发组对抗性审查综述》中"Git 版本库未发现 → 无法证明原创与可追溯变更"的风险点直接相关——现在有了 Git，但历史仍然单薄。建议按功能里程碑分批补提（rebuild 历史或后续按模块拆分提交），并保留独立于本次导入的演进记录。

---

## 二、项目定位与技术架构

### 2.1 定位
基于 SuperMap iServer 的土地资源分析与可视化工作台，核心业务链为：
**绘制评估边界 → 逐步空间分析（范围统计/水体约束/缓冲/道路/行政区）→ 物候匹配 → 区域筛选(Top N 乡镇) → 地块精评 → 报告生成**，每一步的文字结果与地图要素均返回同一工作区。

### 2.2 分层架构（后端）
```
server/
├─ main.py                  # 主入口（模块化，v2.0 重构版，README 指定的启动入口）
├─ main_tianyan.py          # 旧版单体入口（1544 行，疑似遗留/双入口风险）
├─ config.py                # 全局配置（含硬编码个人路径，见问题清单）
├─ database.py              # SQLite/PostgreSQL 双支持 + 默认管理员初始化
├─ models/                  # 7 张表：User/Dataset/Project/AnalysisTask/GEECredential/IServerService/GoldenStandard
├─ api/                     # 14 个路由模块
├─ services/                # 业务逻辑：land_assessment/spatial_analysis/parcel_evaluation/phenology/town_ranking/report_builder/greenhouse_detection
├─ integrations/            # iserver_client(1153行,35函数)/gee_client/udbx_publisher
├─ middleware/auth.py       # JWT 认证（必须登录/可选登录/管理员 三档）
├─ schemas/                 # Pydantic 模型
├─ utils/                   # password/jwt_utils/file_upload
├─ core_algorithms.py       # GEE 算法（AHP/LSI 适宜性指数）
├─ degradation.py           # 离线降级配置与数据来源标记
└─ AHP_original.py          # AHP 原版实现
```

### 2.3 前端结构
```
frontend/
├─ index.html               # 主工作台（三栏布局 + 侧边导航）
├─ login.html               # 登录（JWT/记住我）
├─ map3d.html               # 3D Realspace 工作台（Cesium1.114/SuperMap3D 引擎自适应）
├─ iserver-tools.html       # iServer 原生地理处理工具页
├─ golden_standard.html     # 模型库（金标准管理）
├─ land-workbench.js/css    # 工作台核心（1562 行）
├─ js/api/                  # 5 个封装：spatial-analysis/map-services/data-editing/data-management/scene-3d
├─ js/components/           # sidebar/right-panel/analysis-tools/data-manager
├─ js/map/                  # map-manager/layer-manager/draw-tools
└─ vendor/leaflet/          # 本地 Leaflet（离线可用 ✓）
```

---

## 三、功能完成度矩阵（对照对抗性审查）

| 功能模块 | 仓库内证据 | 完成度判断 |
|---|---|---|
| 多用户 SaaS（JWT/用户隔离/项目激活/数据集） | `api/auth|datasets|projects` + 7 表 + 中间件 | ✅ 完整（13/13 任务文档佐证） |
| iServer 深度集成（34 API） | `integrations/iserver_client.py` 35 个函数 | ✅ 代码完整，**依赖外部 iServer 在线** |
| 空间分析/地图/数据编辑/数据管理/三维 | `api/` 对应 5 模块 + 前端 5 封装 | ✅ 代码完整，运行时依赖 iServer |
| 土地资源评估主链路 | `services/land_assessment.py` | ✅ 已实现"证据包"模式（不产出代理分数） |
| 物候匹配 | `services/phenology.py` + GEE | 🟡 逻辑在，**GEE 缓存数据缺失** |
| Top N 乡镇排序 | `services/town_ranking.py` + 测试 | 🟡 有实现与测试，**需真实数据验证** |
| 地块精评（AHP/四维评分） | `services/parcel_evaluation.py` + `core_algorithms.py` | 🟡 有实现，GEE 依赖 |
| 报告生成 | `services/report_builder.py` | 🟡 需确认 PDF 依赖(weasyprint) |
| 大棚检测（YOLO） | `services/greenhouse_detection.py`（129 行） | 🔴 **骨架**：`_run_inference` 是 TODO 占位，仅预计算/模拟降级 |
| 3D Realspace 工作台 | `map3d.html` + `api/scene_3d.py`(654行) | 🟡 代码完整，**等待真实 3D 场景联调** |
| 洛南案例数据 | `data/manifest.json` | 🔴 **全部 missing**（边界/乡镇/DEM/约束/GEE缓存/高分影像） |

### 数据台账现状（data/ 目录实际内容）
```
data/
├─ golden_standards.json   # present（金标准库）
├─ manifest.json           # 数据台账
├─ outputs/ raster/ vector/   # 仅 .gitkeep 占位
```
洛南县边界、乡镇、DEM、约束图层、NDVI/LST 缓存、高分影像**全部缺失**——这是对抗性审查列出的头号现场风险，导入仓库后仍**未解决**。

---

## 四、亮点（可写进介绍书/答辩）

1. **架构规范**：API/Service/Integration/Model 分层清晰，SQLAlchemy 2.x + Pydantic + FastAPI 组合现代；数据库支持 SQLite/PostgreSQL 切换。
2. **iServer 深度集成**：34 个 API、5 个集成模块，iServer 功能利用率 20% → 85%，前端有真实服务发现/能力检测机制。
3. **多用户隔离完整**：JWT + 中间件三档权限 + 用户目录隔离 + 项目激活机制，工程化程度高。
4. **3D 工作台双引擎自适应**：SuperMap3D → Cesium 1.114 自动回退，SCT 地形检测、相机视角自动读取，思路先进。
5. **数据台账制度**：manifest.json 强制记录来源/许可/SHA256，体现数据合规意识。
6. **降级设计**：degradation.py 定义了完整的数据来源标记与降级提示，GEE/AI/iServer 均设计离线兜底路径。
7. **文档体系完善**：docs/ 下 40+ 份开发/集成/测试/设计文档。

---

## 五、问题与风险清单

### 🔴 高优先级（直接影响现场演示/评审）

1. **核心案例数据全部缺失**：洛南 4 类矢量 + DEM + 高分影像 + GEE 缓存均为 missing。`scripts/prepare-3d-workspace.ps1` 等依赖 DEM 的链路无法现场闭环。
2. **大棚检测（评分亮点）只有骨架**：`greenhouse_detection.py` 的 `_run_inference` 是 TODO，未接 YOLO。README 未强调，但介绍书/答辩若宣称"AI 检测"会被质疑。
3. **iServer 强依赖**：水体/道路/行政区/空间分析全部走 `http://127.0.0.1:8090` 的 iServer REST。现场断网或 iServer 未启动时降级路径是否真能工作、前端是否清晰标注，需实测。
4. **GEE 依赖**：`core_algorithms.py`、`main_tianyan.py` 均 import ee；离线缓存缺失意味着物候/适宜性链路只能走模拟。

### 🟡 中优先级（代码卫生与一致性）

5. **双入口风险**：`main.py`（模块化）与 `main_tianyan.py`（1544 行单体）并存。README 说用 `main.py`，但 `main_tianyan.py` 仍保留大量旧逻辑，容易跑错入口、出现"两个服务"现象。
6. **遗留垃圾文件**：5 个 `*.bak`（parcels/phenology/reports/screening/standards_old）+ 前端 `fix_charts_v3.py`、`update_charts*.py`、`link_api.py`、`demo.html`、`DESIGN.md` 等开发中间产物被提交入库。
7. **硬编码个人路径**：`config.py` 中 `TIANYAN_ROOT = r"D:\Work space\天眼寻珍"`，换机器即失效（有 env 覆盖但默认值仍泄露个人目录结构）。
8. **.omo/ 目录入库**：`.omo/run-continuation/*.json` 是本地 AI 工具运行元数据，不应进入仓库（.gitignore 未排除）。
9. **安全**：README 明示默认管理员 `admin/admin123`；iServer 密码通过环境变量注入（方向正确），但需确认无明文泄露进代码/文档。

### 🔵 低优先级（完善度）

10. **测试覆盖偏弱**：仅 3 个测试文件（land_assessment / map_tiles / town_ranking），相对 2.5 万行代码明显不足；`scripts/test_all_apis.py`(323行) 是集成冒烟脚本，非断言型单测。
11. **版本号不一致**：README 写 v4.1，`main.py` 注释写 v2.0、system_status 返回 `"version": "2.0.0"`，介绍书写 v2.0——多处版本号不统一。
12. **提交历史单薄**：仅 2 次提交，无法支撑"原创性/演进过程"叙事。

---

## 六、建议行动项（按优先级）

**提交前必做（1-2 天）**
1. 补齐洛南案例数据（至少：边界 GeoJSON + DEM + 约束图层 + 一份 NDVI/LST 缓存），并更新 manifest.json 的 status/sha256。
2. 大棚检测要么接入 YOLO 出真实结果，要么在 UI/文档显式标注"演示占位"。
3. 实测断网/iServer 离线降级链路，截图留存。
4. 统一入口：确认以 `main.py` 为准，删除或归档 `main_tianyan.py`。

**代码卫生（0.5 天）**
5. 删除 5 个 `.bak` 与前端开发脚本（或移入 `docs/archive/`）。
6. `.gitignore` 增加 `.omo/`、`*.bak`；`config.py` 去掉硬编码路径默认值。
7. 统一版本号（README / main.py / system_status / 介绍书）。

**答辩加分（后续）**
8. 将提交历史整理为分里程碑提交（认证 → 集成 → 3D → 多用户），生成演进证据。
9. 扩充单元测试（认证、权限隔离、降级分支），产出 pytest 覆盖率报告。
10. 整理一份《数据说明文档》与《SuperMap 技术应用说明》，对应大赛"数据/合规"评分项。

---

## 七、一句话总结

**这是一个架构完整、集成度高的比赛作品（约 2.5 万行、34 个 iServer API、多用户 SaaS 全链路），当前最大短板不在代码而在"可现场闭环的证据链"：洛南案例数据全部缺失、大棚检测为骨架、iServer/GEE 强依赖未做离线闭环验证。下一步应优先补数据与降级实测，其次清理代码卫生，最后用分里程碑提交补足演进叙事。**

---

## 2026-08-03 M0-M3 复核更新

本轮已经完成并验证四个基础里程碑：

- 运行版本统一为 `4.2.0`，`TIANYAN_ROOT` 默认值改为项目根目录，并补充环境基线。
- 三维页面新增地形诊断接口和独立 `TerrainController`，明确区分 SCT、Cesium 在线地形和椭球降级。
- 展示站入口、登录页和真实控制台通过白名单 `next` 串联，外部跳转目标会被拒绝。
- 新增项目级 iServer 数据中心，资产列表、登记、元数据、预览、删除均受当前用户和项目双重隔离。

本轮回归结果为 Python `tests/` 21 passed、Node 6 passed；应用级 TestClient smoke 已确认静态页面、系统状态和 `POST .../iserver-assets/import` 路由可用。真实 iServer/SuperMap3D 联调和洛南案例数据仍是后续现场证据，不应在答辩材料中用静态占位信息替代。
