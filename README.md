# 天眼寻珍·苍穹 - 土地资源评估工作台

基于 SuperMap iServer 的土地资源分析与可视化工作台。系统围绕评估边界开展逐步空间分析，支持将每一步的文字结果和地图要素返回到同一工作区。

## 功能

- 交互式地图、评估范围绘制、缩放、定位与底图切换
- Esri 卫星影像底图，以及已发布 SuperMap iServer 地图服务的切换
- 土地资源默认分析：范围统计、水体约束、缓冲统计、道路空间查询、行政区定位
- 行政区名称输出和行政区边界地图可视化
- 水面、湖泊、主河流与普通河流的精确空间相交查询
- iServer Spatial Analyst 原生算子目录发现与原生 REST 参数执行
- 已发布算子的工作台固定管理，最多固定 6 个工具
- 阶段性结果列表与地图结果可视化
- SuperMap Realspace 三维能力状态检测

## 技术栈

- Backend: Python, FastAPI, SQLAlchemy, SQLite
- GIS: SuperMap iServer REST, SuperMap iObjects Python runtime
- Frontend: HTML, CSS, JavaScript, Leaflet

## 运行环境

- Windows 10/11
- Python 3.9+
- SuperMap iServer 2026（默认地址 `http://127.0.0.1:8090`）
- 可选：SuperMap iDesktop / iObjects Python 运行环境

## 快速启动

1. 启动 SuperMap iServer，并发布地图、数据和 Spatial Analyst 服务。
2. 创建并激活 Python 环境，安装依赖：

   ```powershell
   pip install -r requirements.txt
   ```

3. 设置本地服务参数：

   ```powershell
   $env:ISERVER_BASE = "http://127.0.0.1:8090"
   $env:ISERVER_USER = "admin"
   $env:ISERVER_PASSWORD = "your-password"
   $env:FASTAPI_HOST = "127.0.0.1"
   $env:FASTAPI_PORT = "8000"
   ```

4. 启动应用：

   ```powershell
   python server/main.py
   ```

5. 打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

项目提供了 Windows 启动脚本：

```powershell
.\scripts\start.ps1 -Port 8000
```

## iServer 数据要求

默认配置使用 `China100` 数据源。水体约束会查询以下已发布数据集：

- `Water_R`
- `Lake_R`
- `MainRiver_R`
- `MainRiver_L`
- `River_L`

道路空间查询默认使用 `NationalRd_L`、`Expressway_L` 和 `ProvincialRd_L`。行政区定位使用 `Province_R`。

水体与道路结果采用 iServer 的 `INTERSECT` 空间关系。结果为 0 表示当前发布的数据中没有与评估范围相交的要素，并不代表卫星影像中不存在水体或道路。

## 原生地理处理工具

“iServer 地理处理工具”页面会实时读取当前 Spatial Analyst 服务发布的原生资源。原生算子使用 iServer REST 原始参数对象执行，参数名称和结构以当前 iServer 服务约定为准。

当前本地 iServer 服务可发现：

- 24 个几何分析算子
- 10 类数据集算子
- 330 个已发布数据集算子实例

## 测试

```powershell
python -m unittest tests.test_land_assessment tests.test_map_tiles -v
```

## 项目结构

```text
frontend/       Web 工作台与 iServer 工具页面
server/api/     FastAPI 路由
server/services/ 土地资源评估与空间分析服务
server/integrations/ iServer REST 客户端
data/           示例与运行数据
tests/          单元测试
docs/           部署、测试和设计文档
```

## 安全与数据

`.gitignore` 已排除本地数据库、用户上传数据、运行快照、日志和环境变量文件。不要提交 iServer 密码、Token 或用户生产数据。
