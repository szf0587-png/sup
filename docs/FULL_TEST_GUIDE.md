# 🚀 完整测试指南 - iServer已安装版

**账号信息**: admin / admin123  
**iServer路径**: E:\supermap-iserver-2026-windows-x64-deploy  
**状态**: iServer正在启动...

---

## ✅ 第1步：等待iServer启动（1-2分钟）

iServer正在启动，请等待1-2分钟后访问：
```
http://localhost:8090/iserver
```

**如何确认启动成功**：
- 看到iServer管理界面
- 或者运行这个检查命令：
```bash
curl http://localhost:8090/iserver
```

---

## ✅ 第2步：登录系统

访问：
```
http://localhost:8000/login.html
```

输入：
- 用户名：`admin`
- 密码：`admin123`

登录成功后会跳转到主页面。

---

## ✅ 第3步：测试新功能

### 测试地图服务

1. **点击左侧"地图服务"按钮**
2. 右侧面板弹出
3. 应该看到底图列表（包含iServer底图）
4. 点击任意底图切换

### 测试数据管理

1. **下载测试数据**（在控制台运行）：
```javascript
const testData = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.15, 34.09]},
            "properties": {"name": "核桃种植点1", "yield": 120}
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.16, 34.10]},
            "properties": {"name": "核桃种植点2", "yield": 95}
        }
    ]
};
const blob = new Blob([JSON.stringify(testData, null, 2)], {type: 'application/json'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'test_points.geojson';
a.click();
URL.revokeObjectURL(url);
console.log('✓ 测试数据已下载');
```

2. **点击左侧"数据管理"按钮**
3. 点击"导入GeoJSON"
4. 选择刚下载的文件
5. 数据源：`test_ds`
6. 数据集：`test_points`
7. 确认导入

### 测试图层管理

1. **点击左侧"图层管理"按钮**
2. 应该看到刚导入的数据
3. 点击复选框切换显示/隐藏
4. 点击"缩放到图层"

### 测试空间分析（需要准备DEM数据）

1. **点击左侧"空间分析"按钮**
2. 看到8种分析工具
3. 点击"坡度分析"
4. 看到参数配置表单

---

## ✅ 第4步：在iServer中准备测试数据（可选）

如果您有SuperMap iDesktopX，可以准备真实数据用于空间分析：

### 准备DEM数据

1. 打开iDesktopX
2. 创建工作空间
3. 导入DEM数据（或使用示例数据）
4. 发布数据服务到iServer：
   - 服务地址：`http://localhost:8090/iserver`
   - 数据源名称：`luonan_ds`
   - 数据集名称：`luonan_dem`

---

## 📋 完整测试检查清单

### 登录测试
- [ ] 访问 http://localhost:8000/login.html
- [ ] 输入 admin / admin123
- [ ] 登录成功

### iServer测试
- [ ] 访问 http://localhost:8090/iserver
- [ ] 看到iServer管理界面

### 新功能测试
- [ ] 地图服务 - 看到底图列表
- [ ] 数据管理 - 导入GeoJSON成功
- [ ] 图层管理 - 看到图层列表
- [ ] 空间分析 - 看到8种工具

### 原功能测试
- [ ] 天眼扫描 - 正常工作
- [ ] 适宜性分析 - 正常工作
- [ ] 区域工具 - 正常工作

---

## 🎯 立即开始

### 现在就做这3件事：

1. **等待1分钟**让iServer启动
2. **访问** http://localhost:8000/login.html **登录**
3. **点击"数据管理"**测试第一个功能

---

## 📞 遇到问题？

### iServer无法访问

检查端口：
```bash
netstat -ano | findstr "8090"
```

如果没有输出，手动启动：
```bash
cd E:\supermap-iserver-2026-windows-x64-deploy\bin
startup.bat
```

### 登录失败

在控制台检查：
```javascript
console.log('Token:', localStorage.getItem('access_token'));
```

### API调用失败

查看控制台错误信息，并告诉我详细内容。

---

## 🎉 预期结果

如果一切正常，您应该：
- ✅ 成功登录系统
- ✅ 看到新增的5个按钮
- ✅ 点击按钮，右侧弹出面板
- ✅ 成功导入测试数据
- ✅ 在图层管理中看到数据
- ✅ 切换底图成功
- ✅ 原有功能不受影响

---

**现在请：**
1. 等待1分钟
2. 访问 http://localhost:8090/iserver 确认iServer启动
3. 访问 http://localhost:8000/login.html 登录
4. 告诉我结果！

🚀 准备好了吗？开始测试吧！
