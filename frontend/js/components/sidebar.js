/**
 * 左侧工具栏组件
 * 垂直工具栏，集成所有GIS工具
 */

class Sidebar {
    constructor() {
        this.activeTool = null;
        this.tools = [
            { id: 'map', icon: 'map', label: '地图工具', panel: 'mapTools' },
            { id: 'draw', icon: 'edit', label: '绘制工具', panel: 'drawTools' },
            { id: 'edit', icon: 'crop', label: '编辑工具', panel: 'editTools' },
            { id: 'query', icon: 'search', label: '查询工具', panel: 'queryTools' },
            { id: 'layers', icon: 'layers', label: '图层管理', panel: 'layersPanel' },
            { id: 'attributes', icon: 'table', label: '属性表', panel: 'attributeTable' },
            { id: 'measure', icon: 'ruler', label: '量测工具', panel: 'measureTools' },
            { id: 'analysis', icon: 'chart-bar', label: '空间分析', panel: 'analysisTools' },
            { id: 'data', icon: 'database', label: '数据管理', panel: 'dataManagement' }
        ];
    }

    render() {
        const html = `
            <div id="sidebar" class="fixed left-0 top-16 bottom-8 w-16 bg-slate-900/95 border-r border-slate-700/50
                        backdrop-blur-sm z-40 flex flex-col items-center py-4 space-y-2">
                ${this.tools.map(tool => this.renderToolButton(tool)).join('')}
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);
        this.bindEvents();
    }

    renderToolButton(tool) {
        return `
            <button
                id="tool-${tool.id}"
                class="sidebar-tool-btn group relative w-12 h-12 rounded-lg
                       flex items-center justify-center
                       transition-all duration-200 cursor-pointer
                       hover:bg-slate-700/50 hover:scale-105"
                data-tool="${tool.id}"
                data-panel="${tool.panel}"
                title="${tool.label}">
                <i class="fas fa-${tool.icon} text-slate-400 group-hover:text-green-400 transition-colors"></i>

                <!-- 工具提示 -->
                <div class="absolute left-full ml-2 px-3 py-1.5 bg-slate-800 text-slate-200 text-sm rounded-lg
                            opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap
                            border border-slate-700">
                    ${tool.label}
                </div>
            </button>
        `;
    }

    bindEvents() {
        document.querySelectorAll('.sidebar-tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = btn.dataset.tool;
                const panel = btn.dataset.panel;
                this.activateTool(tool, panel);
            });
        });
    }

    activateTool(toolId, panelId) {
        // 取消之前激活的工具
        if (this.activeTool) {
            document.getElementById(`tool-${this.activeTool}`)?.classList.remove('bg-green-500/20', 'border-green-500');
        }

        // 激活新工具
        const btn = document.getElementById(`tool-${toolId}`);
        btn.classList.add('bg-green-500/20', 'border', 'border-green-500');
        this.activeTool = toolId;

        // 打开对应面板
        if (window.RightPanel) {
            window.RightPanel.showPanel(panelId);
        }

        // 触发工具激活事件
        window.dispatchEvent(new CustomEvent('toolActivated', {
            detail: { tool: toolId, panel: panelId }
        }));
    }

    deactivateTool() {
        if (this.activeTool) {
            document.getElementById(`tool-${this.activeTool}`)?.classList.remove('bg-green-500/20', 'border-green-500');
            this.activeTool = null;
        }
    }
}

// 导出为全局对象
window.Sidebar = new Sidebar();
