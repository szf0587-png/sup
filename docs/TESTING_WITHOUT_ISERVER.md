# 🎯 无需iServer的功能测试方案

## 📊 当前情况

- ✅ **后端运行正常** - http://localhost:8000
- ✅ **找到测试数据** - GeoJSON文件
- ❌ **iServer未安装** - 无法测试空间分析
- ⚠️ **Leaflet.Draw加载失败** - 绘制工具暂时不可用
- ⚠️ **需要登录** - 401错误

---

## 🚀 立即可测试的功能（不需要iServer）

### 1. 登录系统 ⭐

**步骤**：
1. 访问：http://localhost:8000/login.html
2. 输入用户名和密码
3. 登录成功后返回主页面

**默认测试账号**（如果有）：
- 用户名：`admin` 或 `test`
- 密码：（请尝试常用测试密码）

如果没有账号，告诉我，我可以帮您创建。

---

### 2. 测试数据导入/导出

#### 步骤1: 准备测试数据

在浏览器控制台运行这个脚本，下载测试文件：

```javascript
// 创建测试GeoJSON数据
const testData = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [110.15, 34.09]
            },
            "properties": {
                "name": "核桃种植点1",
                "yield": 120,
                "quality": "优",
                "planted_date": "2023-03-15"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [110.16, 34.10]
            },
            "properties": {
                "name": "核桃种植点2",
                "yield": 95,
                "quality": "良",
                "planted_date": "2023-03-20"
            }
        },
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
            "properties": {
                "name": "洛南县测试区域",
                "area": 100,
                "type": "种植区"
            }
        }
    ]
};

// 下载为文件
const blob = new Blob([JSON.stringify(testData, null, 2)], {type: 'application/json'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'test_luonan.geojson';
a.click();
URL.revokeObjectURL(url);

console.log('✓ 测试数据已下载: test_luonan.geojson');
console.log('包含:', testData.features.length, '个要素');
console.log('- 2个点要素（核桃种植点）');
console.log('- 1个多边形要素（测试区域）');
```

#### 步骤2: 测试导入

1. 登录后，点击左侧"数据管理"
2. 点击"导入GeoJSON"
3. 选择刚才下载的 `test_luonan.geojson`
4. 数据源名称：`test_ds`
5. 数据集名称：`luonan_test`
6. 点击确认

**预期结果**：
```
✓ 成功导入 3 个要素到 luonan_test
```

#### 步骤3: 测试导出

1. 点击左侧"数据管理"
2. 点击"导出GeoJSON"
3. 数据源：`test_ds`
4. 数据集：`luonan_test`
5. 点击确认

**预期结果**：
下载包含3个要素的GeoJSON文件

---

### 3. 测试图层管理

#### 测试显示/隐藏图层

1. 导入数据后，点击左侧"图层管理"
2. 看到已导入的图层列表
3. 点击复选框切换图层显示/隐藏
4. 点击"缩放到图层"按钮

**预期结果**：
- 图层在地图上显示/隐藏
- 地图缩放到图层范围

---

### 4. 测试地图服务（OSM底图）

1. 点击左侧"地图服务"
2. 看到底图列表（包含OSM底图）
3. 点击OSM底图

**预期结果**：
地图切换到OpenStreetMap底图

---

### 5. 测试原有功能（确保不受影响）

- [ ] 点击"天眼扫描" - 原功能应正常
- [ ] 点击"适宜性分析" - 原功能应正常
- [ ] 点击"区域工具" - 原功能应正常

---

## 📋 完整测试清单

### 准备工作
- [ ] 后端运行 - http://localhost:8000
- [ ] 浏览器打开 - http://localhost:8000/index.html
- [ ] 下载测试数据 - test_luonan.geojson

### 基础功能测试
- [ ] 登录系统
- [ ] 导入GeoJSON数据
- [ ] 查看图层列表
- [ ] 切换图层显示/隐藏
- [ ] 导出GeoJSON数据
- [ ] 切换OSM底图

### 新旧功能共存测试
- [ ] 新功能：点击"数据管理"
- [ ] 新功能：点击"图层管理"
- [ ] 新功能：点击"地图服务"
- [ ] 原功能：点击"天眼扫描"
- [ ] 原功能：点击"区域工具"

---

## 🎯 测试结果记录

### 预期输出

#### 成功的测试
```
✓ 登录成功
✓ 数据导入成功 - 3个要素
✓ 图层显示正常
✓ 图层管理面板正常
✓ OSM底图切换成功
✓ 原有功能不受影响
```

#### 已知问题
```
⚠️ 绘制工具不可用 - Leaflet.Draw未加载
⚠️ 空间分析不可用 - 需要iServer
⚠️ iServer底图不可用 - iServer未安装
```

---

## 💡 现在开始测试

### 第一步：登录（最重要）

请告诉我：
1. 您有测试账号吗？
2. 用户名和密码是什么？
3. 或者需要我帮您创建一个测试账号？

### 第二步：下载测试数据

1. 打开 http://localhost:8000/index.html
2. 按F12打开控制台
3. 粘贴上面的"创建测试GeoJSON数据"脚本
4. 按回车，下载文件

### 第三步：测试导入

登录后：
1. 点击左侧"数据管理"
2. 点击"导入GeoJSON"
3. 选择文件
4. 等待成功提示

---

## 📞 需要帮助

请告诉我：
1. ✅ 您能登录吗？或需要创建账号？
2. ✅ 测试数据下载成功了吗？
3. ✅ 想先测试哪个功能？
4. ✅ 控制台有什么错误？

根据您的反馈，我会继续指导测试！🚀

---

## 🎊 总结

### 可以测试的功能（无需iServer）
- ✅ 数据导入/导出
- ✅ 图层管理
- ✅ OSM底图
- ✅ 数据查看

### 需要iServer的功能（暂时跳过）
- ⏸️ 空间分析
- ⏸️ iServer底图切换
- ⏸️ 地形分析

### 需要修复的功能
- 🔧 绘制工具（Leaflet.Draw加载问题）

现在最重要的是**先登录系统**，然后我们就可以测试数据导入和图层管理了！
