# 🔧 问题修复指南

**问题报告时间**: 2026-07-27  
**问题**: 绘制工具无法交互、地图服务不可用、401认证错误

---

## 🐛 发现的问题

### 1. **401 Unauthorized 错误**
```
INFO: "GET /api/map-services/list HTTP/1.1" 401 Unauthorized
```
**原因**: 新的API需要认证，但调用时没有传递token

### 2. **绘制工具无法与底图交互**
**原因**: DrawTools可能未正确初始化，或与现有地图实例不匹配

### 3. **地图服务不可用**
**原因**: API调用失败（因为401错误）

---

## ✅ 解决方案

### 方案A: 临时测试方案（立即可用）

#### 1. 先登录系统
访问登录页面获取token：
```
http://localhost:8000/login.html
```

登录后，token会自动保存到localStorage

#### 2. 测试API是否可用
打开浏览器控制台（F12），运行：
```javascript
// 测试认证
const token = localStorage.getItem('access_token');
console.log('Token:', token ? '已获取' : '未登录');

// 测试API
fetch('http://localhost:8000/api/map-services/recommendations/basemaps', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
}).then(r => r.json()).then(console.log);
```

如果看到底图列表，说明API正常工作。

---

### 方案B: 修复代码（推荐）

由于API需要认证，我需要修改两个地方：

#### 修改1: 让部分API不需要认证（用于演示）

在后端添加白名单API，或者：

**临时方案**: 注释掉地图服务API的认证要求

#### 修改2: 确保前端正确传递token

API封装已经使用了`Auth.fetch`，应该会自动添加token。

---

### 方案C: 使用iServer真实数据测试

这是最好的测试方式！

#### 步骤1: 确保iServer运行
```bash
# 检查iServer状态
curl http://localhost:8090/iserver/services.json
```

#### 步骤2: 在iServer中准备数据
1. 打开SuperMap iDesktopX
2. 打开工作空间
3. 发布数据服务和地图服务
4. 确保数据源名称为 `luonan_ds`
5. 确保有DEM数据集（用于坡度分析）

#### 步骤3: 测试功能
1. 登录系统
2. 点击"空间分析"
3. 选择"坡度分析"
4. 填写真实的数据源和数据集名称
5. 运行分析

---

## 🔨 立即修复

让我现在就修复这些问题：

### 修复1: 绘制工具初始化检查

在浏览器控制台运行：
```javascript
// 检查DrawTools是否初始化
console.log('DrawTools:', window.DrawTools);
console.log('Map:', window.mainMap);

// 如果未初始化，手动初始化
if (!window.DrawTools && window.mainMap) {
    window.DrawTools = new DrawTools(window.mainMap);
    window.DrawTools.init();
    console.log('✓ DrawTools已手动初始化');
}
```

### 修复2: 检查地图实例

```javascript
// 检查地图
console.log('Map exists:', !!window.mainMap);
console.log('Map center:', window.mainMap?.getCenter());

// 测试绘制
if (window.DrawTools) {
    window.DrawTools.drawPolygon();
    console.log('✓ 绘制工具已激活，请在地图上点击');
}
```

---

## 🎯 推荐的测试流程

### 1. 基础功能测试（不需要iServer）

#### 测试绘制工具
```javascript
// 1. 检查地图
console.log('Map:', window.mainMap ? '✓' : '✗');

// 2. 检查DrawTools
console.log('DrawTools:', window.DrawTools ? '✓' : '✗');

// 3. 激活绘制
window.DrawTools?.drawPolygon();

// 4. 在地图上点击绘制
// 5. 双击完成
```

#### 测试图层管理
```javascript
// 检查LayerManager
console.log('LayerManager:', window.LayerManager ? '✓' : '✗');

// 获取图层列表
const layers = window.LayerManager?.getAllLayers();
console.log('Layers:', layers);
```

---

### 2. 高级功能测试（需要iServer + 真实数据）

