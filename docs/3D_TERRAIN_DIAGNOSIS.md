# 3D地形图层问题诊断报告

**日期**: 2026-08-03  
**问题**: map3d.html 中地形图层开关无效，无论是否勾选都没有地形起伏

---

## 🔍 诊断结果

### ✅ 数据层面：完全正常
- **地形数据存在**: `D:/supermap/data/terrain/luonan/GridToDEMCache/GridToDEMCache.sct`
- **工作空间存在**: `D:/supermap/data/WebMap/China100/China100.smwu`
- **SCT缓存结构**: 完整（包含9-14级瓦片目录）

### ❌ 服务层面：iServer未启动
- **当前状态**: `http://localhost:8090/iserver` 无响应
- **根本原因**: iServer服务未运行，无法发布3D场景

### ⚠️ 代码层面：逻辑正确但依赖缺失
- **后端逻辑**: `server/api/scene_3d.py` 的 `_terrain_data_url()` 函数正确
- **前端逻辑**: `frontend/map3d.html` 的 `createTerrainProvider()` 正确
- **问题**: 前端依赖 `config.terrain_url`，但后端无法从未启动的iServer获取场景配置

---

## 🛠️ 修复方案

### 方案A：启动iServer并发布3D场景（推荐）

#### 步骤1：启动iServer
```powershell
# 假设iServer安装在 E:\supermap-iserver-2026-windows-x64-deploy
cd E:\supermap-iserver-2026-windows-x64-deploy\bin
.\startup.bat

# 等待30秒后验证
curl http://localhost:8090/iserver/services
```

#### 步骤2：发布3D场景
需要使用iDesktop或iManager完成：

**使用iDesktop**：
1. 打开 `D:/supermap/data/WebMap/China100/China100.smwu` 工作空间
2. 创建新场景（Scene）：
   - 添加地形图层：导入 `D:/supermap/data/terrain/luonan/GridToDEMCache/GridToDEMCache.sct`
   - 设置场景名称：`luonan`
3. 发布为Realspace服务：
   - 服务名称：`3D-luonan`
   - 服务类型：Realspace 3D
   - 勾选地形缓存图层

**或使用iManager Web界面**：
1. 访问 http://localhost:8090/iserver/manager
2. 服务管理 → 发布服务 → 3D服务
3. 选择工作空间：`D:/supermap/data/WebMap/China100/China100.smwu`
4. 选择场景，设置服务名为 `3D-luonan`

#### 步骤3：验证服务
```bash
# 检查3D服务列表
curl http://localhost:8090/iserver/services | grep "3D-"

# 检查场景详情
curl http://localhost:8090/iserver/services/3D-luonan/rest/realspace.json

# 检查地形数据
curl http://localhost:8090/iserver/services/3D-luonan/rest/realspace/datas.json
```

#### 步骤4：前端验证
1. 访问 http://127.0.0.1:8000/map3d.html
2. 场景下拉框应显示 "luonan"
3. 勾选地形图层，场景应有明显起伏

---

### 方案B：使用Cesium在线地形临时替代（快速方案）

如果iServer无法立即启动，可以修改前端代码使用Cesium World Terrain：

```javascript
// frontend/map3d.html 第319-323行修改为：
async function createTerrainProvider(engine) {
    // 临时方案：使用Cesium在线地形
    if (engine === window.Cesium || !state.config?.terrain_url) {
        return engine.createWorldTerrainAsync();
    }
    
    // 原逻辑保留（当iServer可用时自动切换）
    if (engine === window.SuperMap3D && state.config?.terrain_url) {
        const provider = new engine.SuperMapTerrainProvider({
            url: state.config.terrain_url,
            isSct: true
        });
        if (provider.readyPromise) await provider.readyPromise;
        return provider;
    }
    return null;
}
```

**优缺点**：
- ✅ 优点：立即可用，无需配置iServer
- ❌ 缺点：使用全球地形，非洛南县真实地形；需要网络连接

---

## 📊 问题根源分析

### 为什么地形图层开关无效？

```
正常流程应该是：
  用户勾选地形图层
    ↓
  前端调用 toggleTerrain(visible, source)
    ↓
  设置 viewer.terrainProvider = state.terrainProvider
    ↓
  地形显示

当前实际流程：
  用户勾选地形图层
    ↓
  前端调用 toggleTerrain(visible, source)
    ↓
  state.terrainProvider === null （因为iServer未启动）
    ↓
  viewer.terrainProvider 保持为 EllipsoidTerrainProvider（平面地球）
    ↓
  无任何变化！
```

### 关键代码位置

**后端**（`server/api/scene_3d.py:431`）：
```python
"terrain_url": _terrain_data_url(service_name, scene_info_response.get("layers", []))
```
- 如果iServer未启动，`scene_info_response` 为空
- `_terrain_data_url()` 返回 `None`
- 前端收到的 `config.terrain_url` 为 `null`

**前端**（`frontend/map3d.html:319`）：
```javascript
async function createTerrainProvider(engine) {
    if (!state.config?.terrain_url || ...) return null;  // ← 这里直接返回null
    // ...
}
```

**前端**（`frontend/map3d.html:334-337`）：
```javascript
state.terrainProvider = await createTerrainProvider(engine);
if (state.terrainProvider) {
    viewer.terrainProvider = state.terrainProvider;
    state.terrainEnabled = true;
}
```
- `createTerrainProvider()` 返回 `null`
- `state.terrainProvider` 保持为 `null`
- 后续 `toggleTerrain()` 无法切换地形

---

## ✅ 推荐执行顺序

### 立即执行（今天）：
1. **启动iServer**（5分钟）
   ```powershell
   E:\supermap-iserver-2026-windows-x64-deploy\bin\startup.bat
   ```

2. **验证iServer服务**（2分钟）
   ```bash
   curl http://localhost:8090/iserver/services
   ```

### 今天下午：
3. **发布3D场景**（30-60分钟）
   - 使用iDesktop打开工作空间
   - 创建场景并添加地形
   - 发布为Realspace服务

4. **测试地形显示**（10分钟）
   - 访问 map3d.html
   - 勾选地形图层
   - 验证起伏效果

### 如果iServer无法启动：
5. **应用方案B**（临时Cesium地形，15分钟）
   - 修改 `createTerrainProvider()` 函数
   - 测试Cesium World Terrain
   - 后续iServer恢复后自动切换回SCT

---

## 📝 预期结果

### 修复后应有的表现：
1. ✅ 场景下拉框显示 "luonan" 或 "3D-luonan"
2. ✅ 状态栏显示 "含 SCT 地形"
3. ✅ 勾选地形图层后，场景有明显山地起伏
4. ✅ 取消勾选后，回到平面地球
5. ✅ 控制台无 "SCT 地形提供器加载失败" 错误

### 性能指标：
- 地形加载时间：< 3秒（本地SCT缓存）
- 帧率：> 30 FPS（1080p显示器）
- 瓦片加载：逐级加载，9级→14级

---

## 🚨 注意事项

1. **iServer端口冲突**：确保8090端口未被占用
2. **工作空间路径**：iServer配置中的路径必须与实际一致
3. **SuperMap3D引擎**：需要下载并放置到 `frontend/vendor/supermap3d/` 目录
   - 下载地址：SuperMap 资源中心（需要账号）
   - 或使用Cesium回退方案

4. **权限问题**：如果iServer无法读取 `D:/supermap/data`，检查文件夹权限

---

**诊断人**: Claude Code  
**优先级**: P0（阻塞性Bug）  
**预计修复时间**: 1-2小时（iServer启动+场景发布）  
**回退方案**: Cesium World Terrain（15分钟可用）
