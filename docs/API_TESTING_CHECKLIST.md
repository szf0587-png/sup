# API测试清单 - Week 12

**测试目标**: 验证所有新增API功能的正确性和性能  
**测试时间**: 2026-07-27  
**测试环境**: 
- iServer版本: 11i / 10i
- Python版本: 3.9+
- 数据库: SQLite

---

## 📋 测试清单

### ✅ 1. 空间分析API测试

#### 1.1 地形分析

**测试用例 1.1.1: 坡度分析**
```bash
# 准备：确保有DEM数据集
curl -X POST http://localhost:8000/api/spatial-analysis/terrain/slope \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "luonan_ds",
    "dataset": "luonan_dem",
    "slope_type": "DEGREE",
    "z_factor": 1.0
  }'

# 预期结果：
# - status: "success"
# - result_id: "xxxx"
# - succeed: true
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] 返回result_id（新栅格数据集ID）
- [ ] iServer生成了坡度栅格
- [ ] 坡度值在0-90度范围内

**测试用例 1.1.2: 坡向分析**
```bash
curl -X POST http://localhost:8000/api/spatial-analysis/terrain/aspect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "luonan_ds",
    "dataset": "luonan_dem"
  }'
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] 坡向值在0-360度范围内

**测试用例 1.1.3: 山体阴影**
```bash
curl -X POST http://localhost:8000/api/spatial-analysis/terrain/hillshade \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "luonan_ds",
    "dataset": "luonan_dem",
    "azimuth": 315.0,
    "altitude": 45.0
  }'
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] 生成的晕渲图视觉效果正确

---

#### 1.2 密度分析

**测试用例 1.2.1: 核密度分析**
```bash
# 准备：确保有点数据集
curl -X POST http://localhost:8000/api/spatial-analysis/density/kernel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "luonan_ds",
    "dataset": "planting_points",
    "search_radius": 2000,
    "cell_size": 100
  }'
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] 密度值在合理范围内
- [ ] 热点区域识别正确

---

#### 1.3 栅格叠加

**测试用例 1.3.1: 加权叠加（核心功能）**
```bash
curl -X POST http://localhost:8000/api/spatial-analysis/overlay/weighted \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "luonan_ds",
    "layers": [
      {
        "dataset": "slope_reclass",
        "weight": 0.4,
        "reclass_table": []
      },
      {
        "dataset": "aspect_reclass",
        "weight": 0.3,
        "reclass_table": []
      },
      {
        "dataset": "soil_reclass",
        "weight": 0.3,
        "reclass_table": []
      }
    ]
  }'
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] 权重总和必须为1.0（验证拒绝不合法请求）
- [ ] 综合得分计算正确
- [ ] 结果栅格可视化合理

---

### ✅ 2. 地图服务API测试

**测试用例 2.1: 列出地图服务**
```bash
curl -X GET http://localhost:8000/api/map-services/list \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] 返回所有map-开头的服务
- [ ] 每个服务包含maps列表
- [ ] service_url格式正确

**测试用例 2.2: 获取瓦片配置**
```bash
curl -X GET http://localhost:8000/api/map-services/luonan/tile-config \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] tile_url可以在浏览器访问
- [ ] 瓦片图片正常显示
- [ ] bounds范围合理

**测试用例 2.3: 前端集成测试**
```javascript
// 在frontend/index.html中测试
const config = await Auth.fetch('/api/map-services/luonan/tile-config').then(r => r.json());
const tileLayer = L.tileLayer(config.tile_url, {
    attribution: config.attribution,
    maxZoom: config.max_zoom
}).addTo(map);
```

**测试检查点**:
- [ ] 瓦片加载正常
- [ ] 缩放流畅
- [ ] 替换OSM成功

---

### ✅ 3. 数据编辑API测试

**测试用例 3.1: 添加要素**
```bash
curl -X POST http://localhost:8000/api/data-editing/features/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "features": [
      {
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[110.0, 34.0], [110.1, 34.0], [110.1, 34.1], [110.0, 34.1], [110.0, 34.0]]]
        },
        "properties": {
          "name": "测试地块",
          "area": 1000.5
        }
      }
    ]
  }'
```

**测试检查点**:
- [ ] 返回状态码200
- [ ] feature_count正确
- [ ] iServer数据集中确实新增了要素

**测试用例 3.2: 更新要素**
```bash
curl -X PUT http://localhost:8000/api/data-editing/features/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "features": [...],
    "ids": [1]
  }'
```

**测试检查点**:
- [ ] 要素属性更新成功
- [ ] 几何更新成功

**测试用例 3.3: 删除要素**
```bash
curl -X DELETE http://localhost:8000/api/data-editing/features/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "ids": [1]
  }'
```

**测试检查点**:
- [ ] 要素成功删除
- [ ] 再次查询返回404

**测试用例 3.4: SQL查询**
```bash
curl -X POST http://localhost:8000/api/data-editing/features/query-by-sql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "sql_filter": "area > 1000 AND name LIKE '\''测试%'\''"
  }'
```

**测试检查点**:
- [ ] SQL过滤正确
- [ ] 返回GeoJSON格式

---

### ✅ 4. 数据管理API测试

**测试用例 4.1: 获取数据集元数据**
```bash
curl -X GET http://localhost:8000/api/data-management/datasets/user_ds/test_parcels/metadata \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] 返回字段列表
- [ ] 记录数正确
- [ ] bounds范围合理

