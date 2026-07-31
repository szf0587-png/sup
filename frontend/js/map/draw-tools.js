/**
 * 绘制工具管理器
 * 集成Leaflet.Draw，提供点、线、多边形、矩形、圆形绘制功能
 */

class DrawTools {
    constructor(map) {
        this.map = map;
        this._hasDraw = typeof L !== 'undefined' && L.Draw;
        if (this._hasDraw) {
            this.drawnItems = new L.FeatureGroup();
            this.map.addLayer(this.drawnItems);
        }
        this.currentDrawHandler = null;
        this.features = [];
    }

    /**
     * 初始化绘制工具
     */
    init() {
        if (!this._hasDraw) {
            console.warn('[DrawTools] Leaflet.Draw 插件未加载，绘制功能不可用');
            return;
        }
        // 监听绘制完成事件
        this.map.on(L.Draw.Event.CREATED, (e) => {
            const layer = e.layer;
            this.drawnItems.addLayer(layer);

            // 转换为GeoJSON
            const geojson = layer.toGeoJSON();

            // 添加属性
            const feature = {
                geometry: geojson.geometry,
                properties: {
                    draw_type: e.layerType,
                    created_at: new Date().toISOString(),
                    id: this.generateId()
                }
            };

            this.features.push(feature);

            console.log('✓ 绘制完成:', feature);

            if (window.showToast) {
                showToast('success', '绘制完成', '要素已添加，可以保存到数据集');
            }
        });

        console.log('✓ DrawTools初始化完成');
    }

    /**
     * 检查绘制插件是否可用
     */
    _requireDraw() {
        if (!this._hasDraw) {
            console.warn('[DrawTools] Leaflet.Draw 插件未加载');
            if (window.showToast) showToast('warning', '功能不可用', '绘制插件未加载');
            return false;
        }
        return true;
    }

    /**
     * 绘制点
     */
    drawPoint() {
        if (!this._requireDraw()) return;
        this.cancelCurrentDraw();

        this.currentDrawHandler = new L.Draw.Marker(this.map, {
            icon: L.icon({
                iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            })
        });

        this.currentDrawHandler.enable();

        if (window.showToast) {
            showToast('info', '绘制模式', '请在地图上点击放置标记');
        }
    }

    /**
     * 绘制线
     */
    drawLine() {
        if (!this._requireDraw()) return;
        this.cancelCurrentDraw();

        this.currentDrawHandler = new L.Draw.Polyline(this.map, {
            shapeOptions: {
                color: '#3b82f6',
                weight: 3
            }
        });

        this.currentDrawHandler.enable();

        if (window.showToast) {
            showToast('info', '绘制模式', '请在地图上点击绘制线段');
        }
    }

    /**
     * 绘制多边形
     */
    drawPolygon() {
        if (!this._requireDraw()) return;
        this.cancelCurrentDraw();

        this.currentDrawHandler = new L.Draw.Polygon(this.map, {
            shapeOptions: {
                color: '#22c55e',
                fillColor: '#22c55e',
                fillOpacity: 0.2,
                weight: 2
            }
        });

        this.currentDrawHandler.enable();

        if (window.showToast) {
            showToast('info', '绘制模式', '请在地图上点击绘制多边形');
        }
    }

    /**
     * 绘制矩形
     */
    drawRectangle() {
        if (!this._requireDraw()) return;
        this.cancelCurrentDraw();

        this.currentDrawHandler = new L.Draw.Rectangle(this.map, {
            shapeOptions: {
                color: '#f59e0b',
                fillColor: '#f59e0b',
                fillOpacity: 0.2,
                weight: 2
            }
        });

        this.currentDrawHandler.enable();

        if (window.showToast) {
            showToast('info', '绘制模式', '请在地图上拖拽绘制矩形');
        }
    }

    /**
     * 绘制圆形
     */
    drawCircle() {
        if (!this._requireDraw()) return;
        this.cancelCurrentDraw();

        this.currentDrawHandler = new L.Draw.Circle(this.map, {
            shapeOptions: {
                color: '#ec4899',
                fillColor: '#ec4899',
                fillOpacity: 0.2,
                weight: 2
            }
        });

        this.currentDrawHandler.enable();

        if (window.showToast) {
            showToast('info', '绘制模式', '请在地图上拖拽绘制圆形');
        }
    }

    /**
     * 取消当前绘制
     */
    cancelCurrentDraw() {
        if (this.currentDrawHandler) {
            this.currentDrawHandler.disable();
            this.currentDrawHandler = null;
        }
    }

    /**
     * 清除所有绘制
     */
    clearDrawings() {
        if (confirm('确定要清除所有绘制吗？')) {
            this.drawnItems.clearLayers();
            this.features = [];

            if (window.showToast) {
                showToast('success', '清除完成', '所有绘制已清除');
            }
        }
    }

    /**
     * 保存要素到数据集
     */
    async saveFeatures() {
        if (this.features.length === 0) {
            if (window.showToast) {
                showToast('warning', '无要素', '请先绘制要素');
            }
            return;
        }

        // 弹出对话框选择数据源和数据集
        const datasource = prompt('请输入数据源名称:', 'user_ds');
        if (!datasource) return;

        const dataset = prompt('请输入数据集名称:', 'drawn_features');
        if (!dataset) return;

        try {
            // 调用API保存
            const result = await DataEditingAPI.addFeatures(datasource, dataset, this.features);

            if (window.showToast) {
                showToast('success', '保存成功', `已保存 ${result.feature_count} 个要素到 ${dataset}`);
            }

            // 清除已保存的要素
            this.clearDrawings();

        } catch (error) {
            console.error('保存要素失败:', error);
            if (window.showToast) {
                showToast('error', '保存失败', error.message || '请检查数据源和数据集是否存在');
            }
        }
    }

    /**
     * 导出为GeoJSON
     */
    exportGeoJSON() {
        if (this.features.length === 0) {
            if (window.showToast) {
                showToast('warning', '无要素', '请先绘制要素');
            }
            return;
        }

        const geojson = {
            type: 'FeatureCollection',
            features: this.features.map(f => ({
                type: 'Feature',
                geometry: f.geometry,
                properties: f.properties
            }))
        };

        // 下载GeoJSON文件
        const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `drawn_features_${Date.now()}.geojson`;
        a.click();
        URL.revokeObjectURL(url);

        if (window.showToast) {
            showToast('success', '导出成功', 'GeoJSON文件已下载');
        }
    }

    /**
     * 生成唯一ID
     */
    generateId() {
        return `draw_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 获取已绘制要素数量
     */
    getFeatureCount() {
        return this.features.length;
    }

    /**
     * 获取所有要素
     */
    getFeatures() {
        return this.features;
    }
}

// 导出为全局对象（初始化时需要传入地图实例）
window.DrawTools = null; // 将在地图创建后初始化
