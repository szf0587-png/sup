# 🚀 快速修复脚本

复制以下代码到浏览器控制台（F12），立即修复问题：

## 修复1: 检查并初始化DrawTools

```javascript
// 检查当前状态
console.log('=== 系统状态检查 ===');
console.log('地图实例:', window.mainMap ? '✓' : '✗');
console.log('MapManager:', window.MapManager ? '✓' : '✗');
console.log('DrawTools:', window.DrawTools ? '✓' : '✗');
console.log('LayerManager:', window.LayerManager ? '✓' : '✗');
console.log('AnalysisTools:', window.AnalysisTools ? '✓' : '✗');
console.log('DataManager:', window.DataManager ? '✓' : '✗');
console.log('Token:', localStorage.getItem('access_token') ? '✓ 已登录' : '✗ 未登录');

// 如果DrawTools未初始化，手动初始化
if (!window.DrawTools && window.mainMap) {
    console.log('正在初始化DrawTools...');
    window.DrawTools = new DrawTools(window.mainMap);
    window.DrawTools.init();
    console.log('✓ DrawTools初始化完成');
}

// 如果其他管理器未初始化
if (!window.MapManager && window.mainMap) {
    console.log('正在初始化MapManager...');
    window.MapManager = new MapManager(window.mainMap);
    window.MapManager.init();
    console.log('✓ MapManager初始化完成');
}

if (!window.LayerManager && window.mainMap) {
    console.log('正在初始化LayerManager...');
    window.LayerManager = new LayerManager(window.mainMap);
    window.LayerManager.init();
    console.log('✓ LayerManager初始化完成');
}

console.log('=== 修复完成 ===');
console.log('现在可以点击"绘制编辑"按钮测试');
```

## 修复2: 测试绘制功能

```javascript
// 测试绘制多边形
console.log('激活绘制工具...');
window.DrawTools?.drawPolygon();
console.log('✓ 请在地图上点击绘制多边形');
console.log('提示: 双击完成绘制');
```

## 修复3: 测试API（需要先登录）

```javascript
// 检查认证
const token = localStorage.getItem('access_token');
if (!token) {
    console.warn('⚠️ 未登录！请先访问: http://localhost:8000/login.html');
} else {
    console.log('✓ 已登录，Token存在');
    
    // 测试地图服务API
    console.log('测试地图服务API...');
    fetch('http://localhost:8000/api/map-services/recommendations/basemaps', {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(r => {
        console.log('API状态:', r.status);
        return r.json();
    })
    .then(data => {
        console.log('✓ API响应:', data);
    })
    .catch(err => {
        console.error('✗ API错误:', err);
    });
}
```

## 修复4: 手动加载底图列表

```javascript
// 如果地图服务面板打开但底图列表为空
async function loadBasemaps() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('未登录，无法加载底图');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/map-services/recommendations/basemaps', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        console.log('底图列表:', data);
        
        // 尝试切换到第一个底图
        if (data.basemaps && data.basemaps.length > 0) {
            const firstBasemap = data.basemaps[0];
            console.log('尝试切换到:', firstBasemap.name);
            await window.MapManager?.changeBasemap(firstBasemap.id);
        }
    } catch (error) {
        console.error('加载底图失败:', error);
    }
}

// 运行
loadBasemaps();
```

## 一键修复（推荐）

```javascript
// 复制这个完整脚本，一次性修复所有问题
(async function quickFix() {
    console.log('🔧 开始快速修复...');
    
    // 1. 检查状态
    console.log('\n=== 1. 检查系统状态 ===');
    const checks = {
        '地图': !!window.mainMap,
        'MapManager': !!window.MapManager,
        'DrawTools': !!window.DrawTools,
        'LayerManager': !!window.LayerManager,
        'AnalysisTools': !!window.AnalysisTools,
        'DataManager': !!window.DataManager,
        'Token': !!localStorage.getItem('access_token')
    };
    
    for (const [key, value] of Object.entries(checks)) {
        console.log(`${value ? '✓' : '✗'} ${key}`);
    }
    
    // 2. 初始化缺失的管理器
    console.log('\n=== 2. 初始化管理器 ===');
    if (!window.DrawTools && window.mainMap) {
        window.DrawTools = new DrawTools(window.mainMap);
        window.DrawTools.init();
        console.log('✓ DrawTools已初始化');
    }
    
    if (!window.MapManager && window.mainMap) {
        window.MapManager = new MapManager(window.mainMap);
        await window.MapManager.init();
        console.log('✓ MapManager已初始化');
    }
    
    if (!window.LayerManager && window.mainMap) {
        window.LayerManager = new LayerManager(window.mainMap);
        await window.LayerManager.init();
        console.log('✓ LayerManager已初始化');
    }
    
    // 3. 测试绘制工具
    console.log('\n=== 3. 测试绘制工具 ===');
    if (window.DrawTools) {
        console.log('✓ 绘制工具可用');
        console.log('运行: window.DrawTools.drawPolygon() 来测试');
    } else {
        console.error('✗ 绘制工具不可用');
    }
    
    // 4. 测试API
    console.log('\n=== 4. 测试API连接 ===');
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.warn('⚠️  未登录！');
        console.log('请访问: http://localhost:8000/login.html');
    } else {
        try {
            const response = await fetch('http://localhost:8000/api/map-services/recommendations/basemaps', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`✓ API可用，找到 ${data.basemaps?.length || 0} 个底图`);
            } else {
                console.error(`✗ API返回错误: ${response.status}`);
            }
        } catch (error) {
            console.error('✗ API连接失败:', error.message);
        }
    }
    
    console.log('\n🎉 修复完成！');
    console.log('\n📝 下一步:');
    console.log('1. 如果未登录，访问: http://localhost:8000/login.html');
    console.log('2. 点击左侧"绘制编辑"按钮');
    console.log('3. 点击"绘制多边形"');
    console.log('4. 在地图上点击绘制');
})();
```

---

## 使用方法

1. **打开页面**: http://localhost:8000/index.html
2. **按F12打开控制台**
3. **复制上面的"一键修复"脚本**
4. **粘贴到控制台并回车**
5. **查看输出结果**

---

## 预期结果

如果一切正常，您应该看到：
```
🔧 开始快速修复...

=== 1. 检查系统状态 ===
✓ 地图
✓ MapManager
✓ DrawTools
✓ LayerManager
✓ AnalysisTools
✓ DataManager
✓ Token

=== 2. 初始化管理器 ===
(都已初始化，无需修复)

=== 3. 测试绘制工具 ===
✓ 绘制工具可用
运行: window.DrawTools.drawPolygon() 来测试

=== 4. 测试API连接 ===
✓ API可用，找到 2 个底图

🎉 修复完成！
```

---

## 如果还有问题

请将控制台的**完整输出**发给我，包括：
1. 系统状态检查结果
2. 任何红色错误信息
3. API测试结果

我会根据具体错误继续修复！
