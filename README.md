# 天眼寻珍·苍穹 - 土地资源评估工作台

基于 SuperMap iServer 的土地资源分析与可视化工作台。系统围绕评估边界开展逐步空间分析，支持将每一步的文字结果和地图要素返回到同一工作区。

**当前版本**: v4.2（多用户 SaaS + iServer 深度集成 + 3D Realspace 工作台）

---

## 功能

### 多用户平台
- JWT 认证：注册、登录、登出、记住我、自动登录、Token 过期处理
- 用户数据隔离：每个用户只能访问自己的数据，管理员可访问全部
- 项目管理：多项目支持、激活机制（同时仅一个激活项目）、项目关联数据集
- 数据集管理：GeoJSON/Shapefile/GeoTIFF 上传、元数据自动提取、用户目录隔离
- 金标准管理：创建/编辑/重命名/删除，自动关联激活项目，数据库存储

### 土地资源分析
- 交互式地图、评估范围绘制、缩放、定位与底图切换（Esri 卫星 + iServer 地图服务）
- 默认分析：范围统计、水体约束、缓冲统计、道路空间查询、行政区定位
- 行政区名称输出和行政区边界地图可视化
- 水面、湖泊、主河流与普通河流的精确空间相交查询
- 物候匹配、区域筛选（Top N 乡镇排序）、地块精评、报告生成

### iServer 深度集成（34 个 API）
- **空间分析（8）**: 坡度/坡向/山体阴影、核密度/点密度、加权叠加、IDW/Kriging 插值
- **地图服务（5）**: 服务列表、服务详情、瓦片配置、地图列表、推荐底图
- **数据编辑（6）**: 要素增删改查、ID/SQL 查询、批量属性更新
- **数据管理（7）**: 元数据、数据集列表、字段添加、属性表、GeoJSON/CSV 导入导出
- **三维服务（6）**: 场景列表/详情/配置、地形信息、地形生成指南、三维模型上传

### 3D Realspace 工作台（进行中）
- 深色科技风 3D 决策视图（`frontend/map3d.html`）
- 自动发现 iServer 发布的 `3D-*` / `realspace-*` 三维服务
- 场景/数据集目录解析、TerrainFileLayer（SCT 地形）检测
- 初始相机视角从场景 camera 自动读取
- 引擎自动选择：SuperMap3D（官方 WebGL）→ 回退 Cesium 1.114
- 一键生成 3D 工作区（DEM 导入 UDBX、SMWU 工作空间准备）：`scripts/prepare-3d-workspace.ps1`

---

## 技术栈

- **Backend**: Python, FastAPI, SQLAlchemy 2.x, SQLite, PyJWT, bcrypt
- **GIS**: SuperMap iServer REST, SuperMap iObjects Python runtime, iobjectspy
- **Frontend**: HTML, CSS, JavaScript, Leaflet.js, Cesium 1.114 / SuperMap3D, Tailwind CSS
- **图表**: ECharts, Chart.js

---

## 运行环境

- Windows 10/11
- Python 3.9+（已验证 3.9 / 3.12 / 3.13）
- SuperMap iServer 2026（默认地址 `http://127.0.0.1:8090`）
- 可选：SuperMap iDesktop / iObjects Python 运行环境（用于 3D 工作区准备与 DEM 导入）

---

## 快速启动

### 1. 初始化数据库

```powershell
python scripts/init_database.py
```

### 2. 设置本地服务参数

```powershell
$env:ISERVER_BASE = "http://127.0.0.1:8090"
$env:ISERVER_USER = "admin"
$env:ISERVER_PASSWORD = "your-password"
$env:FASTAPI_HOST = "127.0.0.1"
$env:FASTAPI_PORT = "8000"
```

### 3. 启动应用

```powershell
python server/main.py
```

项目提供了 Windows 启动脚本：

```powershell
.\scripts\start.ps1 -Port 8000
```

### 4. 访问应用

