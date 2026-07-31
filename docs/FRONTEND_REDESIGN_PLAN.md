# 天眼寻珍·苍穹 - 前端界面重新设计方案

**设计时间**: 2026-07-27  
**设计目标**: 完全对接后端34个API接口，打造专业WebGIS平台  
**参考平台**: ArcGIS Online, QGIS Cloud, SuperMap iPortal, Mapbox Studio

---

## 🎯 设计原则

### 1. API驱动设计
- 每个API接口都有对应的前端功能入口
- 工具面板组织遵循API分组逻辑
- 表单设计直接映射API参数

### 2. 专业WebGIS规范
- 左侧工具栏 + 中央地图 + 右侧面板（三栏布局）
- 可折叠/浮动面板，不遮挡地图
- 图层管理、属性表、分析工具独立模块

### 3. 深色主题 + 科技感
- 保持现有深色玻璃拟态风格
- 绿色科技主题（#22c55e）
- 数据可视化突出

---

## 📐 界面布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [顶部导航栏 - 64px]                                            │
│  Logo | 项目选择器 | 工作空间 | 数据 | 分析 | 3D | 用户菜单    │
├────┬────────────────────────────────────────────────────┬────────┤
│    │                                                    │        │
│ 左 │                                                    │  右    │
│ 侧 │                  [中央地图区域]                   │  侧    │
│ 工 │                                                    │  面    │
│ 具 │                  Leaflet/Cesium                    │  板    │
│ 栏 │                                                    │        │
│    │                                                    │  [动态]│
│ 64px                                                    │  400px │
│    │                                                    │  可调  │
├────┴────────────────────────────────────────────────────┴────────┤
│  [底部状态栏 - 32px]                                            │
│  坐标 | 比例尺 | 图层数 | 要素数 | iServer状态 | 帮助          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 顶部导航栏重新设计

### 布局（64px高）

```html
┌─────────────────────────────────────────────────────────────────┐
│ [Logo] 天眼寻珍·苍穹                                           │
│                                                                  │
│ [项目] ▼ | [工作台] [数据中心] [空间分析] [三维场景] [设置]    │
│                                                    [通知] [用户▼]│
└─────────────────────────────────────────────────────────────────┘
```

### 导航菜单项

| 菜单 | 功能 | API对接 |
|------|------|---------|
| **项目选择器** | 切换工作项目 | `GET /api/projects` |
| **工作台** | 当前页面（地图+工具） | - |
| **数据中心** | 数据管理、导入导出 | `/api/data-management/*` |
| **空间分析** | 打开分析工具面板 | `/api/spatial-analysis/*` |
| **三维场景** | 切换3D模式 | `/api/3d-services/*` |
| **设置** | 系统设置、底图配置 | `/api/map-services/*` |
| **用户菜单** | 个人资料、登出 | `/api/auth/*` |

---

## 🛠️ 左侧工具栏重新设计

### 工具分组（垂直排列，64px宽）

```
┌──────┐
│ [地图]│ ← 地图工具
│ [绘制]│ ← 绘制工具
│ [编辑]│ ← 编辑工具
│ [查询]│ ← 查询工具
│ [图层]│ ← 图层管理
│ [属性]│ ← 属性表
│ [量测]│ ← 量测工具
│ [分析]│ ← 空间分析
│ [数据]│ ← 数据管理
└──────┘
```

### 工具详细功能

#### 1. 🗺️ 地图工具（Map Tools）
```javascript
// 功能按钮
- 平移（默认）
- 缩放（放大/缩小）
- 全图
- 书签（保存视图）
- 底图切换 → 调用 /api/map-services/list
```

**对接API**:
- `GET /api/map-services/list` - 获取可用底图
- `GET /api/map-services/{service}/tile-config` - 加载底图

#### 2. ✏️ 绘制工具（Draw Tools）
```javascript
// 功能按钮
- 绘制点
- 绘制线
- 绘制多边形
- 绘制矩形
- 绘制圆形
- 保存 → 调用 /api/data-editing/features/add
```

**对接API**:
- `POST /api/data-editing/features/add` - 保存绘制要素

