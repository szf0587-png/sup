/**
 * 右侧动态面板组件
 * 支持多个面板切换显示，可调整宽度
 */

class RightPanel {
    constructor() {
        this.currentPanel = null;
        this.isVisible = false;
        this.width = 420; // 默认宽度
        this.minWidth = 320;
        this.maxWidth = 800;
    }

    render() {
        const html = `
            <div id="right-panel" class="fixed top-16 bottom-8 right-0 bg-slate-900/95 border-l border-slate-700/50
                        backdrop-blur-sm z-30 transform translate-x-full transition-transform duration-300
                        overflow-hidden flex flex-col"
                 style="width: ${this.width}px;">

                <!-- 面板头部 -->
                <div class="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
                    <h3 id="panel-title" class="text-slate-200 font-medium text-lg"></h3>
                    <button id="close-panel" class="p-1.5 hover:bg-slate-700/50 rounded-lg transition-colors cursor-pointer">
                        <i class="fas fa-times text-slate-400"></i>
                    </button>
                </div>

                <!-- 面板内容区域 -->
                <div id="panel-content" class="flex-1 overflow-y-auto overflow-x-hidden p-4">
                    <!-- 动态内容将在这里加载 -->
                </div>

                <!-- 宽度调整手柄 -->
                <div id="resize-handle" class="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize
                            hover:bg-green-500/50 transition-colors"></div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);
        this.bindEvents();
    }

    bindEvents() {
        // 关闭按钮
        document.getElementById('close-panel')?.addEventListener('click', () => {
            this.hidePanel();
        });

        // 宽度调整
        const handle = document.getElementById('resize-handle');
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        handle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = this.width;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const diff = startX - e.clientX;
            const newWidth = Math.max(this.minWidth, Math.min(this.maxWidth, startWidth + diff));
            this.width = newWidth;

            const panel = document.getElementById('right-panel');
            panel.style.width = `${newWidth}px`;
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    showPanel(panelId, title) {
        this.currentPanel = panelId;
        this.isVisible = true;

        const panel = document.getElementById('right-panel');
        const titleElement = document.getElementById('panel-title');
        const contentElement = document.getElementById('panel-content');

        // 显示面板
        panel.classList.remove('translate-x-full');

        // 设置标题
        titleElement.textContent = title || this.getPanelTitle(panelId);

        // 加载内容
        contentElement.innerHTML = '<div class="flex items-center justify-center py-8"><div class="spinner"></div></div>';

        // 异步加载面板内容
        this.loadPanelContent(panelId, contentElement);

        // 触发面板显示事件
        window.dispatchEvent(new CustomEvent('panelShown', {
            detail: { panel: panelId }
        }));
    }

    hidePanel() {
        const panel = document.getElementById('right-panel');
        panel.classList.add('translate-x-full');
        this.isVisible = false;
        this.currentPanel = null;

        // 取消左侧工具栏的激活状态
        if (window.Sidebar) {
            window.Sidebar.deactivateTool();
        }
    }

    getPanelTitle(panelId) {
        const titles = {
            'mapTools': '地图工具',
            'drawTools': '绘制工具',
            'editTools': '编辑工具',
            'queryTools': '查询工具',
            'layersPanel': '图层管理',
            'attributeTable': '属性表',
            'measureTools': '量测工具',
            'analysisTools': '空间分析',
            'dataManagement': '数据管理'
        };
        return titles[panelId] || '面板';
    }

    async loadPanelContent(panelId, container) {
        try {
            let content = '';

            switch(panelId) {
                case 'mapTools':
                    content = this.renderMapTools();
                    break;
                case 'drawTools':
                    content = this.renderDrawTools();
                    break;
                case 'layersPanel':
                    content = await this.renderLayersPanel();
                    break;
                case 'analysisTools':
                    content = this.renderAnalysisTools();
                    break;
                case 'dataManagement':
                    content = this.renderDataManagement();
                    break;
                default:
                    content = '<p class="text-slate-400 text-center py-8">功能开发中...</p>';
            }

            container.innerHTML = content;
            this.bindPanelEvents(panelId);
        } catch (error) {
            console.error('加载面板内容失败:', error);
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-2"></i>
                    <p class="text-slate-400">加载失败</p>
                </div>
            `;
        }
    }

    renderMapTools() {
        return `
            <div class="space-y-4">
                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3 flex items-center">
                        <i class="fas fa-layer-group mr-2 text-green-400"></i>
                        底图切换
                    </h4>
                    <div id="basemap-list" class="space-y-2">
                        <div class="flex items-center justify-center py-4">
                            <div class="spinner"></div>
                        </div>
                    </div>
                </div>

                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">视图控制</h4>
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick="window.MapManager?.zoomIn()" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 cursor-pointer transition-colors">
                            <i class="fas fa-plus mr-2"></i>放大
                        </button>
                        <button onclick="window.MapManager?.zoomOut()" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 cursor-pointer transition-colors">
                            <i class="fas fa-minus mr-2"></i>缩小
                        </button>
                        <button onclick="window.MapManager?.fitBounds()" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 cursor-pointer transition-colors">
                            <i class="fas fa-expand mr-2"></i>全图
                        </button>
                        <button onclick="window.MapManager?.saveBookmark()" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 cursor-pointer transition-colors">
                            <i class="fas fa-bookmark mr-2"></i>书签
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderDrawTools() {
        return `
            <div class="space-y-4">
                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">绘制工具</h4>
                    <div class="space-y-2">
                        <button onclick="window.DrawTools?.drawPoint()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-map-marker-alt mr-3 text-green-400"></i>
                            <span>绘制点</span>
                        </button>
                        <button onclick="window.DrawTools?.drawLine()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-route mr-3 text-blue-400"></i>
                            <span>绘制线</span>
                        </button>
                        <button onclick="window.DrawTools?.drawPolygon()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-draw-polygon mr-3 text-yellow-400"></i>
                            <span>绘制多边形</span>
                        </button>
                        <button onclick="window.DrawTools?.drawRectangle()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-square mr-3 text-purple-400"></i>
                            <span>绘制矩形</span>
                        </button>
                        <button onclick="window.DrawTools?.drawCircle()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-circle mr-3 text-pink-400"></i>
                            <span>绘制圆形</span>
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">操作</h4>
                    <div class="space-y-2">
                        <button onclick="window.DrawTools?.saveFeatures()" class="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white cursor-pointer transition-colors">
                            <i class="fas fa-save mr-2"></i>保存到数据集
                        </button>
                        <button onclick="window.DrawTools?.clearDrawings()" class="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white cursor-pointer transition-colors">
                            <i class="fas fa-trash mr-2"></i>清除绘制
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async renderLayersPanel() {
        // 从API获取图层列表
        try {
            const response = await Auth.fetch('/api/datasets');
            const datasets = await response.json();

            return `
                <div class="space-y-4">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-slate-400 text-sm">${datasets.length || 0} 个图层</span>
                        <button onclick="window.LayerManager?.addLayer()" class="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm cursor-pointer transition-colors">
                            <i class="fas fa-plus mr-1"></i>添加
                        </button>
                    </div>

                    <div id="layer-tree" class="space-y-1">
                        ${this.renderLayerTree(datasets)}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('获取图层列表失败:', error);
            return '<p class="text-slate-400 text-center py-8">加载图层列表失败</p>';
        }
    }

    renderLayerTree(datasets) {
        if (!datasets || datasets.length === 0) {
            return '<p class="text-slate-500 text-sm text-center py-4">暂无图层</p>';
        }

        return datasets.map(layer => `
            <div class="layer-item glass-panel p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer"
                 data-layer-id="${layer.id}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2 flex-1">
                        <input type="checkbox" checked class="layer-visibility" data-layer-id="${layer.id}">
                        <i class="fas fa-layer-group text-slate-400 text-sm"></i>
                        <span class="text-slate-300 text-sm">${layer.name}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="window.LayerManager?.zoomToLayer('${layer.id}')" class="p-1 hover:bg-slate-600 rounded transition-colors" title="缩放到图层">
                            <i class="fas fa-search-location text-slate-400 text-xs"></i>
                        </button>
                        <button onclick="window.LayerManager?.removeLayer('${layer.id}')" class="p-1 hover:bg-slate-600 rounded transition-colors" title="移除图层">
                            <i class="fas fa-trash text-slate-400 text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderAnalysisTools() {
        return `
            <div class="space-y-3">
                <div class="glass-panel p-3 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3 text-sm flex items-center">
                        <i class="fas fa-mountain mr-2 text-green-400"></i>地形分析
                    </h4>
                    <div class="space-y-2">
                        <button onclick="window.AnalysisTools?.openAnalysis('slope')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            坡度分析
                        </button>
                        <button onclick="window.AnalysisTools?.openAnalysis('aspect')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            坡向分析
                        </button>
                        <button onclick="window.AnalysisTools?.openAnalysis('hillshade')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            山体阴影
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-3 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3 text-sm flex items-center">
                        <i class="fas fa-fire mr-2 text-red-400"></i>密度分析
                    </h4>
                    <div class="space-y-2">
                        <button onclick="window.AnalysisTools?.openAnalysis('kernel-density')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            核密度分析
                        </button>
                        <button onclick="window.AnalysisTools?.openAnalysis('point-density')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            点密度分析
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-3 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3 text-sm flex items-center">
                        <i class="fas fa-layer-group mr-2 text-yellow-400"></i>栅格分析
                    </h4>
                    <div class="space-y-2">
                        <button onclick="window.AnalysisTools?.openAnalysis('weighted-overlay')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            <div class="flex items-center justify-between">
                                <span>加权叠加</span>
                                <span class="text-xs text-green-400">核心</span>
                            </div>
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-3 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3 text-sm flex items-center">
                        <i class="fas fa-chart-line mr-2 text-blue-400"></i>插值分析
                    </h4>
                    <div class="space-y-2">
                        <button onclick="window.AnalysisTools?.openAnalysis('idw')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            IDW插值
                        </button>
                        <button onclick="window.AnalysisTools?.openAnalysis('kriging')" class="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm text-left cursor-pointer transition-colors">
                            Kriging插值
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderDataManagement() {
        return `
            <div class="space-y-4">
                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">数据导入</h4>
                    <div class="space-y-2">
                        <button onclick="window.DataManager?.importGeoJSON()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-file-import mr-3 text-green-400"></i>
                            <span>导入GeoJSON</span>
                        </button>
                        <button onclick="window.DataManager?.importCSV()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-file-csv mr-3 text-blue-400"></i>
                            <span>导入CSV（带坐标）</span>
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">数据导出</h4>
                    <div class="space-y-2">
                        <button onclick="window.DataManager?.exportGeoJSON()" class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center">
                            <i class="fas fa-file-export mr-3 text-yellow-400"></i>
                            <span>导出GeoJSON</span>
                        </button>
                    </div>
                </div>

                <div class="glass-panel p-4 rounded-lg">
                    <h4 class="text-slate-300 font-medium mb-3">数据集管理</h4>
                    <div class="space-y-2">
                        <button onclick="window.DataManager?.viewMetadata()" class="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm cursor-pointer transition-colors">
                            查看元数据
                        </button>
                        <button onclick="window.DataManager?.addField()" class="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm cursor-pointer transition-colors">
                            添加字段
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    bindPanelEvents(panelId) {
        // 根据面板类型绑定特定事件
        switch(panelId) {
            case 'mapTools':
                this.loadBasemaps();
                break;
            case 'layersPanel':
                this.bindLayerEvents();
                break;
        }
    }

    async loadBasemaps() {
        try {
            const response = await Auth.fetch('/api/map-services/recommendations/basemaps');
            const data = await response.json();

            const container = document.getElementById('basemap-list');
            if (!container) return;

            container.innerHTML = data.basemaps.map(basemap => `
                <button onclick="window.MapManager?.changeBasemap('${basemap.id}')"
                        class="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-left cursor-pointer transition-colors flex items-center justify-between">
                    <span>${basemap.name}</span>
                    ${basemap.type === 'iserver' ? '<span class="text-xs text-green-400">iServer</span>' : '<span class="text-xs text-slate-500">OSM</span>'}
                </button>
            `).join('');
        } catch (error) {
            console.error('加载底图列表失败:', error);
        }
    }

    bindLayerEvents() {
        // 图层可见性切换
        document.querySelectorAll('.layer-visibility').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const layerId = e.target.dataset.layerId;
                const visible = e.target.checked;
                if (window.LayerManager) {
                    window.LayerManager.setLayerVisibility(layerId, visible);
                }
            });
        });
    }
}

// 导出为全局对象
window.RightPanel = new RightPanel();
