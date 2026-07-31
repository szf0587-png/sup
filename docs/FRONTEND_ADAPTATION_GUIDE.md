# 任务 #13：前端适配完成指南

## ✅ 已完成的工作

### 1. 设计系统文档 ✅
**文件**: `docs/DESIGN_SYSTEM.md`

**内容**:
- 完整的色彩系统（主色、次要色、中性色、语义色）
- 字体系统（字体家族、字号、字重、行高）
- 间距系统（基于 4px 标尺）
- 圆角、阴影、动画系统
- Z-Index 层级管理
- 组件设计规范
- 响应式断点
- 可访问性规范

### 2. 登录页面 ✅
**文件**: `frontend/login.html`

**特性**:
- ✅ 现代化设计（毛玻璃效果、动态背景）
- ✅ 表单验证
- ✅ 错误提示
- ✅ 记住我功能
- ✅ 加载状态
- ✅ 响应式设计
- ✅ 完整的 API 集成

**API 调用**:
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 验证 token

### 3. 认证工具模块 ✅
**文件**: `frontend/auth.js`

**功能**:
- `getToken()` - 获取存储的 token
- `setToken()` - 保存 token
- `clearToken()` - 清除 token
- `getCurrentUser()` - 获取当前用户信息
- `logout()` - 登出
- `checkAuth()` - 检查登录状态
- `fetch()` - 创建带认证头的请求

### 4. 顶部导航栏组件 ✅
**文件**: `frontend/navbar.js`

**功能**:
- ✅ Logo 展示
- ✅ 项目切换下拉菜单
- ✅ 用户信息显示
- ✅ 用户下拉菜单（个人中心、设置、退出登录）
- ✅ 创建项目功能
- ✅ 激活项目功能
- ✅ 响应式设计

**API 调用**:
- `GET /api/auth/me` - 获取用户信息
- `GET /api/projects` - 获取项目列表
- `POST /api/projects/{id}/activate` - 激活项目
- `POST /api/projects` - 创建项目

---

## 📋 需要完成的工作

### 步骤 1：更新主页面（index.html）

**需要修改的内容**:

1. **在 `<head>` 中添加认证和导航栏脚本**:
```html
<!-- 在现有脚本之前添加 -->
<script src="auth.js"></script>
<script src="navbar.js"></script>
```

2. **在页面加载时初始化认证和导航栏**:
```html
<script>
// 在 DOMContentLoaded 事件中添加
document.addEventListener('DOMContentLoaded', async () => {
    // 检查登录状态
    await Auth.checkAuth();
    
    // 初始化顶部导航栏
    await TopNavbar.init();
    
    // 调整页面布局（为导航栏留出空间）
    document.body.style.paddingTop = '64px';
    
    // 原有的初始化代码...
});
</script>
```

3. **更新所有 API 调用为带认证的请求**:

将现有的 `fetch()` 调用改为使用 `Auth.fetch()`:

```javascript
// 之前：
const response = await fetch('/api/golden-standards');

// 之后：
const response = await Auth.fetch('http://localhost:8000/api/golden-standards');
```

### 步骤 2：更新金标准相关 JS（golden_standard.js）

**需要修改的地方**:

1. **列出金标准**:
```javascript
async function loadGoldenStandards() {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/golden-standards`);
        const data = await response.json();
        
        // 渲染金标准列表
        renderGoldenStandards(data.standards);
    } catch (error) {
        console.error('加载金标准失败:', error);
    }
}
```

2. **创建金标准**:
```javascript
async function createGoldenStandard(formData) {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/golden-standards`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('金标准创建成功！');
            await loadGoldenStandards();
        }
    } catch (error) {
        console.error('创建金标准失败:', error);
        alert('创建失败');
    }
}
```

3. **删除金标准**:
```javascript
async function deleteGoldenStandard(standardId) {
    if (!confirm('确定要删除这个金标准吗？')) return;
    
    try {
        const response = await Auth.fetch(`${API_BASE}/api/golden-standards/${standardId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('删除成功！');
            await loadGoldenStandards();
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}
```

### 步骤 3：更新物候匹配、区域筛选、地块精评等功能

**通用模式**:

所有 API 调用都需要：
1. 使用 `Auth.fetch()` 替代 `fetch()`
2. 使用完整的 API URL（`http://localhost:8000/api/...`）
3. 添加错误处理（401 会自动跳转到登录页）

**示例**:

```javascript
// 物候匹配
async function performPhenologyMatch(lat, lon, standardId) {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/phenology/match`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat,
                lon,
                golden_standard_id: standardId,
                top_n: 5
            })
        });
        
        const data = await response.json();
        // 处理返回数据...
    } catch (error) {
        console.error('物候匹配失败:', error);
    }
}

// 区域筛选
async function performScreening(standardId, county, topN) {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/screening/runs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                golden_standard_id: standardId,
                county,
                top_n: topN
            })
        });
        
        const data = await response.json();
        // 处理返回数据...
    } catch (error) {
        console.error('区域筛选失败:', error);
    }
}