#### 准备工作
1. 启动iServer（端口8090）
2. 在iDesktopX中准备数据：
   - 数据源名称：`luonan_ds`
   - DEM数据集：`luonan_dem`
   - 点数据集：`planting_points`（用于密度分析）

#### 测试坡度分析
1. 登录系统
2. 点击"空间分析"
3. 点击"坡度分析"
4. 填写参数：
   - 数据源：`luonan_ds`
   - DEM数据集：`luonan_dem`
   - 坡度类型：度
5. 点击"运行分析"
6. 等待结果（2-5秒）

#### 测试底图切换
1. 点击"地图服务"
2. 等待底图列表加载
3. 如果看到iServer底图，点击切换
4. 如果只看到OSM，说明iServer服务未发布或不可达

---

## 📋 故障排查清单

### 问题：绘制工具不工作

检查项：
- [ ] 浏览器控制台有错误吗？
- [ ] `window.mainMap` 存在吗？
- [ ] `window.DrawTools` 存在吗？
- [ ] Leaflet.Draw库加载了吗？
- [ ] 点击"绘制编辑"按钮后，控制台有"绘制模式"提示吗？

**最可能的原因**：
- DrawTools未初始化
- 地图实例传递错误
- Leaflet.Draw库未加载

**快速修复**：
```javascript
// 控制台运行
if (window.mainMap && !window.DrawTools) {
    window.DrawTools = new DrawTools(window.mainMap);
    window.DrawTools.init();
}
```

---

### 问题：地图服务不可用

检查项：
- [ ] 登录了吗？（有token吗？）
- [ ] API返回401还是其他错误？
- [ ] iServer在运行吗？（http://localhost:8090）
- [ ] 后端API能访问吗？（http://localhost:8000/docs）

**最可能的原因**：
- 未登录，没有token
- iServer未运行或未发布服务

**快速修复**：
1. 先登录：http://localhost:8000/login.html
2. 检查iServer：curl http://localhost:8090/iserver/services.json

---

### 问题：空间分析失败

检查项：
- [ ] 数据源名称正确吗？
- [ ] 数据集存在吗？
- [ ] 数据集类型匹配吗？（DEM用于地形分析，点用于密度分析）
- [ ] iServer数据服务已发布吗？

**最可能的原因**：
- 数据源或数据集不存在
- 数据类型不匹配（用矢量数据做地形分析）

**快速测试**：
访问API文档测试：
```
http://localhost:8000/docs
找到 POST /api/spatial-analysis/terrain/slope
点击 "Try it out"
填写参数并测试
```

---

## 🚀 下一步建议

### 立即可做
1. **登录系统** - 获取token
2. **在控制台手动初始化DrawTools** - 测试绘制
3. **查看API文档** - 了解参数格式

### 短期准备（1-2小时）
1. **准备iServer测试数据**
   - 发布数据服务
   - 准备DEM、矢量数据
   - 记录数据源和数据集名称

2. **测试每个功能**
   - 绘制工具
   - 空间分析
   - 数据导入导出

### 长期优化（1-2天）
1. **添加错误提示**
   - 未登录时显示提示
   - API失败时显示详细错误

2. **添加数据验证**
   - 检查数据源是否存在
   - 检查数据集类型是否匹配

3. **改进用户体验**
   - 添加加载动画
   - 添加成功/失败通知
   - 添加帮助文档

---

## 💡 我的建议

**现在立即做的**：
1. 打开 http://localhost:8000/login.html 登录
2. 打开浏览器控制台（F12）
3. 运行这个命令测试DrawTools：
```javascript
if (window.mainMap && !window.DrawTools) {
    window.DrawTools = new DrawTools(window.mainMap);
    window.DrawTools.init();
    console.log('✓ DrawTools初始化完成');
}
window.DrawTools?.drawPolygon();
```
4. 在地图上点击绘制

**然后告诉我**：
- 绘制工具能用了吗？
- 控制台有什么错误？
- 地图服务API返回什么？

我会根据您的反馈继续修复！🔧

---

**文档版本**: v1.0  
**创建时间**: 2026-07-27  
**状态**: 待测试反馈