#### 3. ✂️ 编辑工具（Edit Tools）
```javascript
// 功能按钮
- 选择要素
- 移动要素
- 修改顶点
- 删除要素 → 调用 /api/data-editing/features/delete
- 批量编辑 → 调用 /api/data-editing/features/batch-update-attribute
```

**对接API**:
- `PUT /api/data-editing/features/update` - 更新要素
- `DELETE /api/data-editing/features/delete` - 删除要素
- `POST /api/data-editing/features/batch-update-attribute` - 批量修改

#### 4. 🔍 查询工具（Query Tools）
```javascript
// 功能按钮
- 点击查询
- 框选查询
- 圆形查询
- SQL查询 → 调用 /api/data-editing/features/query-by-sql
- 空间查询（相交、包含、缓冲）
```

**对接API**:
- `POST /api/data-editing/features/query-by-ids` - ID查询
- `POST /api/data-editing/features/query-by-sql` - SQL查询

#### 5. 📚 图层管理（Layers）
```javascript
// 面板内容（右侧弹出）
- 图层树
  ├─ 底图
  ├─ 数据图层
  │   ├─ [✓] 洛南县边界
  │   ├─ [✓] 核桃种植点
  │   └─ [ ] DEM地形
  └─ 分析结果
- 操作按钮
  - 添加图层 → 调用 /api/datasets/list
  - 删除图层
  - 图层样式
  - 透明度调整
```

**对接API**:
- `GET /api/datasets` - 获取数据集列表
- `GET /api/data-management/datasets/{datasource}/list` - 列出数据集

#### 6. 📋 属性表（Attributes）
```javascript
// 面板内容（底部弹出或右侧）
- 表格显示要素属性
- 分页（100条/页）
- 排序、过滤
- 字段管理 → 调用 /api/data-management/fields/add
- 导出CSV/Excel
```

**对接API**:
- `GET /api/data-management/records/{datasource}/{dataset}` - 分页查询
- `POST /api/data-management/fields/add` - 添加字段
- `GET /api/data-management/datasets/{datasource}/{dataset}/metadata` - 获取元数据

#### 7. 📏 量测工具（Measure）
```javascript
// 功能按钮
- 量测距离
- 量测面积
- 量测角度
- 清除测量
```

#### 8. 🔬 空间分析（Analysis）
```javascript
// 面板内容（右侧弹出，多级菜单）
分析工具箱
├─ 地形分析
│   ├─ 坡度分析 → /api/spatial-analysis/terrain/slope
│   ├─ 坡向分析 → /api/spatial-analysis/terrain/aspect
│   └─ 山体阴影 → /api/spatial-analysis/terrain/hillshade
├─ 密度分析
│   ├─ 核密度 → /api/spatial-analysis/density/kernel
│   └─ 点密度 → /api/spatial-analysis/density/point
├─ 栅格分析
│   └─ 加权叠加 → /api/spatial-analysis/overlay/weighted
├─ 插值分析
│   ├─ IDW插值 → /api/spatial-analysis/interpolation/idw
│   └─ Kriging插值 → /api/spatial-analysis/interpolation/kriging
└─ 缓冲区分析
```

**对接API**: 所有 `/api/spatial-analysis/*` 接口

#### 9. 💾 数据管理（Data）
```javascript
// 面板内容（右侧弹出）
数据管理
├─ 数据导入
│   ├─ 导入GeoJSON → /api/data-management/import/geojson
│   ├─ 导入CSV → /api/data-management/import/csv
│   └─ 导入Shapefile（待实现）
├─ 数据导出
│   ├─ 导出GeoJSON → /api/data-management/export/geojson
│   └─ 导出CSV
└─ 数据集管理
    ├─ 创建数据集
    ├─ 删除数据集
    └─ 数据集属性
```

**对接API**: 所有 `/api/data-management/*` 接口

---

## 📊 右侧动态面板设计

### 面板类型

#### 1. 工具面板（Tool Panel）
- 点击左侧工具栏按钮时弹出
- 400px宽，可调整
- 可最小化到右侧边缘

#### 2. 属性面板（Properties Panel）
- 选中要素时显示属性
- 可编辑属性字段
- 保存按钮 → 调用 `/api/data-editing/features/update`

#### 3. 分析结果面板（Results Panel）
- 显示分析进度
- 显示结果统计
- 结果可视化（图表）
- 导出结果

