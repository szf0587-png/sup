# 主界面布局优化方案

## 问题分析
当前主界面存在的问题：
1. Target Selection 模块（地名搜索）独立显示
2. 区域选取与管理 模块独立显示
3. 两个模块功能相近但分散，导致界面混乱

## 解决方案

### 方案：将两个模块收纳到可折叠的工具面板

创建一个统一的"区域工具"面板，包含：
- Target Selection（目标选择）
- 区域选取与管理

用户点击"区域工具"按钮后，弹出包含这两个子模块的面板。

---

## 实现步骤

### 步骤 1：创建工具按钮

在侧边栏或主界面合适位置添加一个"区域工具"按钮：

```html
<!-- 工具按钮 -->
<button id="region-tools-btn" class="tool-button">
    <i class="fa-solid fa-map-location-dot"></i>
    <span>区域工具</span>
</button>
```

### 步骤 2：创建统一的工具面板

```html
<!-- 区域工具面板（默认隐藏） -->
<div id="region-tools-panel" class="glass-panel tool-panel hidden">
    <!-- 面板头部 -->
    <div class="panel-header">
        <h3 class="panel-title">
            <i class="fa-solid fa-map-location-dot"></i>
            区域工具
        </h3>
        <button id="close-region-tools" class="close-btn">
            <i class="fa-solid fa-xmark"></i>
        </button>
    </div>

    <!-- 标签页导航 -->
    <div class="tabs-nav">
        <button class="tab-btn active" data-tab="target-selection">
            <i class="fa-solid fa-location-crosshairs"></i>
            目标选择
        </button>
        <button class="tab-btn" data-tab="region-management">
            <i class="fa-solid fa-map-pin"></i>
            区域管理
        </button>
    </div>

    <!-- 标签页内容 -->
    <div class="tabs-content">
        <!-- Target Selection -->
        <div id="target-selection-tab" class="tab-content active">
            <!-- 原有的 Target Selection 内容 -->
            <div class="mb-4">
                <label class="text-xs text-gray-500 block mb-1">REGION</label>
                <div class="flex items-center justify-between text-sm font-medium border-b border-gray-700 pb-2">
                    <span id="target-region-display">未选择区域</span>
                    <i class="fa-solid fa-location-crosshairs text-tech-green"></i>
                </div>
            </div>

            <div class="mb-4">
                <label class="text-xs text-gray-500 block mb-1">地名搜索</label>
                <div class="flex gap-1 items-stretch">
                    <input type="text" id="place-search-input" placeholder="输入地名" 
                           class="flex-1 bg-black/30 border border-gray-700 rounded px-2 py-1.5 text-sm">
                    <button onclick="searchPlaceByName()" class="gis-action-btn is-primary">
                        <i class="fa-solid fa-search"></i>
                    </button>
                </div>
            </div>

            <div class="mb-4">
                <label class="text-xs text-gray-500 block mb-1">经纬度</label>
                <div class="grid grid-cols-2 gap-2">
                    <input type="number" id="target-lat-input" placeholder="纬度" step="0.01"
                           class="bg-black/30 border border-gray-700 rounded px-2 py-1.5 text-sm">
                    <input type="number" id="target-lon-input" placeholder="经度" step="0.01"
                           class="bg-black/30 border border-gray-700 rounded px-2 py-1.5 text-sm">
                </div>
                <button onclick="applyCoordInput()" class="gis-action-btn is-primary w-full mt-2">
                    <i class="fa-solid fa-map-pin"></i>
                    <span>定位</span>
                </button>
            </div>
        </div>

        <!-- 区域选取与管理 -->
        <div id="region-management-tab" class="tab-content hidden">
            <!-- 原有的区域选取与管理内容 -->
            <div class="mb-4">
                <div class="text-gray-400 text-xs mb-1">当前选中区域</div>
                <div id="scan-selected-region-label" class="text-lg font-bold">未选取</div>
                <div id="scan-selected-region-coord" class="text-right text-xs text-tech-green mt-1 font-mono">
                    请点击"启用地图选区"后在地图单击
                </div>
            </div>

            <div class="mb-4">
                <label class="text-xs text-gray-400 block mb-1">区域名称</label>
                <input type="text" id="scan-region-name-input" placeholder="例如：陕西自定义区1" 
                       class="w-full bg-black/30 border border-gray-700 rounded-lg px-3 py-2 text-sm">
            </div>

            <div class="gis-action-row">
                <button onclick="saveScanRegion()" class="gis-action-btn is-save">
                    <i class="fa-solid fa-floppy-disk"></i><span>保存</span>
                </button>
                <button onclick="clearScanSelectedRegion()" class="gis-action-btn is-danger">
                    <i class="fa-solid fa-xmark"></i><span>取消</span>
                </button>
                <button onclick="enableRegionSelection()" class="gis-action-btn">
                    <i class="fa-solid fa-map-pin"></i><span>重选</span>
                </button>
                <button onclick="applySelectedRegionToAnalysis()" class="gis-action-btn is-primary">
                    <i class="fa-solid fa-arrow-right"></i><span>分析</span>
                </button>
            </div>

            <!-- 已保存区域列表 -->
            <div class="mt-4">
                <h4 class="text-xs text-gray-400 uppercase tracking-widest mb-2">已保存的区域</h4>
                <div id="scan-regions-container" class="space-y-2 max-h-80 overflow-y-auto">
                    <div class="text-xs text-gray-500 text-center py-6">
                        <i class="fa-solid fa-inbox block mb-2 text-lg opacity-50"></i>
                        暂无保存的区域
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 步骤 3：添加样式

```css
/* 工具按钮 */
.tool-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: #e2e8f0;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 150ms ease-out;
}

