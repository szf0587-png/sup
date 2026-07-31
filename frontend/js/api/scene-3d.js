/**
 * 三维服务API封装
 * 对接后端 /api/3d-services/* 接口
 */

const Scene3DAPI = {
    /**
     * 列出所有三维场景
     */
    async listScenes() {
        const response = await Auth.fetch('/api/3d-services/scenes/list');
        return await response.json();
    },

    /**
     * 获取三维场景详情
     */
    async getSceneInfo(sceneName) {
        const response = await Auth.fetch(`/api/3d-services/scenes/${sceneName}`);
        return await response.json();
    },

    /**
     * 获取前端三维场景配置（Cesium）
     */
    async getSceneConfig(sceneName) {
        const response = await Auth.fetch(`/api/3d-services/scenes/${sceneName}/config`);
        return await response.json();
    },

    /**
     * 获取地形服务信息
     */
    async getTerrainInfo(sceneName) {
        const response = await Auth.fetch(`/api/3d-services/terrain/${sceneName}/info`);
        return await response.json();
    },

    /**
     * 获取地形缓存生成指南
     */
    async getTerrainGuide() {
        const response = await Auth.fetch('/api/3d-services/terrain/generation-guide');
        return await response.json();
    },

    /**
     * 上传三维模型
     */
    async uploadModel(file, modelName = null, sceneName = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (modelName) formData.append('model_name', modelName);
        if (sceneName) formData.append('scene_name', sceneName);

        const response = await Auth.fetch('/api/3d-services/models/upload', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }
};

window.Scene3DAPI = Scene3DAPI;