#### 4. 图层样式面板（Style Panel）
- 符号编辑
- 颜色配置
- 标注设置

---

## 🎛️ 核心功能模块设计

### 模块1: 数据中心（Data Center）

**页面路由**: `/data-center`

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│ [数据中心]                                              │
├─────────┬───────────────────────────────────────────────┤
│ 数据源  │  数据集列表                                   │
│         │  ┌────────────────────────────────────────┐   │
│ ▸ 本地  │  │ [+新建] [导入] [导出] [刷新]           │   │
│ ▾ iServer│ ├────────────────────────────────────────┤   │
│   ├ 洛南 │  │ 📁 洛南县_边界    | 面 | 1   | 12KB │   │
│   ├ 用户 │  │ 📍 核桃种植点      | 点 | 156 | 8KB  │   │
│   └ 临时 │  │ 🗺️ DEM地形        | 栅格| -   | 2.5MB│   │
│         │  └────────────────────────────────────────┘   │
│ [导入]  │                                               │
│ ▸ 导出  │  [预览区域 - 显示选中数据集的地图预览]        │
└─────────┴───────────────────────────────────────────────┘
```

**功能操作**:
1. 数据导入
   - 点击"导入" → 弹出对话框
   - 选择文件格式：GeoJSON / CSV / Shapefile
   - 上传文件 → 调用 `/api/data-management/import/{format}`
   - 显示导入进度
   - 导入完成 → 刷新数据集列表

2. 数据导出
   - 选中数据集
   - 点击"导出" → 选择格式
   - 调用 `/api/data-management/export/{format}`
   - 下载文件

3. 数据集管理
   - 双击数据集 → 显示元数据
   - 右键菜单：查看属性 / 编辑 / 删除 / 发布到地图

---

### 模块2: 空间分析工作台（Spatial Analysis Workspace）

**页面路由**: `/analysis`

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│ [空间分析工作台]                                        │
├─────────┬───────────────────────────────────────────────┤
│ 分析工具│  分析配置面板                                 │
│         │  ┌────────────────────────────────────────┐   │
│ 地形分析│  │ 【坡度分析】                           │   │
│ ▾坡度   │  │ 数据源: [选择数据源 ▼]                 │   │
│  坡向   │  │ 数据集: [选择DEM ▼]                    │   │
│  阴影   │  │ 坡度类型: ◉ 度 ○ 百分比               │   │
│         │  │ Z因子: [1.0    ]                       │   │
│ 密度分析│  │ [运行分析] [重置]                      │   │
│ ▸核密度 │  └────────────────────────────────────────┘   │
│  点密度 │                                               │
│         │  分析结果                                     │
│ 栅格分析│  ┌────────────────────────────────────────┐   │
│ ▸加权叠加│ │ ✓ 坡度分析完成                         │   │
│         │  │ 结果ID: slope_result_20260727_001      │   │
│ 插值分析│  │ 耗时: 2.3秒                            │   │
│ ▸IDW    │  │                                        │   │
│  Kriging│  │ [查看结果] [导出] [发布到地图]         │   │
│         │  └────────────────────────────────────────┘   │
└─────────┴───────────────────────────────────────────────┘
```

**核心交互流程**:
1. 选择分析类型（左侧树）
2. 配置参数（右侧表单）
3. 运行分析 → 调用API
4. 显示进度（进度条 + 百分比）
5. 显示结果（统计 + 预览）
6. 操作结果：查看 / 导出 / 发布

**示例：坡度分析完整流程**

```javascript
// 1. 用户选择"坡度分析"
// 2. 自动加载数据源列表
const datasources = await Auth.fetch('/api/data-management/datasets/luonan_ds/list');

// 3. 用户选择DEM数据集
// 4. 配置参数
const params = {
    datasource: 'luonan_ds',
    dataset: 'luonan_dem',
    slope_type: 'DEGREE',
    z_factor: 1.0
};

// 5. 运行分析
const response = await Auth.fetch('/api/spatial-analysis/terrain/slope', {
    method: 'POST',
    body: JSON.stringify(params)
});

// 6. 显示结果
const result = await response.json();
showResult(result.result_id);

// 7. 可选：发布到地图
addLayerToMap(result.result_id);
```