- 工作台: [http://127.0.0.1:8000](http://127.0.0.1:8000)（未登录自动跳转登录页）
- 登录页: [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)
- 3D 工作台: [http://127.0.0.1:8000/map3d.html](http://127.0.0.1:8000/map3d.html)
- API 文档: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**默认管理员账号**: `admin` / `admin123`（请在部署后立即修改密码）

---

## iServer 数据要求

默认配置使用 `China100` 数据源。水体约束会查询以下已发布数据集：

- `Water_R`
- `Lake_R`
- `MainRiver_R`
- `MainRiver_L`
- `River_L`

道路空间查询默认使用 `NationalRd_L`、`Expressway_L` 和 `ProvincialRd_L`。行政区定位使用 `Province_R`。

水体与道路结果采用 iServer 的 `INTERSECT` 空间关系。结果为 0 表示当前发布的数据中没有与评估范围相交的要素，并不代表卫星影像中不存在水体或道路。

三维场景要求 iServer 已发布 `3D-*` 或 `realspace-*` 前缀的 Realspace 服务（含 SCT 地形缓存图层）。工作台启动时会自动检测 `dem_available` / `realspace_available` 能力状态。

---

## 原生地理处理工具

"iServer 地理处理工具"页面会实时读取当前 Spatial Analyst 服务发布的原生资源。原生算子使用 iServer REST 原始参数对象执行，参数名称和结构以当前 iServer 服务约定为准。

当前本地 iServer 服务可发现：

- 24 个几何分析算子
- 10 类数据集算子
- 330 个已发布数据集算子实例

---

## 测试

```powershell
python -m unittest tests.test_land_assessment tests.test_map_tiles -v
```

全量 API 集成测试：

```powershell
python scripts/test_all_apis.py
```

---

## 项目结构

```text
frontend/        Web 工作台、iServer 工具页、3D Realspace 工作台
  index.html        主页面（三栏布局）
  login.html        登录页面
  map3d.html        3D 工作台（Cesium/SuperMap3D）
  land-workbench.js 工作台核心逻辑
  js/api/           5 个 API 封装模块
  js/components/    侧边工具栏、右面板、分析/数据管理器
  js/map/           Leaflet 地图、绘制、图层管理器
server/
  api/              FastAPI 路由（认证/数据集/项目/金标准/物候/筛选/地块/报告/空间分析/地图/编辑/管理/三维）
  services/         土地资源评估、空间分析、物候、地块评价、报告生成等业务逻辑
  integrations/     iServer REST 客户端、GEE 客户端、UDBX 发布器
  models/           SQLAlchemy 数据模型（7 张表）
  middleware/       认证中间件（必须登录/可选登录/管理员）
  schemas/          Pydantic 请求/响应模型
  utils/            密码加密、JWT、文件上传
data/               示例与运行数据（用户数据按 user_id 隔离）
database/           SQLite 数据库（tianyan.db）
scripts/            启动、初始化、测试与 3D 工作区准备脚本
tests/              单元测试
docs/               部署、测试和设计文档
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| `docs/PROJECT_FINAL_SUMMARY.md` | 多用户系统改造完成总结（13/13 任务） |
| `docs/COMPLETE_INTEGRATION_SUMMARY.md` | 前后端完整对接实施报告（34 API） |
| `docs/ISERVER_INTEGRATION_REPORT.md` | iServer 深度集成报告 |
| `docs/DEVELOPMENT_TODO.md` | 开发计划与进度追踪 |
| `docs/API_TESTING_CHECKLIST.md` | API 测试清单 |
| `docs/DESIGN_SYSTEM.md` | 前端设计系统规范 |
| `docs/INSTALLATION_GUIDE.md` | 安装指南 |
| `docs/TROUBLESHOOTING.md` | 常见问题排查 |

---

## 安全与数据

`.gitignore` 已排除本地数据库、用户上传数据、3D 工作区（`data/3d/`）、运行快照、日志和环境变量文件。不要提交 iServer 密码、Token 或用户生产数据。

## 近期开发状态

- ✅ 多用户 SaaS 平台（任务 #8-#13 全部完成）
- ✅ iServer 深度集成（34 个 API，iServer 功能利用率 20% → 85%）
- ✅ 前端三栏 WebGIS 重构与登录/导航集成
- 🔄 3D Realspace 工作台（场景发现、SCT 地形检测、相机视角已接入；等待 iServer 端实际 3D 场景发布后联调）
