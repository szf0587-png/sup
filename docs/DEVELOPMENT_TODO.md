# 天眼寻珍·苍穹 - 后续开发计划备忘录

**创建时间**: 2026-07-26
**状态**: ✅ 部分完成（iServer深度集成 + 3D Realspace 工作台）
**最后更新**: 2026-08-01

---

## 🎉 已完成工作

### ✅ 第1个月：iServer深度集成（Week 1-4）
- ✅ Week 1-2: 补充空间分析API（坡度、密度、叠加、插值）
- ✅ Week 3: 地图服务集成（替换OSM底图）
- ✅ Week 4: 数据编辑功能（要素增删改查）

### ✅ 第3个月：完善和三维（Week 9-11）
- ✅ Week 9: 数据管理完善（属性表、多格式导入导出）
- ✅ Week 10-11: 三维场景准备（地形、模型上传）
- ✅ Week 12: 测试和优化

### ✅ 3D Realspace 工作台（2026-07-27 → 08-01）
- ✅ `frontend/map3d.html` 全新深色科技风 3D 决策视图（Cesium 1.114 / SuperMap3D 引擎自适应）
- ✅ `server/api/scene_3d.py` 重构：场景/数据集目录解析、SCT TerrainFileLayer 检测、相机视角从场景自动读取
- ✅ `server/services/land_assessment.py` 能力检测：`dem_available` / `realspace_available` / `3d_scenes`
- ✅ `server/integrations/iserver_client.py` 服务名规范化（兼容 `name/rest` 格式）
- ✅ `frontend/land-workbench.js` 3D 入口：检测到 Realspace 服务后才跳转
- ✅ `scripts/prepare-3d-workspace.ps1` / `prepare_3d_workspace.py`：一键生成 3D 工作区（DEM → UDBX 网格、SMWU 工作空间、可选 OSM 导入）
- 🔄 待办：等待 iServer 端实际发布 3D 场景后，用真实 SCT 地形缓存联调 Realspace 渲染

### 📊 成果统计
- 新增API接口：**34个**
- 新增API模块：**5个**（spatial_analysis, map_services, data_editing, data_management, scene_3d）
- iServer功能利用率：20% → **85%**
- 详细报告：[ISERVER_INTEGRATION_REPORT.md](./ISERVER_INTEGRATION_REPORT.md)
- 测试清单：[API_TESTING_CHECKLIST.md](./API_TESTING_CHECKLIST.md)
- 项目总览：[README.md](../README.md)

---

## 📋 开发任务清单

### 🎨 阶段 0：前端优化和完善（3-4 天）

#### 任务 0.1：设计和实现浏览网站
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 1-2 天

**需求描述**:
创建一个产品展示/介绍网站，作为用户访问的第一个页面。

**功能要求**:
- [ ] 产品介绍页（Landing Page）
  - [ ] 产品 Logo 和名称展示
  - [ ] 产品简介和核心功能介绍
  - [ ] 核心亮点展示（3-4 个）
  - [ ] 应用场景展示
  - [ ] 用户评价/案例展示（可选）
  
- [ ] 导航结构
  - [ ] 首页（Home）
  - [ ] 功能介绍（Features）
  - [ ] 关于我们（About）
  - [ ] 联系我们（Contact）
  - [ ] 登录按钮（右上角）

- [ ] 视觉设计
  - [ ] 延续深色主题 + 绿色科技风格
  - [ ] 大尺寸 Hero 区域（产品主图）
  - [ ] 动画效果（滚动动画、悬停效果）
  - [ ] 响应式设计（移动端适配）

**技术要点**:
```
技术栈
├── HTML5 + CSS3
├── Tailwind CSS（保持一致性）
├── 原生 JavaScript（轻量级）
├── 动画库: AOS (Animate On Scroll) 或 GSAP
└── 图标: Heroicons / Lucide
```

**页面流程**:
```
用户访问
    ↓
浏览网站 (index.html)
    ↓ 点击"登录"或"开始使用"
登录页面 (login.html)
    ↓ 登录成功
控制台 (app.html / dashboard.html)
```

**参考设计**:
- Linear.app
- Notion.so
- Mapbox.com
- Climate FieldView

---

#### 任务 0.2：美化登录界面
**优先级**: ⭐⭐⭐⭐
**预计时间**: 0.5-1 天

