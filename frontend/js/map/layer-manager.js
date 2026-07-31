/**
 * 图层管理器
 * 负责图层的添加、删除、显示/隐藏、样式管理
 */

class LayerManager {
    constructor(map) {
        this.map = map;
        this.layers = new Map(); // layerId -> {layer, config}
        this.layerOrder = []; // 图层顺序
    }

    /**
     * 初始化图层管理器
     */
    async init() {
        try {
            // 加载用户的数据集列表
            await this.loadUserDatasets();
            console.log('✓ LayerManager初始化完成');
        } catch (error) {
            console.error('LayerManager初始化失败:', error);
        }
    }

    /**
     * 加载用户数据集列表
     */
    async loadUserDatasets() {
        try {
            const response = await Auth.fetch('/api/datasets');
            const datasets = await response.json();

            this.userDatasets = datasets || [];
            return this.userDatasets;
        } catch (error) {
            console.error('加载数据集列表失败:', error);
            this.userDatasets = [];
            return [];
        }
    }

    /**
     * 添加图层
     */
    async addLayer(layerConfig) {
        try {
            const { id, name, type, datasource, dataset, style } = layerConfig;

            // 检查图层是否已存在
            if (this.layers.has(id)) {
                console.warn('图层已存在:', id);
                return;
            }

            let layer;

            // 根据类型创建图层
            switch (type) {
                case 'geojson':
                    layer = await this.createGeoJSONLayer(datasource, dataset, style);
                    break;
                case 'wms':
                    layer = this.createWMSLayer(layerConfig);
                    break;
                case 'tile':
                    layer = this.createTileLayer(layerConfig);
                    break;
                default:
                    throw new Error(`不支持的图层类型: ${type}`);
            }

            // 添加到地图
            layer.addTo(this.map);

            // 保存图层引用
            this.layers.set(id, {
                layer: layer,
                config: layerConfig,
                visible: true
            });

            this.layerOrder.push(id);

            console.log('✓ 图层已添加:', name);

            if (window.showToast) {
                showToast('success', '图层添加', `${name} 已添加到地图`);
            }

            // 刷新图层面板
            this.refreshLayerPanel();

            return layer;

        } catch (error) {
            console.error('添加图层失败:', error);
            if (window.showToast) {
                showToast('error', '添加失败', error.message);
            }
            throw error;
        }
    }

