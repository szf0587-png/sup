(function () {
    "use strict";

    const LUONAN_VIEW = Object.freeze({ latitude: 34.09, longitude: 110.15 });
    const CESIUM_SCRIPT = "https://cdn.jsdelivr.net/npm/cesium@1.114/Build/Cesium/Cesium.js";
    const CESIUM_STYLES = "https://cdn.jsdelivr.net/npm/cesium@1.114/Build/Cesium/Widgets/widgets.css";
    const FALLBACK_STANDARD_ID = "5c52a232-c322-43e2-91a2-00119bb282cc";

    const state = {
        mode: "2d",
        cesiumViewer: null,
        cesiumPromise: null,
        towns: [],
        selectedTownCode: null,
    };

    const byId = (id) => document.getElementById(id);

    function setStatus(message) {
        const status = byId("map-mode-status");
        if (status) status.textContent = message;
    }

    function setLoading(visible, message) {
        const loading = byId("map-loading");
        if (!loading) return;
        loading.hidden = !visible;
        const label = loading.querySelector("span:last-child");
        if (label && message) label.textContent = message;
    }

    function loadCesiumAssets() {
        if (window.Cesium) return Promise.resolve(window.Cesium);
        if (state.cesiumPromise) return state.cesiumPromise;

        state.cesiumPromise = new Promise((resolve, reject) => {
            if (!document.querySelector(`link[href="${CESIUM_STYLES}"]`)) {
                const stylesheet = document.createElement("link");
                stylesheet.rel = "stylesheet";
                stylesheet.href = CESIUM_STYLES;
                document.head.appendChild(stylesheet);
            }

            const script = document.createElement("script");
            script.src = CESIUM_SCRIPT;
            script.async = true;
            script.onload = () => resolve(window.Cesium);
            script.onerror = () => reject(new Error("三维引擎资源加载失败"));
            document.head.appendChild(script);
        });
        return state.cesiumPromise;
    }

    function createCesiumViewer(Cesium) {
        if (state.cesiumViewer) return state.cesiumViewer;

        const viewer = new Cesium.Viewer("cesium-map", {
            baseLayerPicker: false,
            geocoder: false,
            homeButton: false,
            sceneModePicker: false,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            infoBox: false,
            selectionIndicator: false,
            terrainProvider: new Cesium.EllipsoidTerrainProvider(),
        });
        viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#18231d");
        viewer.scene.globe.enableLighting = true;
        viewer.scene.skyAtmosphere.show = false;
        viewer.scene.fog.enabled = true;
        viewer.scene.backgroundColor = Cesium.Color.fromCssColorString("#090d0c");
        viewer.imageryLayers.removeAll();

        try {
            viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                url: "https://tile.openstreetmap.org/",
            }));
        } catch (error) {
            console.warn("[workspace] 三维底图不可用，保留地球表面", error);
        }

        state.cesiumViewer = viewer;
        renderCesiumTowns();
        focusLuonan(false);
        return viewer;
    }

    function scoreColor(Cesium, score) {
        if (score >= 80) return Cesium.Color.fromCssColorString("#68d69d");
        if (score >= 74) return Cesium.Color.fromCssColorString("#d2a45f");
        return Cesium.Color.fromCssColorString("#9aa9a0");
    }

    function renderCesiumTowns() {
        const viewer = state.cesiumViewer;
        if (!viewer || !window.Cesium) return;
        const Cesium = window.Cesium;
        viewer.entities.removeAll();

        state.towns.forEach((town, index) => {
            const score = Number(town.overall_score);
            const height = Math.max(180, score * 42);
            viewer.entities.add({
                id: `town-${town.town_code}`,
                position: Cesium.Cartesian3.fromDegrees(town.longitude, town.latitude, height / 2),
                cylinder: {
                    length: height,
                    topRadius: 1050,
                    bottomRadius: 1050,
                    material: scoreColor(Cesium, score).withAlpha(0.82),
                    outline: true,
                    outlineColor: Cesium.Color.fromCssColorString("#edf3ef").withAlpha(0.5),
                },
                label: {
                    text: `${index + 1}  ${town.town_name}\n${score.toFixed(1)}`,
                    font: "600 14px Noto Sans SC",
                    fillColor: Cesium.Color.fromCssColorString("#edf3ef"),
                    showBackground: true,
                    backgroundColor: Cesium.Color.fromCssColorString("#101614").withAlpha(0.86),
                    pixelOffset: new Cesium.Cartesian2(0, -36),
                    distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 130000),
                },
            });
        });
    }

    function updateModeButtons() {
        ["2d", "3d"].forEach((mode) => {
            const button = byId(`view-${mode}`);
            if (!button) return;
            const isActive = state.mode === mode;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        });
    }

    async function setViewMode(mode) {
        if (mode === state.mode) return;

        if (mode === "2d") {
            state.mode = "2d";
            document.body.classList.remove("is-3d");
            byId("cesium-map")?.setAttribute("aria-hidden", "true");
            updateModeButtons();
            setStatus("二维业务底图");
            window.setTimeout(() => window.map?.invalidateSize(), 40);
            return;
        }

        setLoading(true, "正在初始化三维场景");
        setStatus("三维场景加载中");
        try {
            const Cesium = await loadCesiumAssets();
            createCesiumViewer(Cesium);
            state.mode = "3d";
            document.body.classList.add("is-3d");
            byId("cesium-map")?.setAttribute("aria-hidden", "false");
            updateModeButtons();
            setStatus("三维候选乡镇视图 · 椭球地形");
        } catch (error) {
            state.cesiumPromise = null;
            state.mode = "2d";
            document.body.classList.remove("is-3d");
            updateModeButtons();
            setStatus(error instanceof Error ? `${error.message}，已返回二维` : "三维不可用，已返回二维");
        } finally {
            setLoading(false);
        }
    }

    function focusLuonan(animate = true) {
        if (state.mode === "3d" && state.cesiumViewer && window.Cesium) {
            const destination = window.Cesium.Cartesian3.fromDegrees(
                LUONAN_VIEW.longitude,
                LUONAN_VIEW.latitude,
                42000,
            );
            if (animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                state.cesiumViewer.camera.flyTo({ destination, duration: 1.1 });
            } else {
                state.cesiumViewer.camera.setView({ destination });
            }
            return;
        }
        window.map?.flyTo([LUONAN_VIEW.latitude, LUONAN_VIEW.longitude], 10, { duration: animate ? 0.8 : 0 });
    }

    function focusTown(town) {
        state.selectedTownCode = town.town_code;
        document.querySelectorAll(".rank-row").forEach((row) => {
            row.classList.toggle("is-selected", row.dataset.townCode === town.town_code);
        });

        if (state.mode === "3d" && state.cesiumViewer && window.Cesium) {
            state.cesiumViewer.camera.flyTo({
                destination: window.Cesium.Cartesian3.fromDegrees(town.longitude, town.latitude, 13000),
                duration: 0.8,
            });
            return;
        }
        window.map?.flyTo([town.latitude, town.longitude], 12, { duration: 0.8 });
    }

    function renderRanking(result) {
        const list = byId("town-ranking-list");
        const badge = byId("ranking-data-mode");
        if (!list || !badge) return;

        state.towns = Array.isArray(result.towns) ? result.towns : [];
        window._lastScreeningRunId = result.run_id || null;
        badge.textContent = result.data_mode === "mock" || result.status === "mock" ? "演示数据" : "真实计算";
        badge.classList.toggle("is-mock", result.data_mode === "mock" || result.status === "mock");

        if (!state.towns.length) {
            list.innerHTML = '<div class="ranking-state">暂无可参与排名的乡镇，请检查数据覆盖率。</div>';
            renderCesiumTowns();
            return;
        }

        list.replaceChildren(...state.towns.map((town, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "rank-row";
            button.dataset.townCode = town.town_code;
            button.setAttribute("aria-label", `聚焦第 ${index + 1} 名 ${town.town_name}`);
            button.innerHTML = `
                <span class="rank-number">${String(index + 1).padStart(2, "0")}</span>
                <span>
                    <span class="rank-name">${town.town_name}</span>
                    <span class="rank-factors">
                        <span>适宜 ${Number(town.suitability_score).toFixed(1)}</span>
                        <span>物候 ${Number(town.phenology_score).toFixed(1)}</span>
                        <span>覆盖 ${Math.round(Number(town.data_coverage) * 100)}%</span>
                    </span>
                </span>
                <span class="rank-score">${Number(town.overall_score).toFixed(1)}</span>`;
            button.addEventListener("click", () => focusTown(town));
            return button;
        }));
        renderCesiumTowns();
    }

    async function loadRanking() {
        const list = byId("town-ranking-list");
        const badge = byId("ranking-data-mode");
        if (list) list.innerHTML = '<div class="ranking-state"><span class="map-loading-spinner" aria-hidden="true"></span>正在计算乡镇排名</div>';
        if (badge) {
            badge.textContent = "计算中";
            badge.classList.remove("is-mock");
        }

        try {
            const standardsResponse = await fetch("/api/golden-standards/list");
            const standards = standardsResponse.ok ? await standardsResponse.json() : [];
            const standardId = standards[0]?.id || standards[0]?.model_id || FALLBACK_STANDARD_ID;
            const response = await fetch("/api/screening/runs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ golden_standard_id: standardId, county: "洛南县", top_n: 5 }),
            });
            if (!response.ok) throw new Error(`筛选服务返回 ${response.status}`);
            renderRanking(await response.json());
        } catch (error) {
            if (badge) badge.textContent = "不可用";
            if (list) list.innerHTML = `<div class="ranking-state">${error instanceof Error ? error.message : "无法读取乡镇排名"}</div>`;
        }
    }

    function initializeWorkspace() {
        byId("view-2d")?.addEventListener("click", () => setViewMode("2d"));
        byId("view-3d")?.addEventListener("click", () => setViewMode("3d"));
        byId("focus-luonan")?.addEventListener("click", () => focusLuonan());
        byId("refresh-ranking")?.addEventListener("click", loadRanking);
        // 暴露 towns 状态供地块精评模块读取
        window._getWorkspaceTowns = () => state.towns;
        loadRanking();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeWorkspace, { once: true });
    } else {
        initializeWorkspace();
    }
})();