.tool-button:hover {
    background: rgba(30, 41, 59, 1);
    border-color: rgba(34, 197, 94, 0.5);
    transform: translateY(-1px);
}

/* 工具面板 */
.tool-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.tool-panel.hidden {
    display: none;
}

/* 面板头部 */
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: linear-gradient(to right, rgba(34, 197, 94, 0.1), transparent);
}

.panel-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.125rem;
    font-weight: 600;
    color: #f8fafc;
}

.close-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    border-radius: 0.375rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 150ms ease-out;
}

.close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #f8fafc;
}

/* 标签页导航 */
.tabs-nav {
    display: flex;
    padding: 0 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
}

.tab-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.875rem 1.25rem;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease-out;
}

.tab-btn:hover {
    color: #e2e8f0;
}

.tab-btn.active {
    color: #22c55e;
    border-bottom-color: #22c55e;
}

/* 标签页内容 */
.tabs-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* 遮罩层 */
.tool-panel-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 999;
}

.tool-panel-backdrop.hidden {
    display: none;
}
```

### 步骤 4：添加 JavaScript 交互

```javascript
// 区域工具面板控制
const RegionTools = {
    panel: null,
    backdrop: null,
    
    init() {
        this.panel = document.getElementById('region-tools-panel');
        this.backdrop = document.getElementById('region-tools-backdrop');
        
        // 打开按钮
        document.getElementById('region-tools-btn').addEventListener('click', () => {
            this.open();
        });
        
        // 关闭按钮
        document.getElementById('close-region-tools').addEventListener('click', () => {
            this.close();
        });
        
        // 点击遮罩层关闭
        this.backdrop.addEventListener('click', () => {
            this.close();
        });
        
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
    },
    
    open() {
        this.panel.classList.remove('hidden');
        this.backdrop.classList.remove('hidden');
    },
    
    close() {
        this.panel.classList.add('hidden');
        this.backdrop.classList.add('hidden');
    },
    
    switchTab(tabId) {
        // 更新按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
            }
        });
        
        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.classList.add('hidden');
        });
        
        const targetContent = document.getElementById(tabId + '-tab');
        if (targetContent) {
            targetContent.classList.remove('hidden');
            targetContent.classList.add('active');
        }
    }
};

// 初始化
window.addEventListener('DOMContentLoaded', () => {
    RegionTools.init();
});
```

---

## 布局示意

```
┌─────────────────────────────────────────┐
│  ┌─ 区域工具 ─────────────────────┐ ×  │
│  │                                      │
│  │  [目标选择] [区域管理]              │
│  │  ─────────  ───────────              │
│  │                                      │
│  │  REGION: 未选择区域                 │
│  │                                      │
│  │  地名搜索: [输入框] [搜索]         │
│  │                                      │
│  │  经纬度:                            │
│  │  [纬度] [经度]                      │
│  │  [定位]                              │
│  │                                      │
│  └──────────────────────────────────────┘
└─────────────────────────────────────────┘
```

---

## 优点

1. **界面更整洁**: 减少主界面的视觉混乱
2. **逻辑清晰**: 相关功能集中在一起
3. **按需显示**: 只在需要时打开工具面板
4. **易于扩展**: 未来可以添加更多工具标签页
5. **用户友好**: 清晰的标签页导航

---

## 实施建议

1. 先创建新的工具面板结构
2. 将原有的两个模块内容迁移到标签页中
3. 隐藏原有的独立模块
4. 测试功能是否正常
5. 如果一切正常，删除原有模块代码

---

## 需要修改的文件

- `frontend/index.html` - 添加工具面板 HTML
- `frontend/workspace.css` - 添加样式
- `frontend/workspace.js` - 添加交互逻辑

---

是否需要我帮您实现这个方案？
