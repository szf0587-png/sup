/**
 * 空间分析API封装
 * 对接后端 /api/spatial-analysis/* 接口
 */

const SpatialAnalysisAPI = {
    /**
     * 地形分析 - 坡度
     */
    async analyzeSlope(params) {
        const response = await Auth.fetch('/api/spatial-analysis/terrain/slope', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 地形分析 - 坡向
     */
    async analyzeAspect(params) {
        const response = await Auth.fetch('/api/spatial-analysis/terrain/aspect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 地形分析 - 山体阴影
     */
    async analyzeHillshade(params) {
        const response = await Auth.fetch('/api/spatial-analysis/terrain/hillshade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 密度分析 - 核密度
     */
    async kernelDensity(params) {
        const response = await Auth.fetch('/api/spatial-analysis/density/kernel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 密度分析 - 点密度
     */
    async pointDensity(params) {
        const response = await Auth.fetch('/api/spatial-analysis/density/point', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 栅格分析 - 加权叠加（核心功能）
     */
    async weightedOverlay(params) {
        const response = await Auth.fetch('/api/spatial-analysis/overlay/weighted', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 插值分析 - IDW
     */
    async idwInterpolation(params) {
        const response = await Auth.fetch('/api/spatial-analysis/interpolation/idw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    },

    /**
     * 插值分析 - Kriging
     */
    async krigingInterpolation(params) {
        const response = await Auth.fetch('/api/spatial-analysis/interpolation/kriging', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await response.json();
    }
};

window.SpatialAnalysisAPI = SpatialAnalysisAPI;