    /**
     * 创建GeoJSON图层
     */
    async createGeoJSONLayer(datasource, dataset, style = {}) {
        try {
            // 从API获取数据
            const data = await DataManagementAPI.getRecords(datasource, dataset, 1, 1000);

            // 创建GeoJSON图层
            const layer = L.geoJSON(data, {
                style: feature => ({
                    color: style.color || '#3b82f6',
                    weight: style.weight || 2,
                    fillColor: style.fillColor || '#3b82f6',
                    fillOpacity: style.fillOpacity || 0.2
                }),
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        fillColor: style.color || '#3b82f6',
                        color: '#fff',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                },
                onEachFeature: (feature, layer) => {
                    // 添加点击弹窗
                    const properties = feature.properties || {};
                    let popupContent = '<div class="p-2">';
                    popupContent += '<h4 class="font-bold mb-2">属性信息</h4>';
                    for (const [key, value] of Object.entries(properties)) {
                        popupContent += `<div><strong>${key}:</strong> ${value}</div>`;
                    }
                    popupContent += '</div>';
                    layer.bindPopup(popupContent);
                }
            });

            return layer;

        } catch (error) {
            console.error('创建GeoJSON图层失败:', error);
            throw error;
        }
    }

    /**
     * 创建WMS图层
     */
    createWMSLayer(config) {
        return L.tileLayer.wms(config.url, {
            layers: config.layers,
            format: 'image/png',
            transparent: true,
            attribution: config.attribution || ''
        });
    }

    /**
     * 创建瓦片图层
     */
    createTileLayer(config) {
        return L.tileLayer(config.url, {
            attribution: config.attribution || '',
            maxZoom: config.maxZoom || 18,
            minZoom: config.minZoom || 3
        });
    }

    /**
     * 移除图层
     */
    removeLayer(layerId) {
        const layerData = this.layers.get(layerId);
        if (!layerData) {
            console.warn('图层不存在:', layerId);
            return;
        }

        // 从地图移除
        this.map.removeLayer(layerData.layer);

        // 从集合中删除
        this.layers.delete(layerId);
        this.layerOrder = this.layerOrder.filter(id => id !== layerId);

        console.log('✓ 图层已移除:', layerData.config.name);

        if (window.showToast) {
            showToast('success', '图层移除', `${layerData.config.name} 已从地图移除`);
        }

        // 刷新图层面板
        this.refreshLayerPanel();
    }

    /**
     * 设置图层可见性
     */
    setLayerVisibility(layerId, visible) {
        const layerData = this.layers.get(layerId);
        if (!layerData) return;

        if (visible) {
            if (!this.map.hasLayer(layerData.layer)) {
                this.map.addLayer(layerData.layer);
            }
        } else {
            if (this.map.hasLayer(layerData.layer)) {
                this.map.removeLayer(layerData.layer);
            }
        }

        layerData.visible = visible;
        console.log(`✓ 图层 ${layerData.config.name} 可见性:`, visible);
    }

    /**
     * 缩放到图层
     */
    zoomToLayer(layerId) {
        const layerData = this.layers.get(layerId);
        if (!layerData) return;

        try {
            const bounds = layerData.layer.getBounds();
            if (bounds && bounds.isValid()) {
                this.map.fitBounds(bounds, { padding: [50, 50] });
            }
        } catch (error) {
            console.error('缩放到图层失败:', error);
        }
    }

    /**
     * 设置图层透明度
     */
    setLayerOpacity(layerId, opacity) {
        const layerData = this.layers.get(layerId);
        if (!layerData) return;

        if (layerData.layer.setOpacity) {
            layerData.layer.setOpacity(opacity);
        } else if (layerData.layer.setStyle) {
            layerData.layer.setStyle({ fillOpacity: opacity * 0.5, opacity: opacity });
        }

        console.log(`✓ 图层透明度已设置:`, opacity);
    }

    /**
     * 获取所有图层
     */
    getAllLayers() {
        return Array.from(this.layers.entries()).map(([id, data]) => ({
            id: id,
            name: data.config.name,
            type: data.config.type,
            visible: data.visible
        }));
    }

    /**
     * 获取图层数量
     */
    getLayerCount() {
        return this.layers.size;
    }

    /**
     * 刷新图层面板
     */
    refreshLayerPanel() {
        // 如果右侧面板显示的是图层管理，刷新内容
        if (window.RightPanel && window.RightPanel.currentPanel === 'layersPanel') {
            window.RightPanel.showPanel('layersPanel', '图层管理');
        }

        // 触发图层变化事件
        window.dispatchEvent(new CustomEvent('layersChanged', {
            detail: { count: this.layers.size }
        }));
    }

    /**
     * 弹出添加图层对话框
     */
    async addLayerDialog() {
        // 简单的对话框（实际项目中应该用更好的UI）
        const datasource = prompt('请输入数据源名称:', 'user_ds');
        if (!datasource) return;

        const dataset = prompt('请输入数据集名称:');
        if (!dataset) return;

        const layerId = `layer_${Date.now()}`;

        await this.addLayer({
            id: layerId,
            name: dataset,
            type: 'geojson',
            datasource: datasource,
            dataset: dataset,
            style: {
                color: '#3b82f6',
                weight: 2,
                fillOpacity: 0.2
            }
        });
    }
}

// 导出为全局对象（初始化时需要传入地图实例）
window.LayerManager = null; // 将在地图创建后初始化
