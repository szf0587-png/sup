/**
 * 地图服务API封装
 * 对接后端 /api/map-services/* 接口
 */

const MapServicesAPI = {
    /**
     * 列出所有地图服务
     */
    async listServices() {
        const response = await Auth.fetch('/api/map-services/list');
        return await response.json();
    },

    /**
     * 获取地图服务详情
     */
    async getServiceInfo(serviceName) {
        const response = await Auth.fetch(`/api/map-services/${serviceName}`);
        return await response.json();
    },

    /**
     * 获取瓦片图层配置（供Leaflet使用）
     */
    async getTileConfig(serviceName, mapName = null) {
        const url = mapName
            ? `/api/map-services/${serviceName}/tile-config?map_name=${mapName}`
            : `/api/map-services/${serviceName}/tile-config`;

        const response = await Auth.fetch(url);
        return await response.json();
    },

    /**
     * 列出服务中的所有地图
     */
    async listMaps(serviceName) {
        const response = await Auth.fetch(`/api/map-services/${serviceName}/maps`);
        return await response.json();
    },

    /**
     * 获取推荐底图配置
     */
    async getBasemapRecommendations() {
        const response = await Auth.fetch('/api/map-services/recommendations/basemaps');
        return await response.json();
    }
};

window.MapServicesAPI = MapServicesAPI;
