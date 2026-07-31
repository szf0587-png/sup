# 🚀 iServer启动和测试数据准备指南

## 📊 当前状态

### ✅ 已找到的测试数据
```
src/tianyan-cangqiong/data/users/user_admin/vector/daeb552cbedd.geojson
内容: {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [110.15, 34.09]}, "properties": {"name": "测试点"}}]}
```

### ❌ iServer状态
- **未运行**（端口8090未监听）
- **未找到安装目录**（需要手动定位）

---

## 🎯 方案A: 使用现有数据测试（不需要iServer）

### 可以立即测试的功能

#### 1. 数据导入测试
使用已有的GeoJSON文件测试数据导入：

在浏览器控制台运行：
```javascript
// 测试数据导入API
const testGeoJSON = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [110.15, 34.09]
        },
        "properties": {
            "name": "测试点",
            "description": "这是一个测试数据"
        }
    }]
};

// 创建Blob并模拟文件上传
const blob = new Blob([JSON.stringify(testGeoJSON)], {type: 'application/json'});
const file = new File([blob], 'test.geojson', {type: 'application/json'});

console.log('测试文件已创建:', file);
console.log('文件大小:', file.size, 'bytes');
```

#### 2. 不需要iServer的功能
这些功能可以直接测试（登录后）：
- ✅ **数据导入/导出** - 使用上面的GeoJSON
- ✅ **图层管理** - 管理已导入的数据
- ✅ **地图服务** - OSM底图始终可用
- ⚠️ **空间分析** - 需要iServer
- ⚠️ **底图切换（iServer）** - 需要iServer

---

## 🎯 方案B: 启动iServer（用于完整测试）

### 步骤1: 找到iServer安装位置

常见位置：
```
C:\Program Files\SuperMap\SuperMap iServer 11i
C:\Program Files\SuperMap\SuperMap iServer 10i
D:\SuperMap\iServer
```

或者在开始菜单搜索"SuperMap iServer"

### 步骤2: 启动iServer

#### 方法1: 使用开始菜单
1. 打开开始菜单
2. 搜索"SuperMap iServer"
3. 点击"启动iServer"

#### 方法2: 使用启动脚本
找到安装目录，运行：
```bash
cd "C:\Program Files\SuperMap\SuperMap iServer 11i\bin"
startup.bat
```

#### 方法3: 使用Windows服务
1. 按Win+R，输入 `services.msc`
2. 找到"SuperMap iServer"服务
3. 右键 → 启动

### 步骤3: 验证iServer启动

在浏览器访问：
```
http://localhost:8090/iserver
```

如果看到iServer管理界面，说明启动成功！

### 步骤4: 准备测试数据

#### 选项1: 使用iServer示例数据
iServer通常自带示例数据，在：
```
<iServer安装目录>/webapps/iserver/WEB-INF/data
```

#### 选项2: 创建自己的测试数据

**使用SuperMap iDesktopX**：

1. **创建工作空间**
   ```
   文件 → 新建工作空间
   保存为: D:\test_workspace.smwu
   ```

2. **创建数据源**
   ```
   右键"数据源" → 新建数据源
   类型: UDB
   名称: luonan_ds
   ```

3. **导入测试数据**
   ```
   右键数据源 → 导入数据集
   选择刚才找到的GeoJSON文件
   数据集名称: test_points
   ```

4. **创建地图**
   ```
   右键"地图" → 新建地图
   将test_points拖入地图
   ```

5. **发布到iServer**
   ```
   工具 → 发布 → 发布数据服务
   服务器地址: http://localhost:8090/iserver
   服务名称: map-luonan
   ```

---

## 🎯 方案C: 使用模拟数据测试（推荐用于快速验证）

### 创建测试数据集

在浏览器控制台运行：
```javascript
// 创建更丰富的测试数据
const testData = {
    "type": "FeatureCollection",
    "features": [
        // 测试点数据
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.15, 34.09]},
            "properties": {"name": "核桃种植点1", "yield": 120, "quality": "优"}
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.16, 34.10]},
            "properties": {"name": "核桃种植点2", "yield": 95, "quality": "良"}
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.14, 34.08]},
            "properties": {"name": "核桃种植点3", "yield": 110, "quality": "优"}
        },
        // 测试多边形数据
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [110.10, 34.05],
                    [110.20, 34.05],
                    [110.20, 34.15],
                    [110.10, 34.15],
                    [110.10, 34.05]
                ]]
            },
            "properties": {"name": "洛南县边界", "area": 2830}
        }
    ]
};

// 保存为文件
const blob = new Blob([JSON.stringify(testData, null, 2)], {type: 'application/json'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'test_data_rich.geojson';
a.click();
URL.revokeObjectURL(url);

console.log('✓ 测试数据已下载: test_data_rich.geojson');
console.log('包含:', testData.features.length, '个要素');
```

---

## 📋 测试检查清单

### 不需要iServer的测试

- [ ] 登录系统 → http://localhost:8000/login.html
- [ ] 点击"数据管理" → "导入GeoJSON"
- [ ] 上传test_data_rich.geojson
- [ ] 点击"图层管理" → 查看导入的图层
- [ ] 点击"地图服务" → 使用OSM底图

### 需要iServer的测试

- [ ] 启动iServer
- [ ] 访问 http://localhost:8090/iserver 确认运行
- [ ] 在iDesktopX中准备测试数据
- [ ] 发布数据服务到iServer
- [ ] 点击"空间分析" → "坡度分析"
- [ ] 点击"地图服务" → 切换到iServer底图

---

## 💡 推荐的测试流程

### 现在立即可做（5分钟）

1. **登录系统**
   ```
   访问: http://localhost:8000/login.html
   用户名: admin (或您的测试账号)
   密码: (您的密码)
   ```

2. **下载测试数据**
   - 运行上面的"创建测试数据集"脚本
   - 下载 test_data_rich.geojson

3. **测试数据导入**
   - 返回主页面
   - 点击"数据管理" → "导入GeoJSON"
   - 选择下载的文件
   - 等待导入成功

4. **测试图层管理**
   - 点击"图层管理"
   - 看到导入的数据
   - 切换图层显示/隐藏

### 后续完整测试（需要iServer）

1. **找到iServer安装位置**
2. **启动iServer服务**
3. **准备DEM数据**（用于地形分析）
4. **发布服务到iServer**
5. **测试空间分析功能**

---

## 🔍 快速诊断

### 检查iServer是否安装

```bash
# 在PowerShell运行
Get-Service | Where-Object {$_.DisplayName -like "*iServer*"}
```

### 检查端口占用

```bash
netstat -ano | findstr "8090"
```

如果没有输出，说明iServer未运行。

---

## 📞 需要帮助？

请告诉我：
1. ✅ 您安装了iServer吗？
2. ✅ iServer安装在哪个目录？
3. ✅ 您想先测试哪些功能？
   - 简单功能（数据导入、图层管理）
   - 完整功能（空间分析、底图切换）

我会根据您的情况提供具体的步骤！🚀

---

**文档版本**: v1.0  
**创建时间**: 2026-07-27  
**状态**: 等待用户反馈
