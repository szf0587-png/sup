"use strict";

class TerrainController {
    constructor({ engine, viewer, state, onStatus } = {}) {
        this.engine = engine;
        this.viewer = viewer;
        this.state = state || {};
        this.onStatus = typeof onStatus === "function" ? onStatus : () => {};
    }

    setProvider(provider) {
        this.state.terrainProvider = provider || null;
        if (provider) {
            this.viewer.terrainProvider = provider;
        }
    }

    setVisible(visible) {
        const provider = visible ? this.state.terrainProvider : null;
        if (provider) {
            this.viewer.terrainProvider = provider;
        } else if (this.engine?.EllipsoidTerrainProvider) {
            this.viewer.terrainProvider = new this.engine.EllipsoidTerrainProvider();
        }
        this.state.terrainEnabled = Boolean(visible && this.state.terrainProvider);
        this.viewer.scene?.requestRender?.();
        this.onStatus(this.state.terrainEnabled ? "SCT 地形已显示" : "已切换为椭球地形");
    }

    setExaggeration(value) {
        const next = Number(value);
        if (!Number.isFinite(next) || next <= 0) {
            throw new Error("地形夸张倍数必须是正数");
        }
        this.state.exaggeration = next;
        if (this.viewer.scene) {
            this.viewer.scene.terrainExaggeration = next;
            this.viewer.scene.verticalExaggeration = next;
            this.viewer.scene.requestRender?.();
        }
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { TerrainController };
}
if (typeof window !== "undefined") {
    window.TerrainController = TerrainController;
}