**优化内容**:
- [ ] 优化背景动画效果
  - [ ] 更流畅的动画
  - [ ] 添加粒子效果（可选）
  - [ ] 添加地图元素装饰

- [ ] 优化表单设计
  - [ ] 更清晰的输入框样式
  - [ ] 更好的错误提示动画
  - [ ] 添加"忘记密码"功能
  - [ ] 添加"记住我" checkbox 样式优化

- [ ] 添加品牌元素
  - [ ] 更大更醒目的 Logo
  - [ ] 品牌标语（Slogan）
  - [ ] 产品宣传文案

- [ ] 响应式优化
  - [ ] 移动端适配
  - [ ] 平板端适配

**设计参考**:
- Stripe Login
- GitHub Login
- Linear Login

---

#### 任务 0.3：控制台重命名和入口优化
**优先级**: ⭐⭐⭐
**预计时间**: 0.5 天

**修改内容**:
- [ ] 将 `index.html` 重命名为 `app.html` 或 `dashboard.html`
- [ ] 创建新的 `index.html` 作为浏览网站首页
- [ ] 修改登录成功后的跳转目标
- [ ] 更新服务器路由配置

**文件结构**:
```
frontend/
├── index.html          # 浏览网站（新建）
├── login.html          # 登录页面（优化）
├── app.html            # 控制台主页（原 index.html）
├── auth.js             # 认证工具
├── navbar.js           # 导航栏组件
├── workspace.js        # 工作区功能
└── workspace.css       # 样式文件
```

---

### 🗺️ 阶段 1：基础 GIS 交互功能（1-2 周）

#### 任务 1.1：要素弹窗（Popup）
**优先级**: ⭐⭐⭐⭐⭐ 最快见效
**预计时间**: 1-2 天

**功能需求**:
- [ ] 点击地图要素显示弹窗
- [ ] 显示要素属性信息
- [ ] 自定义弹窗样式（深色主题）
- [ ] 弹窗位置智能调整
- [ ] 支持 HTML 内容渲染

**技术实现**:
```javascript
// 基于 Leaflet Popup
layer.bindPopup(`
  <div class="custom-popup">
    <h3>${feature.properties.name}</h3>
    <p>面积: ${feature.properties.area} 公顷</p>
    <p>类型: ${feature.properties.type}</p>
  </div>
`);
```

**样式设计**:
- 深色主题
- 毛玻璃效果
- 绿色强调色
- 统一的字体和间距

---

#### 任务 1.2：底图切换
**优先级**: ⭐⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 底图选择控件
- [ ] 支持多种底图
  - [ ] 卫星影像（默认）
  - [ ] 街道地图
  - [ ] 地形图
  - [ ] 灰度底图
  - [ ] 深色底图

**底图源**:
```javascript
const basemaps = {
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  street: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  terrain: 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
};
```

**UI 设计**:
- 浮动控件（右上角）
- 缩略图预览
- 平滑切换动画

---

#### 任务 1.3：比例尺和指北针
**优先级**: ⭐⭐⭐
**预计时间**: 0.5 天

**功能需求**:
- [ ] 比例尺控件
  - [ ] 动态显示当前比例尺
  - [ ] 支持公制/英制切换
  - [ ] 位置：左下角

- [ ] 指北针控件
  - [ ] 指示地图朝向
  - [ ] 点击重置为正北
  - [ ] 位置：左上角

**技术实现**:
```javascript
// Leaflet 自带
L.control.scale({ position: 'bottomleft' }).addTo(map);

// 自定义指北针
L.control.compass({ position: 'topleft' }).addTo(map);
```

---

#### 任务 1.4：测量工具
**优先级**: ⭐⭐⭐⭐
**预计时间**: 1-2 天

**功能需求**:
- [ ] 距离测量
  - [ ] 点击多点绘制测量线
  - [ ] 实时显示距离
  - [ ] 支持多段线

- [ ] 面积测量
  - [ ] 点击多点绘制多边形
  - [ ] 实时显示面积
  - [ ] 支持复杂多边形

- [ ] 坐标拾取
  - [ ] 点击地图显示坐标
  - [ ] 支持多种坐标格式
  - [ ] 一键复制坐标