---

### 模块3: 三维场景（3D Viewer）

**页面路由**: `/3d-viewer`

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│ [三维场景]                       [场景选择▼] [退出3D]   │
├─────────┬───────────────────────────────────────────────┤
│ 场景控制│                                               │
│         │                                               │
│ [图层]  │                                               │
│ ▾地形   │           [Cesium 三维地球]                   │
│ ▸影像   │                                               │
│ ▸矢量   │                                               │
│         │                                               │
│ [视角]  │                                               │
│ 俯视    │                                               │
│ 斜视    │                                               │
│ 第一人称│                                               │
│         │                                               │
│ [分析]  │                                               │
│ 通视    │                                               │
│ 剖面    │                                               │
│ 淹没    │                                               │
└─────────┴───────────────────────────────────────────────┘
```

**对接API**:
- `GET /api/3d-services/scenes/list` - 获取场景列表
- `GET /api/3d-services/scenes/{name}/config` - 获取场景配置
- `GET /api/3d-services/terrain/{name}/info` - 获取地形服务

**Cesium初始化**:
```javascript
// 获取场景配置
const config = await Auth.fetch('/api/3d-services/scenes/luonan/config');
const sceneConfig = await config.json();

// 初始化Cesium
const viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: new Cesium.CesiumTerrainProvider({
        url: sceneConfig.terrain_url
    }),
    baseLayerPicker: false,
    animation: false,
    timeline: false
});

// 设置初始视角
viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(
        sceneConfig.initial_view.longitude,
        sceneConfig.initial_view.latitude,
        sceneConfig.initial_view.height
    ),
    orientation: {
        heading: Cesium.Math.toRadians(sceneConfig.initial_view.heading),
        pitch: Cesium.Math.toRadians(sceneConfig.initial_view.pitch)
    }
});
```

---

## 🎯 现有功能模块改造

### 改造1: 物候匹配模块

**当前问题**: 独立窗口，与其他模块割裂

**改造方案**:
```
物候匹配 → 整合到"空间分析"菜单
├─ 调整为右侧面板
├─ 保留现有功能
└─ 添加"保存结果"按钮 → 保存到数据集
```

### 改造2: 区域筛选模块

**当前问题**: 独立窗口

**改造方案**:
```
区域筛选 → 整合到"空间分析"菜单
├─ 分析参数配置（右侧面板）
├─ 结果展示在地图上
└─ Top5结果列表 → 可点击定位
```

### 改造3: 地块精评模块

**当前问题**: STEP1/2/3配置复杂

**改造方案**:
```
地块精评 → 整合到"空间分析"菜单 → "综合评价"
├─ 向导式界面（Wizard）
│   STEP 1: 选择评价因子
│   STEP 2: 设置权重
│   STEP 3: 运行评价
├─ 使用加权叠加API
│   POST /api/spatial-analysis/overlay/weighted
└─ 结果可视化
```

---

## 📱 响应式设计

### 桌面端（≥1024px）
```
三栏布局：左侧工具栏(64px) + 地图 + 右侧面板(400px)
```

### 平板端（768px-1023px）
```
两栏布局：左侧工具栏(隐藏) + 地图 + 浮动面板
- 工具栏变为顶部横向
- 右侧面板改为底部抽屉
```

### 移动端(<768px)
```
单栏布局：全屏地图 + 底部工具栏 + 浮动按钮
- 所有面板改为全屏弹窗
- 简化功能，保留核心操作
```

---

## 🎨 视觉设计规范

### 颜色系统（延续现有风格）

```css
/* 主题色 */
--primary: #22c55e;           /* 科技绿 */
--secondary: #3b82f6;         /* 蓝色 */
--accent: #f59e0b;            /* 金色（强调） */

/* 背景色 */
--bg-dark: #0f172a;           /* 深色背景（slate-900） */
--bg-glass: rgba(15,23,42,0.7);  /* 玻璃效果 */

/* 文字色 */
--text-primary: #f1f5f9;      /* 主文字（slate-100） */
--text-secondary: #94a3b8;    /* 次要文字（slate-400） */
--text-muted: #64748b;        /* 提示文字（slate-500） */

