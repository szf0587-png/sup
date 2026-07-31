/**
 * 地图管理器
 * 负责底图切换、视图控制、地图交互
 */

class MapManager {
    constructor(map) {
        this.map = map;
        this.currentBasemap = null;
        this.basemapLayers = {};
        this.bookmarks = [];
    }

    /**
     * 初始化地图管理器
     */
    async init() {
        try {
            // 加载推荐底图
            await this.loadBasemaps();
            console.log('✓ MapManager初始化完成');
        } catch (error) {
            console.error('MapManager初始化失败:', error);
        }
    }

    /**
     * 加载推荐底图列表（无需登录即可使用 iServer China100）
     */
    async loadBasemaps() {
        // 始终优先注入 iServer China100（公共瓦片，无需认证）
        this.basemapConfigs = [];
        this.addChina100Option();

        // 尝试从后端加载更多底图（需要登录）
        try {
            const data = await MapServicesAPI.getBasemapRecommendations();
            if (data.basemaps && data.basemaps.length > 0) {
                // 合并，避免重复
                const existingIds = new Set(this.basemapConfigs.map(b => b.id));
                data.basemaps.forEach(b => {
                    if (!existingIds.has(b.id)) {
                        this.basemapConfigs.push(b);
                    }
                });
            }
        } catch (error) {
            // 未登录或 API 不可用时静默降级 — China100 已就绪
            console.warn('后端底图列表不可用（可能需要登录），已使用本地底图', error.message || error);
        }

        // 默认以 China100 作为初始底图
        if (this.basemapConfigs.length > 0 && !this.currentBasemap) {
            await this.changeBasemap(this.basemapConfigs[0].id);
        }

        return this.basemapConfigs;
    }

    /**
     * 追加 iServer China100 底图为可选项（公共瓦片，无需登录）
     */
    addChina100Option() {
        if (!this.basemapConfigs) this.basemapConfigs = [];

        const chinaMaps = [
            {
                id: 'china100-dark',
                name: '中国全图 · 暗色 (iServer)',
                type: 'iserver',
                tile_url: 'http://localhost:8090/iserver/services/map-China100/rest/maps/China100_2021_Dark/zxyTileImage.png?z={z}&x={x}&y={y}&width=256&height=256',
                attribution: 'SuperMap iServer',
                min_zoom: 0,
                max_zoom: 12,
                is_china100: true
            },
            {
                id: 'china100-light',
                name: '中国全图 · 亮色 (iServer)',
                type: 'iserver',
                tile_url: 'http://localhost:8090/iserver/services/map-China100/rest/maps/China100_2021_Light/zxyTileImage.png?z={z}&x={x}&y={y}&width=256&height=256',
                attribution: 'SuperMap iServer',
                min_zoom: 0,
                max_zoom: 12,
                is_china100: true
            }
        ];

        chinaMaps.forEach(entry => {
            if (!this.basemapConfigs.find(b => b.id === entry.id)) {
                this.basemapConfigs.push(entry);
            }
        });

        // 追加 Esri 卫星底图回选项（供切换回原底图）
        if (!this.basemapConfigs.find(b => b.id === 'esri-satellite')) {
            this.basemapConfigs.push({
                id: 'esri-satellite',
                name: 'Esri 卫星影像',
                type: 'osm',
                tile_url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attribution: 'Esri, Maxar, Earthstar Geographics',
                min_zoom: 0,
                max_zoom: 19
            });
        }
    }