**UI 设计**:
- 工具按钮组
- 测量结果浮动显示
- 清除测量按钮

**技术实现**:
```javascript
// 使用 Leaflet.draw 或 Leaflet-measure
L.control.measure({
  position: 'topright',
  primaryLengthUnit: 'meters',
  primaryAreaUnit: 'hectares'
}).addTo(map);
```

---

### 🗂️ 阶段 2：图层管理系统（2-3 天）

#### 任务 2.1：图层列表面板
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 1-2 天

**功能需求**:
- [ ] 图层列表 UI
  - [ ] 图层名称显示
  - [ ] 图层类型图标（矢量/栅格）
  - [ ] 折叠/展开图层组
  - [ ] 拖拽排序

- [ ] 图层操作
  - [ ] 显示/隐藏开关
  - [ ] 缩放至图层范围
  - [ ] 删除图层
  - [ ] 图层属性设置

**数据结构**:
```javascript
const layers = [
  {
    id: 'layer_001',
    name: '土壤类型',
    type: 'vector',
    visible: true,
    opacity: 1.0,
    order: 1,
    group: '数据图层'
  },
  // ...
];
```

**UI 位置**:
- 右侧浮动面板
- 可折叠/展开
- 与其他面板协调

---

#### 任务 2.2：图层显示/隐藏开关
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 0.5 天

**功能需求**:
- [ ] 眼睛图标切换按钮
- [ ] 点击切换图层可见性
- [ ] 状态持久化（localStorage）
- [ ] 动画过渡效果

**实现**:
```javascript
function toggleLayer(layerId) {
  const layer = layers.find(l => l.id === layerId);
  layer.visible = !layer.visible;
  
  if (layer.visible) {
    layer.leafletLayer.addTo(map);
  } else {
    map.removeLayer(layer.leafletLayer);
  }
}
```

---

#### 任务 2.3：图层透明度滑块
**优先级**: ⭐⭐⭐⭐
**预计时间**: 0.5 天

**功能需求**:
- [ ] 透明度滑块（0-100%）
- [ ] 实时预览效果
- [ ] 数值显示
- [ ] 重置按钮

**实现**:
```javascript
function setLayerOpacity(layerId, opacity) {
  const layer = layers.find(l => l.id === layerId);
  layer.opacity = opacity;
  layer.leafletLayer.setOpacity(opacity);
}
```

---

#### 任务 2.4：图层顺序调整
**优先级**: ⭐⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 上移/下移按钮
- [ ] 拖拽排序
- [ ] 置顶/置底快捷操作
- [ ] Z-index 自动管理

**实现**:
```javascript
function moveLayerUp(layerId) {
  // 调整图层顺序
  const index = layers.findIndex(l => l.id === layerId);
  if (index > 0) {
    [layers[index], layers[index-1]] = [layers[index-1], layers[index]];
    updateLayerOrder();
  }
}
```

---

### 📊 阶段 3：数据查看和编辑（3-4 天）

#### 任务 3.1：属性表组件
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 2 天

**功能需求**:
- [ ] 表格显示
  - [ ] 列头（字段名）
  - [ ] 数据行
  - [ ] 分页
  - [ ] 虚拟滚动（大数据）

- [ ] 交互功能
  - [ ] 排序（点击列头）
  - [ ] 筛选
  - [ ] 搜索
  - [ ] 选择行

- [ ] 联动功能
  - [ ] 点击行高亮地图要素
  - [ ] 地图点击定位到表格行

**UI 设计**:
- 底部抽屉式面板
- 可调整高度
- 深色主题表格

---

#### 任务 3.2：属性查看
**优先级**: ⭐⭐⭐⭐
**预计时间**: 0.5 天

**功能需求**:
- [ ] 字段类型识别（文本/数字/日期）
- [ ] 格式化显示
- [ ] 空值处理
- [ ] 长文本省略

---

#### 任务 3.3：属性编辑
**优先级**: ⭐⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 单元格编辑
- [ ] 数据验证
- [ ] 保存/取消
- [ ] 撤销/重做
- [ ] 批量编辑

**权限控制**:
- 只能编辑自己的数据
- 管理员可编辑所有数据

---