/* 边框色 */
--border: rgba(255,255,255,0.1);
--border-hover: rgba(34,197,94,0.3);
```

### 组件样式

#### 按钮
```html
<!-- 主按钮 -->
<button class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg 
               transition-colors duration-200 cursor-pointer">
    运行分析
</button>

<!-- 次要按钮 -->
<button class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg 
               transition-colors duration-200 cursor-pointer">
    取消
</button>

<!-- 图标按钮 -->
<button class="p-2 hover:bg-slate-700 rounded-lg transition-colors cursor-pointer">
    <svg class="w-5 h-5">...</svg>
</button>
```

#### 输入框
```html
<input type="text" 
       class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg
              text-slate-100 placeholder-slate-500
              focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500
              transition-colors duration-200">
```

#### 面板
```html
<div class="glass-panel rounded-xl p-4">
    <!-- 内容 -->
</div>

<style>
.glass-panel {
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}
</style>
```

---

## 🔧 技术实现方案

### 前端技术栈（保持现有）
- HTML5 + CSS3 + JavaScript（Vanilla）
- Tailwind CSS（样式）
- Leaflet.js（2D地图）
- Cesium.js（3D地球）
- Chart.js（图表）
- Axios/Fetch（HTTP请求）

### 代码组织结构

```
frontend/
├── index.html          # 主页面（工作台）
├── data-center.html    # 数据中心
├── analysis.html       # 空间分析工作台
├── 3d-viewer.html      # 三维场景
├── login.html          # 登录页（已有）
├── css/
│   ├── main.css        # 全局样式
│   ├── components.css  # 组件样式
│   └── workspace.css   # 工作区样式（已有）
├── js/
│   ├── auth.js         # 认证模块（已有）
│   ├── navbar.js       # 导航栏（已有）
│   ├── api/            # API调用封装
│   │   ├── spatial-analysis.js
│   │   ├── data-management.js
│   │   ├── map-services.js
│   │   ├── data-editing.js
│   │   └── scene-3d.js
│   ├── components/     # UI组件
│   │   ├── sidebar.js        # 左侧工具栏
│   │   ├── right-panel.js    # 右侧面板
│   │   ├── layer-tree.js     # 图层树
│   │   ├── attribute-table.js # 属性表
│   │   └── analysis-wizard.js # 分析向导
│   ├── map/            # 地图模块
│   │   ├── map-manager.js    # 地图管理
│   │   ├── draw-tools.js     # 绘制工具
│   │   ├── query-tools.js    # 查询工具
│   │   └── measure-tools.js  # 量测工具
│   └── utils/          # 工具函数
│       ├── geojson.js
│       ├── format.js
│       └── validate.js
└── assets/
    └── icons/          # SVG图标
```

---

## 📝 实施优先级

### Phase 1: 核心框架（1-2天）
- [x] 重新设计index.html布局
- [ ] 实现左侧工具栏组件
- [ ] 实现右侧动态面板组件
- [ ] 底图切换功能（对接map-services API）

### Phase 2: 数据管理（2-3天）
- [ ] 数据中心页面
- [ ] 数据导入导出功能
- [ ] 属性表组件
- [ ] 图层管理面板

### Phase 3: 编辑功能（2天）
- [ ] 绘制工具
- [ ] 编辑工具
- [ ] 保存到iServer功能

### Phase 4: 空间分析（3-4天）
- [ ] 分析工具面板
- [ ] 地形分析UI
- [ ] 密度分析UI
- [ ] 加权叠加UI（核心）
- [ ] 分析结果可视化

### Phase 5: 三维场景（2天）
- [ ] 3D页面
- [ ] Cesium集成
- [ ] 场景切换
- [ ] 地形加载

### Phase 6: 整合现有模块（1-2天）
- [ ] 物候匹配整合
- [ ] 区域筛选整合
- [ ] 地块精评改造

---

## 🎯 下一步行动

1. **立即开始**: 重新设计 `index.html`（主工作台）
2. **创建组件库**: 封装可复用的UI组件
3. **API封装**: 为每个API创建JavaScript封装函数
4. **逐步迁移**: 将现有功能逐步迁移到新架构

---

**文档版本**: v1.0  
**设计负责人**: Claude  
**审核状态**: 待用户确认