**测试用例 4.2: 添加字段**
```bash
curl -X POST http://localhost:8000/api/data-management/fields/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "field_name": "crop_type",
    "field_type": "TEXT",
    "field_length": 50
  }'
```

**测试检查点**:
- [ ] 字段添加成功
- [ ] 元数据中包含新字段

**测试用例 4.3: 导入GeoJSON**
```bash
curl -X POST http://localhost:8000/api/data-management/import/geojson \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.geojson" \
  -F "target_datasource=user_ds" \
  -F "target_dataset=imported_data"
```

**测试检查点**:
- [ ] 上传成功
- [ ] 要素数量正确
- [ ] UDBX文件已创建

**测试用例 4.4: 导入CSV（带坐标）**
```bash
curl -X POST http://localhost:8000/api/data-management/import/csv \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@points.csv" \
  -F "lon_field=longitude" \
  -F "lat_field=latitude"
```

**测试检查点**:
- [ ] CSV解析正确
- [ ] 点要素生成正确
- [ ] 属性字段映射正确

**测试用例 4.5: 导出GeoJSON**
```bash
curl -X POST http://localhost:8000/api/data-management/export/geojson \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "datasource": "user_ds",
    "dataset": "test_parcels",
    "format": "geojson"
  }'
```

**测试检查点**:
- [ ] 导出文件完整
- [ ] GeoJSON格式正确
- [ ] 可用GIS软件打开

---

### ✅ 5. 三维服务API测试

**测试用例 5.1: 列出三维场景**
```bash
curl -X GET http://localhost:8000/api/3d-services/scenes/list \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] 返回所有3D-/realspace-服务
- [ ] terrain_available状态正确

**测试用例 5.2: 获取场景配置**
```bash
curl -X GET http://localhost:8000/api/3d-services/scenes/luonan/config \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] scene_url可访问
- [ ] terrain_url可访问
- [ ] initial_view参数合理

**测试用例 5.3: 获取地形信息**
```bash
curl -X GET http://localhost:8000/api/3d-services/terrain/luonan/info \
  -H "Authorization: Bearer $TOKEN"
```

**测试检查点**:
- [ ] 如果有.sct缓存，返回地形信息
- [ ] 如果没有，返回404并提示生成步骤

**测试用例 5.4: 上传模型**
```bash
curl -X POST http://localhost:8000/api/3d-services/models/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@model.osgb" \
  -F "model_name=test_building"
```

**测试检查点**:
- [ ] 模型文件保存成功
- [ ] 返回model_id和路径

---

## 🔍 性能测试

### 6.1 空间分析性能

**测试场景**: 1000×1000像元DEM坡度分析

**测试步骤**:
1. 记录开始时间
2. 调用坡度分析API
3. 记录结束时间
4. 计算耗时

**性能指标**:
- ✅ 优秀: < 1秒
- ⚠️ 可接受: 1-3秒
- ❌ 需优化: > 3秒

---

### 6.2 数据编辑性能

**测试场景**: 批量添加100个要素

**性能指标**:
- ✅ 优秀: < 2秒
- ⚠️ 可接受: 2-5秒
- ❌ 需优化: > 5秒

---

### 6.3 数据导入性能

**测试场景**: 导入1000个点的CSV

**性能指标**:
- ✅ 优秀: < 3秒
- ⚠️ 可接受: 3-10秒
- ❌ 需优化: > 10秒

---

## 🐛 已知问题

### Issue #1: iServer服务不可用
**现象**: API返回500，提示iServer不可达  
**原因**: iServer未启动或端口错误  
**解决**: 检查config.py中ISERVER_BASE配置

### Issue #2: 地形服务404
**现象**: 三维场景API返回404  
**原因**: 未生成.sct地形缓存  
**解决**: 按照生成指南在Desktop中生成缓存

### Issue #3: 数据编辑失败
**现象**: 添加要素返回500  
**原因**: 数据源是只读的  
**解决**: 确保UDBX数据源设置为可编辑

---

## ✅ 测试通过标准

### 功能测试
- [ ] 所有API返回正确状态码
- [ ] 所有API返回预期数据格式
- [ ] 边界条件处理正确（空数据、错误参数）
- [ ] 错误信息清晰友好

### 性能测试
- [ ] 所有分析在可接受时间内完成
- [ ] 批量操作性能合理
- [ ] 内存占用正常

### 集成测试
- [ ] 前端可以正常调用所有API
- [ ] iServer集成无问题
- [ ] 数据流转完整（导入→编辑→导出）

---

## 📊 测试结果记录

| API模块 | 测试用例数 | 通过 | 失败 | 通过率 |
|--------|----------|------|------|--------|
| 空间分析 | 8 | - | - | - |
| 地图服务 | 3 | - | - | - |
| 数据编辑 | 4 | - | - | - |
| 数据管理 | 5 | - | - | - |
| 三维服务 | 4 | - | - | - |
| **总计** | **24** | **-** | **-** | **-%** |

---

## 🚀 优化建议

### 高优先级
1. 添加请求限流（防止滥用）
2. 添加日志记录（便于调试）
3. 添加缓存机制（提升性能）

### 中优先级
1. 完善错误处理
2. 添加API文档示例
3. 添加单元测试

### 低优先级
1. 添加性能监控
2. 添加API版本管理
3. 添加Webhook通知

---

**测试负责人**: 待定  
**测试完成日期**: 待定  
**文档版本**: v1.0