#### 任务 3.4：数据筛选
**优先级**: ⭐⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 按字段筛选
- [ ] 多条件组合（AND/OR）
- [ ] 常用筛选条件保存
- [ ] 筛选结果统计

**筛选类型**:
```
数值: >, <, =, ≥, ≤, ≠
文本: 等于, 包含, 开始于, 结束于
日期: 在...之前, 在...之后, 在...之间
```

---

### 🎨 阶段 4：符号化系统（4-5 天）

#### 任务 4.1：单一符号
**优先级**: ⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 统一样式设置
  - [ ] 颜色选择器
  - [ ] 线宽设置
  - [ ] 填充透明度
  - [ ] 边框样式

---

#### 任务 4.2：分类符号
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 2 天

**功能需求**:
- [ ] 选择分类字段
- [ ] 自动识别唯一值
- [ ] 为每个类别分配颜色
- [ ] 配色方案选择
- [ ] 图例生成

**示例**:
```
土壤类型 (分类符号)
├── 红壤    → #ff6b6b
├── 黄壤    → #ffd93d
├── 棕壤    → #8b4513
└── 黑土    → #2d3436
```

---

#### 任务 4.3：分级符号
**优先级**: ⭐⭐⭐⭐⭐
**预计时间**: 2 天

**功能需求**:
- [ ] 选择数值字段
- [ ] 分级方法选择
  - [ ] 等间距
  - [ ] 分位数
  - [ ] 自然断点
  - [ ] 标准差

- [ ] 分级数量设置（3-10 级）
- [ ] 颜色渐变设置
- [ ] 图例生成

**示例**:
```
适宜性得分 (分级符号)
├── 0-20    → #d32f2f (低)
├── 20-40   → #ff9800 (较低)
├── 40-60   → #fdd835 (中等)
├── 60-80   → #8bc34a (较高)
└── 80-100  → #4caf50 (高)
```

---

#### 任务 4.4：自定义样式
**优先级**: ⭐⭐⭐
**预计时间**: 1 天

**功能需求**:
- [ ] 表达式编辑器
- [ ] 基于属性的动态样式
- [ ] 样式模板保存
- [ ] 样式导入/导出

---

## 📅 时间规划

### 第一周（7天）
```
Day 1-2: 浏览网站设计和开发
Day 3:   登录界面美化
Day 4:   控制台重命名和入口优化
Day 5-6: 要素弹窗 + 底图切换
Day 7:   比例尺、指北针、测量工具
```

### 第二周（7天）
```
Day 8-9:  图层管理系统
Day 10-11: 属性表组件
Day 12:   属性编辑和筛选
Day 13-14: 符号化系统（分类+分级）
```

---

## 🎯 优先级总结

### 🔴 立即开始（明天）
1. **浏览网站设计** - 产品门户
2. **登录界面美化** - 第一印象
3. **要素弹窗** - 最基础的交互

### 🟡 本周内完成
4. 底图切换
5. 测量工具
6. 比例尺和指北针

### 🟢 下周完成
7. 图层管理
8. 属性表
9. 符号化

---

## 📚 参考资源

### 设计灵感
- **浏览网站**: Linear.app, Notion.so, Mapbox.com
- **登录页面**: Stripe, GitHub, Linear
- **GIS 功能**: ArcGIS Online, QGIS, Mapbox Studio

### 技术文档
- **Leaflet.js**: https://leafletjs.com
- **Leaflet.draw**: https://github.com/Leaflet/Leaflet.draw
- **Leaflet-measure**: https://github.com/ljagis/leaflet-measure
- **Tailwind CSS**: https://tailwindcss.com

---

## ✅ 备忘事项

- [ ] 所有新功能要保持统一的设计风格（深色主题 + 绿色科技风）
- [ ] 每个功能完成后立即测试
- [ ] 及时更新文档
- [ ] 注意响应式设计
- [ ] 代码质量和注释
- [ ] Git 提交规范

---

## 💾 保存位置

**文件**: `docs/DEVELOPMENT_TODO.md`
**创建时间**: 2026-07-26 23:45
**下次查看**: 2026-07-27

---

**备注**: 这是一份详细的开发计划，明天开始按优先级逐步实施。重点是先完成浏览网站和登录界面美化，然后再补充基础 GIS 功能。

🎯 **明天的首要任务**: 设计浏览网站！