    /**
     * 切换底图
     */
    async changeBasemap(basemapId) {
        try {
            // 首次切换时，清理页面初始化阶段直接加的旧瓦片层（如 ArcGIS Esri）
            if (!this._initialCleanupDone) {
                this.map.eachLayer(layer => {
                    if (layer instanceof L.TileLayer && !Object.values(this.basemapLayers).includes(layer)) {
                        this.map.removeLayer(layer);
                    }
                });
                this._initialCleanupDone = true;
            }

            // 移除当前底图
            if (this.currentBasemap && this.basemapLayers[this.currentBasemap]) {
                this.map.removeLayer(this.basemapLayers[this.currentBasemap]);
            }

            // 如果已经加载过该底图，直接使用
            if (this.basemapLayers[basemapId]) {
                this.map.addLayer(this.basemapLayers[basemapId]);
                this.basemapLayers[basemapId].bringToBack();
                this.currentBasemap = basemapId;
                return;
            }

            // 查找底图配置
            const basemapConfig = this.basemapConfigs?.find(b => b.id === basemapId);
            if (!basemapConfig) {
                console.error('底图配置不存在:', basemapId);
                return;
            }

            // 创建底图图层
            let layer;
            if (basemapConfig.is_china100) {
                // iServer China100 直连底图（跳过后端 API）
                layer = L.tileLayer(basemapConfig.tile_url, {
                    attribution: basemapConfig.attribution,
                    minZoom: basemapConfig.min_zoom || 0,
                    maxZoom: basemapConfig.max_zoom || 12,
                    tms: false
                });
            } else if (basemapConfig.type === 'iserver') {
                // iServer底图（通过后端 API 获取瓦片配置）
                const serviceName = basemapId.replace('iserver-', '');
                try {
                    const config = await MapServicesAPI.getTileConfig(serviceName);
                    layer = L.tileLayer(config.tile_url, {
                        attribution: config.attribution,
                        minZoom: config.min_zoom,
                        maxZoom: config.max_zoom
                    });
                } catch (e) {
                    console.warn('iServer 瓦片配置获取失败，使用直接 URL', e);
                    layer = L.tileLayer(basemapConfig.tile_url, {
                        attribution: basemapConfig.attribution,
                        minZoom: basemapConfig.min_zoom || 0,
                        maxZoom: basemapConfig.max_zoom || 12
                    });
                }
            } else {
                // OSM底图
                layer = L.tileLayer(basemapConfig.tile_url, {
                    attribution: basemapConfig.attribution,
                    subdomains: ['a', 'b', 'c']
                });
            }

            // 添加到地图
            layer.addTo(this.map);
            layer.bringToBack();

            // 保存图层引用
            this.basemapLayers[basemapId] = layer;
            this.currentBasemap = basemapId;

            console.log('✓ 底图切换成功:', basemapConfig.name);

            // 显示通知
            if (window.showToast) {
                showToast('success', '底图切换', `已切换到 ${basemapConfig.name}`);
            }

        } catch (error) {
            console.error('切换底图失败:', error);
            if (window.showToast) {
                showToast('error', '切换失败', '无法加载底图，请检查iServer服务');
            }
        }
    }

    /**
     * 添加OSM备用底图
     */
    addOSMBasemap() {
        if (this.basemapLayers['osm']) return;

        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            subdomains: ['a', 'b', 'c']
        });

        osmLayer.addTo(this.map);
        osmLayer.bringToBack();

        this.basemapLayers['osm'] = osmLayer;
        this.currentBasemap = 'osm';
    }

    /**
     * 视图控制 - 放大
     */
    zoomIn() {
        this.map.zoomIn();
    }

    /**
     * 视图控制 - 缩小
     */
    zoomOut() {
        this.map.zoomOut();
    }

    /**
     * 视图控制 - 全图
     */
    fitBounds() {
        // 如果有图层，缩放到所有图层的范围
        const layers = [];
        this.map.eachLayer(layer => {
            if (layer instanceof L.GeoJSON || layer instanceof L.Marker) {
                layers.push(layer);
            }
        });

        if (layers.length > 0) {
            const group = L.featureGroup(layers);
            this.map.fitBounds(group.getBounds(), { padding: [50, 50] });
        } else {
            // 回到默认视图
            this.map.setView([34.09, 110.15], 10);
        }
    }

    /**
     * 保存书签
     */
    saveBookmark() {
        const center = this.map.getCenter();
        const zoom = this.map.getZoom();

        const name = prompt('请输入书签名称:');
        if (!name) return;

        const bookmark = {
            id: Date.now(),
            name: name,
            lat: center.lat,
            lng: center.lng,
            zoom: zoom
        };

        this.bookmarks.push(bookmark);

        // 保存到localStorage
        localStorage.setItem('map_bookmarks', JSON.stringify(this.bookmarks));

        if (window.showToast) {
            showToast('success', '书签保存', `书签"${name}"已保存`);
        }

        console.log('✓ 书签已保存:', bookmark);
    }

    /**
     * 加载书签
     */
    loadBookmarks() {
        const stored = localStorage.getItem('map_bookmarks');
        if (stored) {
            this.bookmarks = JSON.parse(stored);
        }
        return this.bookmarks;
    }

    /**
     * 跳转到书签
     */
    goToBookmark(bookmarkId) {
        const bookmark = this.bookmarks.find(b => b.id === bookmarkId);
        if (bookmark) {
            this.map.setView([bookmark.lat, bookmark.lng], bookmark.zoom);
        }
    }

    /**
     * 删除书签
     */
    deleteBookmark(bookmarkId) {
        this.bookmarks = this.bookmarks.filter(b => b.id !== bookmarkId);
        localStorage.setItem('map_bookmarks', JSON.stringify(this.bookmarks));
    }

    /**
     * 获取当前地图中心和缩放级别
     */
    getCurrentView() {
        return {
            center: this.map.getCenter(),
            zoom: this.map.getZoom(),
            bounds: this.map.getBounds()
        };
    }

    /**
     * 设置地图视图
     */
    setView(lat, lng, zoom) {
        this.map.setView([lat, lng], zoom);
    }

    /**
     * 飞行到指定位置（动画）
     */
    flyTo(lat, lng, zoom = 13) {
        this.map.flyTo([lat, lng], zoom, {
            animate: true,
            duration: 1.5
        });
    }

    /**
     * 获取地图实例
     */
    getMap() {
        return this.map;
    }
}

// 导出为全局对象（初始化时需要传入地图实例）
window.MapManager = null; // 将在地图创建后初始化