// 地块精评
async function evaluateParcel(townCode, parcelGeojson, standardId) {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/parcels/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                town_code: townCode,
                parcel_geojson: parcelGeojson,
                golden_standard_id: standardId
            })
        });
        
        const data = await response.json();
        // 处理返回数据...
    } catch (error) {
        console.error('地块精评失败:', error);
    }
}
```

### 步骤 4：添加数据集上传功能

**创建数据集上传面板**:

```javascript
async function uploadDataset(file, name, description) {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);
    
    try {
        const response = await Auth.fetch(`${API_BASE}/api/datasets/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('数据集上传成功！');
            console.log('数据集信息:', data);
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败');
    }
}

// 列出数据集
async function loadDatasets() {
    try {
        const response = await Auth.fetch(`${API_BASE}/api/datasets`);
        const data = await response.json();
        
        // 渲染数据集列表
        console.log('我的数据集:', data.datasets);
    } catch (error) {
        console.error('加载数据集失败:', error);
    }
}
```

### 步骤 5：项目关联数据集功能

**添加数据集到当前项目**:

```javascript
async function addDatasetToCurrentProject(datasetId) {
    const currentProject = TopNavbar.currentProject;
    if (!currentProject) {
        alert('请先选择一个项目');
        return;
    }
    
    try {
        const response = await Auth.fetch(
            `${API_BASE}/api/projects/${currentProject.id}/datasets`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ dataset_id: datasetId })
            }
        );
        
        if (response.ok) {
            alert('数据集已添加到项目');
        }
    } catch (error) {
        console.error('添加数据集到项目失败:', error);
    }
}
```

---

## 🎨 样式统一指南

### 1. 使用设计系统的 CSS 变量

在 `workspace.css` 或主样式文件中定义 CSS 变量：

```css
:root {
    /* 主色调 */
    --primary-500: #22c55e;
    --primary-600: #16a34a;
    --primary-700: #15803d;
    
    /* 次要色 */
    --secondary-500: #3b82f6;
    --secondary-600: #2563eb;
    
    /* 背景色 */
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    
    /* 文字颜色 */
    --text-primary: #f8fafc;
    --text-secondary: #e2e8f0;
    --text-tertiary: #cbd5e1;
    --text-muted: #94a3b8;
    
    /* 间距 */
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    
    /* 圆角 */
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    
    /* 阴影 */
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

### 2. 统一卡片样式

```css
.card {
    background: rgba(30, 41, 59, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    box-shadow: var(--shadow-md);
}
```

### 3. 统一按钮样式

```css
.btn-primary {
    background: var(--primary-600);
    color: white;
    padding: var(--space-3) var(--space-6);
    border-radius: var(--radius-md);
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease-out;
}

.btn-primary:hover {
    background: var(--primary-700);
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
}
```

### 4. 统一输入框样式

```css
.input {
    width: 100%;
    padding: var(--space-3) var(--space-4);
    background: var(--bg-secondary);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 1rem;
}

.input:focus {
    outline: none;
    border-color: var(--primary-500);
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.5);
}
```

---

## 🧪 测试清单

完成适配后，请测试以下功能：

### 认证流程
- [ ] 未登录时自动跳转到登录页
- [ ] 登录成功后跳转到主页
- [ ] 记住我功能正常工作
- [ ] Token 过期后自动跳转到登录页
- [ ] 退出登录功能正常

### 导航栏
- [ ] 用户信息正确显示
- [ ] 项目下拉菜单正常工作
- [ ] 项目切换功能正常
- [ ] 创建项目功能正常
- [ ] 退出登录功能正常

### 业务功能
- [ ] 金标准列表加载正常
- [ ] 创建金标准功能正常
- [ ] 物候匹配功能正常
- [ ] 区域筛选功能正常
- [ ] 地块精评功能正常
- [ ] 报告生成功能正常

### 数据管理
- [ ] 数据集上传功能正常
- [ ] 数据集列表加载正常
- [ ] 数据集关联到项目功能正常

### 样式一致性
- [ ] 所有卡片使用统一样式
- [ ] 所有按钮使用统一样式
- [ ] 所有输入框使用统一样式
- [ ] 色彩方案一致
- [ ] 响应式设计正常

---

## 📁 文件清单

### 新增文件
- ✅ `frontend/login.html` - 登录页面
- ✅ `frontend/auth.js` - 认证工具模块
- ✅ `frontend/navbar.js` - 顶部导航栏组件
- ✅ `docs/DESIGN_SYSTEM.md` - 设计系统文档

### 需要修改的文件
- ⏳ `frontend/index.html` - 添加认证和导航栏
- ⏳ `frontend/golden_standard.js` - 更新 API 调用
- ⏳ `frontend/workspace.js` - 更新 API 调用
- ⏳ `frontend/workspace.css` - 添加 CSS 变量和统一样式

---

## 🎯 下一步行动

1. **立即测试登录页面**:
   ```bash
   # 确保服务器运行
   python server/main.py
   
   # 访问登录页面
   http://localhost:8000/login.html
   ```

2. **修改主页面（index.html）**:
   - 添加认证和导航栏脚本
   - 添加初始化代码
   - 调整页面布局

3. **更新所有 JS 文件的 API 调用**:
   - 使用 `Auth.fetch()` 替代 `fetch()`
   - 添加错误处理

4. **统一样式**:
   - 添加 CSS 变量到 `workspace.css`
   - 更新组件样式

5. **测试完整流程**:
   - 登录 → 创建项目 → 上传数据 → 创建金标准 → 分析

---

## 💡 提示

- 所有修改都是增量的，不会破坏现有功能
- 可以先在开发分支测试
- 建议先完成主页面的认证集成，再逐个功能模块更新
- 遇到问题可以查看浏览器控制台的错误信息

准备好开始适配主页面了吗？
