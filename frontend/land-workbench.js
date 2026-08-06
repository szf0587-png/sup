(function () {
    "use strict";

    const API = "";
    const LUONAN_CENTER = { lat: 34.09, lon: 110.15 };
    const VIEW_BOUNDS = {
        west: 109.88,
        east: 110.42,
        south: 33.96,
        north: 34.22,
    };
    const SAMPLE_BOUNDARY = {
        type: "Polygon",
        coordinates: [[
            [110.075, 34.055],
            [110.205, 34.055],
            [110.205, 34.145],
            [110.075, 34.145],
            [110.075, 34.055],
        ]],
    };
    const ESRI_BASEMAP = {
        id: "esri-world-imagery",
        name: "Esri 卫星影像",
        type: "xyz",
        tile_url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution: "Esri, Maxar, Earthstar Geographics",
        min_zoom: 2,
        max_zoom: 19,
    };
    const ANALYSIS_TOOLS = {
        land_summary: {
            component: "land_summary",
            resultKey: "land_summary",
            label: "范围统计",
            sourceLabel: "GeoJSON",
            metrics: [
                ["boundary_area_km2", "范围面积", "km²"],
            ],
        },
        water_constraint: {
            component: "water_constraint",
            resultKey: "water_constraint",
            label: "水体约束",
            sourceLabel: "iServer Water Query",
            metrics: [
                ["feature_count", "命中水体", "个"],
                ["parcel_area_km2", "范围面积", "km²"],
                ["queried_layers", "查询图层", "项"],
            ],
        },
        buffer: {
            component: "buffer",
            resultKey: "buffer",
            label: "缓冲统计",
            sourceLabel: "iServer Buffer",
            metrics: [
                ["buffer_area_km2", "缓冲区", "km²"],
                ["distance_m", "缓冲距离", "m"],
            ],
        },
        road_access: {
            component: "road_access",
            resultKey: "road_access",
            label: "道路空间查询",
            sourceLabel: "iServer Query",
            metrics: [
                ["feature_count", "命中道路", "条"],
                ["layers", "参与图层", "项"],
            ],
        },
        admin_context: {
            component: "admin_context",
            resultKey: "admin_context",
            label: "行政区定位",
            sourceLabel: "iServer Administrative Query",
            metrics: [
                ["feature_count", "命中行政区", "个"],
                ["administrative_names", "行政区名称", ""],
            ],
        },
    };

    const PROCESSING_TOOLS = {
        terrain_slope: { label: "坡度分析", icon: "fa-mountain-sun", sourceLabel: "iServer Terrain", endpoint: "/api/spatial-analysis/terrain/slope", family: "terrain" },
        terrain_aspect: { label: "坡向分析", icon: "fa-compass", sourceLabel: "iServer Terrain", endpoint: "/api/spatial-analysis/terrain/aspect", family: "terrain" },
        terrain_hillshade: { label: "山体阴影", icon: "fa-sun", sourceLabel: "iServer Terrain", endpoint: "/api/spatial-analysis/terrain/hillshade", family: "terrain" },
        density_kernel: { label: "核密度分析", icon: "fa-bullseye", sourceLabel: "iServer Density", endpoint: "/api/spatial-analysis/density/kernel", family: "density" },
        density_point: { label: "点密度分析", icon: "fa-grip", sourceLabel: "iServer Density", endpoint: "/api/spatial-analysis/density/point", family: "density" },
        overlay_weighted: { label: "加权叠加", icon: "fa-layer-group", sourceLabel: "iServer Overlay", endpoint: "/api/spatial-analysis/overlay/weighted", family: "overlay" },
        interpolation_idw: { label: "IDW 插值", icon: "fa-chart-area", sourceLabel: "iServer Interpolation", endpoint: "/api/spatial-analysis/interpolation/idw", family: "interpolation" },
        interpolation_kriging: { label: "Kriging 插值", icon: "fa-wave-square", sourceLabel: "iServer Interpolation", endpoint: "/api/spatial-analysis/interpolation/kriging", family: "interpolation" },
    };
    const ALL_ANALYSIS_TOOLS = { ...ANALYSIS_TOOLS, ...PROCESSING_TOOLS };
    const TOOL_ICONS = {
        land_summary: "fa-vector-square",
        water_constraint: "fa-water",
        buffer: "fa-circle-notch",
        road_access: "fa-road",
        admin_context: "fa-building-columns",
    };
    const PINNED_TOOLS_KEY = "land-resource.pinned-iserver-tools.v1";
    const DEFAULT_PINNED_TOOLS = ["land_summary", "water_constraint", "buffer", "road_access", "admin_context"];
    const MAX_PINNED_TOOLS = 6;

    const DEFAULT_ANALYSIS_OPTIONS = {
        target_use: "general",
        buffer_distance_m: 1000,
        use_3d: true,
        scene_name: "",
        constraint_datasets: "Water_R,Lake_R,MainRiver_R,MainRiver_L,River_L",
        road_datasource: "China100",
        road_dataset: "NationalRd_L",
        weights: {
            terrain: 0.32,
            constraint: 0.30,
            accessibility: 0.22,
            ecology: 0.16,
        },
    };

    const state = {
        mode: "2d",
        boundary: SAMPLE_BOUNDARY,
        previewBoundary: null,
        mapEl: null,
        overlayEl: null,
        drawing: false,
        drawStart: null,
        drawPointerId: null,
        capabilities: null,
        basemapConfig: null,
        baseMapError: null,
        zoom: 4,
        center: { ...LUONAN_CENTER },
        panStart: null,
        dynamicImageRequest: 0,
        leafletMap: null,
        leafletBasemap: null,
        boundaryLayer: null,
        previewLayer: null,
        analysisResultLayer: null,
        basemaps: [ESRI_BASEMAP],
        toolResults: {},
        runningTool: null,
        analysisOptions: structuredClone(DEFAULT_ANALYSIS_OPTIONS),
        processingOptions: {
            datasource: "China100",
            dataset: "",
            slope_type: "DEGREE",
            z_factor: 1,
            azimuth: 315,
            altitude: 45,
            search_radius: 1000,
            cell_size: 100,
            population_field: "",
            z_field: "",
            power: 2,
            variogram_type: "SPHERICAL",
            output_dataset: "",
            layers_json: '[{"dataset":"","weight":1,"reclass_table":[]}]',
        },
        activeAnalysis: null,
        assessmentCompleted: false,
        agentConversationId: null,
        agentProvider: null,
    };

    const $ = (id) => document.getElementById(id);

    function getPinnedToolIds() {
        try {
            const stored = JSON.parse(localStorage.getItem(PINNED_TOOLS_KEY) || "null");
            if (!Array.isArray(stored)) return [...DEFAULT_PINNED_TOOLS];
            return stored.filter((id) => ALL_ANALYSIS_TOOLS[id]).slice(0, MAX_PINNED_TOOLS);
        } catch {
            return [...DEFAULT_PINNED_TOOLS];
        }
    }

    function renderToolbox() {
        const grid = $("analysis-tool-grid");
        const count = $("pinned-tool-count");
        const pinned = getPinnedToolIds();
        if (count) count.textContent = `${pinned.length} / ${MAX_PINNED_TOOLS} 已固定`;
        if (!grid) return;
        if (!pinned.length) {
            grid.innerHTML = '<div class="toolbox-empty">请在工具库中固定需要的分析工具。</div>';
            return;
        }
        grid.replaceChildren(...pinned.map((id) => {
            const tool = ALL_ANALYSIS_TOOLS[id];
            const button = document.createElement("button");
            button.className = "analysis-tool";
            button.type = "button";
            button.dataset.tool = id;
            button.innerHTML = `<i class="fa-solid ${TOOL_ICONS[id] || tool.icon || "fa-gears"}"></i><span>${escapeHtml(tool.label)}</span>`;
            return button;
        }));
        updateToolButtons();
    }

    const authedFetch = (url, options = {}) => {
        if (window.Auth?.getToken()) {
            return window.Auth.fetch(url, options);
        }
        return fetch(url, options);
    };

    function workbenchEvidence() {
        const completed = Object.entries(state.toolResults).map(([id, item]) => ({
            tool: ALL_ANALYSIS_TOOLS[id]?.label || id,
            result: item.detail,
        }));
        return JSON.stringify({
            purpose: "土地资源评估分析与决策支持",
            boundary_selected: Boolean(state.boundary),
            completed_analysis: completed,
            capabilities: state.capabilities ? {
                iserver_online: state.capabilities.iServer,
                dem_available: state.capabilities.dem_available,
                realspace_available: state.capabilities.realspace_available,
                published_datasets: state.capabilities.published_datasets,
            } : "未加载",
            instruction: "基于这些证据提出下一步分析或决策建议；证据不足时必须说明缺口。",
        });
    }

    function appendAgentMessage(role, content) {
        const box = $("agent-messages");
        if (!box) return;
        const intro = box.querySelector(".agent-intro");
        if (intro) intro.remove();
        const item = document.createElement("article");
        item.className = `agent-message ${role}`;
        item.textContent = content;
        box.appendChild(item);
        box.scrollTop = box.scrollHeight;
    }

    async function ensureAgentConversation() {
        if (state.agentConversationId) return state.agentConversationId;
        const created = await authedFetch(`${API}/api/ai/conversations`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: "工作台分析决策" }),
        });
        if (!created.ok) throw new Error("请先登录并配置 AI 供应商");
        state.agentConversationId = (await created.json()).conversation.id;
        return state.agentConversationId;
    }

    async function sendToDecisionAgent(content) {
        const input = $("agent-input");
        const question = String(content || input?.value || "").trim();
        if (!question) return;
        try {
            const providersResponse = await authedFetch(`${API}/api/ai/providers`);
            if (!providersResponse.ok) throw new Error("请先登录后使用分析决策智能体");
            const providers = (await providersResponse.json()).providers || [];
            if (!providers.length) throw new Error("请先配置 AI 供应商与 API Key");
            state.agentProvider = state.agentProvider || providers[0].provider;
            const conversationId = await ensureAgentConversation();
            appendAgentMessage("user", question);
            if (input) input.value = "";
            $("agent-evidence").textContent = `已引用 ${Object.keys(state.toolResults).length} 项阶段成果和当前数据能力`;
            const response = await authedFetch(`${API}/api/ai/conversations/${conversationId}/messages`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: question, provider: state.agentProvider, context: workbenchEvidence() }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || "智能体请求失败");
            appendAgentMessage("assistant", payload.message.content);
        } catch (error) {
            toast(error instanceof Error ? error.message : "智能体请求失败", "error");
        }
    }

    function toast(message, type = "info") {
        const region = $("toast-region");
        if (!region) return;
        const item = document.createElement("div");
        item.className = `toast ${type === "error" ? "is-error" : ""}`;
        item.textContent = message;
        region.appendChild(item);
        window.setTimeout(() => item.remove(), 3600);
    }

    function formatNumber(value, digits = 1) {
        const number = Number(value);
        return Number.isFinite(number) ? number.toFixed(digits) : "--";
    }

    function setChip(id, label, status) {
        const chip = $(id);
        if (!chip) return;
        chip.classList.remove("is-online", "is-warning", "is-offline");
        chip.classList.add(status);
        chip.lastChild.textContent = label;
    }

    function setCapability(id, value) {
        const el = $(id);
        if (el) el.textContent = value;
    }

    function toPercent(value) {
        const number = Number(value);
        if (!Number.isFinite(number)) return "--";
        return `${Math.round(number)}%`;
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function lonToTileX(lon, zoom) {
        return ((lon + 180) / 360) * Math.pow(2, zoom);
    }

    function latToTileY(lat, zoom) {
        const rad = lat * Math.PI / 180;
        return ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * Math.pow(2, zoom);
    }

    function normalizeTileX(x, zoom) {
        const max = Math.pow(2, zoom);
        return ((x % max) + max) % max;
    }

    function lonLatToWorldPixel(lon, lat, zoom) {
        return {
            x: lonToTileX(lon, zoom) * 256,
            y: latToTileY(lat, zoom) * 256,
        };
    }

    function worldPixelToLonLat(x, y, zoom) {
        const worldSize = Math.pow(2, zoom) * 256;
        const lon = (x / worldSize) * 360 - 180;
        const mercator = Math.PI - (2 * Math.PI * y) / worldSize;
        const lat = (180 / Math.PI) * Math.atan(Math.sinh(mercator));
        return [lon, clamp(lat, -85.05112878, 85.05112878)];
    }

    function getMapZoomLimits() {
        const min = Number(state.basemapConfig?.min_zoom ?? 0);
        const max = Number(state.basemapConfig?.max_zoom ?? 4);
        return { min: Number.isFinite(min) ? min : 0, max: Number.isFinite(max) ? max : 4 };
    }

    function getMapView(width, height) {
        const limits = getMapZoomLimits();
        const zoom = clamp(Number(state.zoom) || limits.max, limits.min, limits.max);
        const center = lonLatToWorldPixel(state.center.lon, state.center.lat, zoom);
        return {
            zoom,
            topLeftX: center.x - width / 2,
            topLeftY: center.y - height / 2,
        };
    }

    function lonLatToMercator(lon, lat) {
        const x = (lon * 20037508.34) / 180;
        const y = Math.log(Math.tan(((90 + clamp(lat, -85.05112878, 85.05112878)) * Math.PI) / 360)) / (Math.PI / 180);
        return { x, y: (y * 20037508.34) / 180 };
    }

    function getDynamicImageUrl(config, view, width, height) {
        const [west, north] = worldPixelToLonLat(view.topLeftX, view.topLeftY, view.zoom);
        const [east, south] = worldPixelToLonLat(view.topLeftX + width, view.topLeftY + height, view.zoom);
        const leftBottom = lonLatToMercator(west, south);
        const rightTop = lonLatToMercator(east, north);
        const params = new URLSearchParams({
            width: String(Math.max(1, Math.round(width))),
            height: String(Math.max(1, Math.round(height))),
            transparent: "true",
            cacheEnabled: "false",
            viewBounds: JSON.stringify({ leftBottom, rightTop }),
        });
        return `${config.image_url}?${params.toString()}`;
    }

    function lonLatToPoint(lon, lat, width, height) {
        const view = getMapView(width, height);
        const point = lonLatToWorldPixel(lon, lat, view.zoom);
        return {
            x: point.x - view.topLeftX,
            y: point.y - view.topLeftY,
        };
    }

    function pointToLonLat(x, y, width, height) {
        const view = getMapView(width, height);
        return worldPixelToLonLat(view.topLeftX + x, view.topLeftY + y, view.zoom);
    }

    function geometryToPath(geometry, width, height) {
        if (!geometry || !geometry.type || !geometry.coordinates) return "";
        const rings = geometry.type === "Polygon"
            ? geometry.coordinates
            : geometry.type === "MultiPolygon"
                ? geometry.coordinates.flat()
                : [];
        return rings.map((ring) => {
            if (!ring || ring.length < 2) return "";
            return ring.map((pt, index) => {
                const p = lonLatToPoint(pt[0], pt[1], width, height);
                return `${index === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
            }).join(" ") + " Z";
        }).join(" ");
    }

    function rectangleGeometryFromPoints(a, b) {
        const lon1 = Math.min(a[0], b[0]);
        const lon2 = Math.max(a[0], b[0]);
        const lat1 = Math.min(a[1], b[1]);
        const lat2 = Math.max(a[1], b[1]);
        return {
            type: "Polygon",
            coordinates: [[
                [lon1, lat1],
                [lon2, lat1],
                [lon2, lat2],
                [lon1, lat2],
                [lon1, lat1],
            ]],
        };
    }

    function renderBaseMap() {
        if (state.leafletMap) {
            renderBoundary();
            updateMapControls();
            return;
        }
        if (!state.mapEl) return;
        if (state.basemapConfig?.tile_url && renderBasemapTiles(state.basemapConfig)) {
            return;
        }
        const width = state.mapEl.clientWidth || 1;
        const height = state.mapEl.clientHeight || 1;
        const gridCols = Math.max(8, Math.round(width / 120));
        const gridRows = Math.max(6, Math.round(height / 110));

        state.mapEl.classList.add("is-fallback");
        state.mapEl.innerHTML = `
            <div class="fallback-map">
                <div class="fallback-bg"></div>
                <div class="fallback-grid" style="--cols:${gridCols}; --rows:${gridRows};"></div>
                <div class="fallback-contours"></div>
                <svg class="fallback-overlay" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true"></svg>
                <div class="fallback-label fallback-label-left">离线底图预览</div>
                <div class="fallback-label fallback-label-right">洛南候选区</div>
                <div class="fallback-crosshair"></div>
            </div>
        `;
        state.overlayEl = state.mapEl.querySelector(".fallback-overlay");
        renderBoundary();
        updateMapControls();
    }

    function renderBasemapTiles(config) {
        if (!state.mapEl || !config?.tile_url) return false;

        const width = state.mapEl.clientWidth || 1;
        const height = state.mapEl.clientHeight || 1;
        const gridCols = Math.max(8, Math.round(width / 120));
        const gridRows = Math.max(6, Math.round(height / 110));
        const view = getMapView(width, height);
        const { zoom, topLeftX, topLeftY } = view;
        state.zoom = zoom;
        if (zoom > Number(config.cache_max_zoom ?? config.max_zoom ?? zoom) && config.image_url) {
            return renderDynamicBasemap(config, width, height, view);
        }
        state.dynamicImageRequest += 1;
        const startTileX = Math.floor(topLeftX / 256) - 1;
        const startTileY = Math.floor(topLeftY / 256) - 1;
        const endTileX = Math.ceil((topLeftX + width) / 256) + 1;
        const endTileY = Math.ceil((topLeftY + height) / 256) + 1;
        const maxTile = Math.pow(2, zoom) - 1;
        const tiles = [];

        for (let tileY = startTileY; tileY <= endTileY; tileY += 1) {
            if (tileY < 0 || tileY > maxTile) continue;
            for (let tileX = startTileX; tileX <= endTileX; tileX += 1) {
                const wrappedX = normalizeTileX(tileX, zoom);
                const left = tileX * 256 - topLeftX;
                const top = tileY * 256 - topLeftY;
                const url = config.tile_url
                    .replace("{x}", String(wrappedX))
                    .replace("{y}", String(tileY))
                    .replace("{z}", String(zoom))
                    .replace("{s}", "a");
                tiles.push(`
                    <img class="basemap-tile" src="${url}" alt="" loading="eager" decoding="async"
                         style="left:${left.toFixed(1)}px; top:${top.toFixed(1)}px;">
                `);
            }
        }

        state.mapEl.classList.remove("is-fallback");
        state.mapEl.classList.add("has-real-basemap");
        state.mapEl.innerHTML = `
            <div class="basemap-tiles" aria-hidden="true">${tiles.join("")}</div>
            <div class="fallback-grid subtle-grid" style="--cols:${gridCols}; --rows:${gridRows};"></div>
            <div class="fallback-contours"></div>
            <svg class="fallback-overlay" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true"></svg>
            <div class="fallback-label fallback-label-left">iServer 底图</div>
            <div class="fallback-label fallback-label-right">${config.name || config.service_name || "洛南候选区"}</div>
            <div class="fallback-crosshair"></div>
        `;
        state.overlayEl = state.mapEl.querySelector(".fallback-overlay");
        renderBoundary();
        updateMapControls();
        return true;
    }

    function renderDynamicBasemap(config, width, height, view) {
        const gridCols = Math.max(8, Math.round(width / 120));
        const gridRows = Math.max(6, Math.round(height / 110));
        // Request an overscan image so the local pan preview has real map pixels to reveal.
        const panBuffer = 256;
        const expandedView = {
            ...view,
            topLeftX: view.topLeftX - panBuffer,
            topLeftY: view.topLeftY - panBuffer,
        };
        const imageUrl = getDynamicImageUrl(
            config,
            expandedView,
            width + panBuffer * 2,
            height + panBuffer * 2,
        );
        state.mapEl.classList.remove("is-fallback");
        state.mapEl.classList.add("has-real-basemap");

        const existingImage = state.mapEl.querySelector(".basemap-image");
        if (existingImage) {
            existingImage.style.setProperty("--dynamic-pan-buffer", `${panBuffer}px`);
            requestDynamicMapImage(existingImage, imageUrl);
            state.mapEl.querySelector(".fallback-grid")?.style.setProperty("--cols", gridCols);
            state.mapEl.querySelector(".fallback-grid")?.style.setProperty("--rows", gridRows);
            const label = state.mapEl.querySelector(".fallback-label-right");
            if (label) label.textContent = config.map_name || config.service_name || "评估范围";
            state.overlayEl = state.mapEl.querySelector(".fallback-overlay");
            renderBoundary();
            updateMapControls();
            return true;
        }

        state.dynamicImageRequest += 1;
        state.mapEl.innerHTML = `
            <img class="basemap-image" src="${imageUrl}" alt="" decoding="async"
                 style="--dynamic-pan-buffer:${panBuffer}px;">
            <div class="fallback-grid subtle-grid" style="--cols:${gridCols}; --rows:${gridRows};"></div>
            <svg class="fallback-overlay" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true"></svg>
            <div class="fallback-label fallback-label-left">iServer 动态出图</div>
            <div class="fallback-label fallback-label-right">${config.map_name || config.service_name || "评估范围"}</div>
            <div class="fallback-crosshair"></div>
        `;
        state.overlayEl = state.mapEl.querySelector(".fallback-overlay");
        renderBoundary();
        updateMapControls();
        return true;
    }

    function requestDynamicMapImage(currentImage, imageUrl) {
        const requestId = ++state.dynamicImageRequest;
        const preload = new Image();
        preload.decoding = "async";
        preload.alt = "";

        preload.addEventListener("load", () => {
            if (requestId !== state.dynamicImageRequest || !currentImage.isConnected) return;
            preload.className = currentImage.className;
            preload.style.cssText = currentImage.style.cssText;
            currentImage.replaceWith(preload);
        }, { once: true });
        preload.addEventListener("error", () => {
            if (requestId === state.dynamicImageRequest) {
                toast("底图更新失败，已保留当前地图", "error");
            }
        }, { once: true });
        preload.src = imageUrl;
    }

    function renderBoundary() {
        if (state.leafletMap) {
            if (state.boundaryLayer) state.leafletMap.removeLayer(state.boundaryLayer);
            if (state.previewLayer) state.leafletMap.removeLayer(state.previewLayer);
            state.boundaryLayer = state.boundary ? L.geoJSON(state.boundary, {
                style: { color: "#0f766e", weight: 3, fillColor: "#0f766e", fillOpacity: 0.14 },
            }).addTo(state.leafletMap) : null;
            state.previewLayer = state.previewBoundary ? L.geoJSON(state.previewBoundary, {
                style: { color: "#d97706", weight: 2, dashArray: "8 6", fillOpacity: 0.08 },
            }).addTo(state.leafletMap) : null;
            return;
        }
        if (!state.overlayEl || !state.mapEl) return;
        const width = state.mapEl.clientWidth || 1;
        const height = state.mapEl.clientHeight || 1;
        const mainPath = geometryToPath(state.boundary, width, height);
        const previewPath = geometryToPath(state.previewBoundary, width, height);

        const centerPoint = lonLatToPoint(LUONAN_CENTER.lon, LUONAN_CENTER.lat, width, height);
        state.overlayEl.innerHTML = `
            <defs>
                <linearGradient id="boundaryFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="rgba(15,118,110,0.20)" />
                    <stop offset="100%" stop-color="rgba(15,118,110,0.06)" />
                </linearGradient>
            </defs>
            <circle cx="${centerPoint.x.toFixed(1)}" cy="${centerPoint.y.toFixed(1)}" r="7" fill="#0f766e" opacity="0.8"></circle>
            ${mainPath ? `<path d="${mainPath}" fill="url(#boundaryFill)" stroke="#0f766e" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"></path>` : ""}
            ${previewPath ? `<path d="${previewPath}" fill="rgba(217,119,6,0.12)" stroke="#d97706" stroke-width="2" stroke-dasharray="8 6" stroke-linejoin="round" stroke-linecap="round"></path>` : ""}
        `;
    }

    function setBoundary(geometry, sourceLabel) {
        state.boundary = geometry;
        state.previewBoundary = null;
        $("boundary-status").querySelector("span").textContent = sourceLabel;
        renderBoundary();
    }

    function fitBoundary() {
        if (state.leafletMap) {
            if (state.boundaryLayer) state.leafletMap.fitBounds(state.boundaryLayer.getBounds(), { padding: [36, 36] });
            else state.leafletMap.setView([LUONAN_CENTER.lat, LUONAN_CENTER.lon], 11);
            return;
        }
        const geometry = state.boundary;
        const points = geometry?.type === "Polygon"
            ? geometry.coordinates.flat()
            : geometry?.type === "MultiPolygon"
                ? geometry.coordinates.flat(2)
                : [];
        if (points.length) {
            const longitudes = points.map((point) => point[0]);
            const latitudes = points.map((point) => point[1]);
            state.center = {
                lon: (Math.min(...longitudes) + Math.max(...longitudes)) / 2,
                lat: (Math.min(...latitudes) + Math.max(...latitudes)) / 2,
            };
        } else {
            state.center = { ...LUONAN_CENTER };
        }
        state.zoom = Math.min(getMapZoomLimits().max, 10);
        renderBaseMap();
        toast("已聚焦到当前评估范围");
    }

    function updateMapControls() {
        if (state.leafletMap) {
            const zoom = state.leafletMap.getZoom();
            const limits = getMapZoomLimits();
            state.zoom = zoom;
            $("map-zoom-label").textContent = `Z ${zoom}`;
            $("zoom-in").disabled = zoom >= limits.max;
            $("zoom-out").disabled = zoom <= limits.min;
            return;
        }
        const limits = getMapZoomLimits();
        const zoom = clamp(Number(state.zoom) || limits.max, limits.min, limits.max);
        state.zoom = zoom;
        const label = $("map-zoom-label");
        if (label) label.textContent = `Z ${zoom}`;
        const zoomIn = $("zoom-in");
        const zoomOut = $("zoom-out");
        if (zoomIn) zoomIn.disabled = zoom >= limits.max;
        if (zoomOut) zoomOut.disabled = zoom <= limits.min;
    }

    function setMapZoom(nextZoom) {
        if (state.leafletMap) {
            const limits = getMapZoomLimits();
            state.leafletMap.setZoom(clamp(nextZoom, limits.min, limits.max));
            return;
        }
        const limits = getMapZoomLimits();
        state.zoom = clamp(nextZoom, limits.min, limits.max);
        renderBaseMap();
    }

    function buildTileUrl(config, mapName) {
        return `${config.service_url}/maps/${encodeURIComponent(mapName)}/zxyTileImage.png?z={z}&x={x}&y={y}&width=256&height=256`;
    }

    function populateBasemapSelector() {
        const select = $("basemap-select");
        const basemaps = state.basemaps || [ESRI_BASEMAP];
        if (!select) return;

        const options = [];
        basemaps.forEach((basemap) => {
            const option = document.createElement("option");
            option.value = basemap.id;
            option.textContent = basemap.name;
            options.push(option);
        });
        select.replaceChildren(...options);
        select.value = state.basemapConfig?.id || ESRI_BASEMAP.id;
        select.disabled = options.length === 0;
    }

    async function changeBasemap(value) {
        let basemap = state.basemaps.find((item) => item.id === value);
        if (!basemap || !state.leafletMap) return;
        if (basemap.type === "iserver" && !basemap.tile_url) {
            const response = await authedFetch(`${API}/api/map-services/${encodeURIComponent(basemap.service_name)}/tile-config?map_name=${encodeURIComponent(basemap.map_name)}`);
            if (!response.ok) throw new Error("无法读取 iServer 瓦片配置");
            basemap = { ...basemap, ...await response.json() };
            state.basemaps = state.basemaps.map((item) => item.id === basemap.id ? basemap : item);
        }
        const minZoom = Number(basemap.min_zoom ?? 0);
        const maxZoom = Number(basemap.max_zoom ?? 19);
        state.leafletMap.setMinZoom(minZoom);
        state.leafletMap.setMaxZoom(maxZoom);
        if (state.leafletMap.getZoom() > maxZoom) state.leafletMap.setZoom(maxZoom);
        if (state.leafletMap.getZoom() < minZoom) state.leafletMap.setZoom(minZoom);
        if (state.leafletBasemap) state.leafletMap.removeLayer(state.leafletBasemap);
        state.leafletBasemap = L.tileLayer(basemap.tile_url, {
            attribution: basemap.attribution || "",
            minZoom,
            maxZoom,
        }).addTo(state.leafletMap);
        state.leafletBasemap.bringToBack();
        state.basemapConfig = basemap;
        updateMapControls();
        toast(`已切换至 ${basemap.name}`);
    }

    function beginDrawMode() {
        if (!state.mapEl) return;
        state.drawing = true;
        state.drawStart = null;
        state.previewBoundary = null;
        state.mapEl.classList.add("is-drawing");
        state.leafletMap?.dragging.disable();
        $("boundary-status").querySelector("span").textContent = "请在地图上拖拽绘制矩形";
        toast("拖拽地图区域生成边界");
    }

    function previewMapPan(dx, dy) {
        if (!state.mapEl) return;
        state.mapEl.style.setProperty("--pan-x", `${dx}px`);
        state.mapEl.style.setProperty("--pan-y", `${dy}px`);
    }

    function clearMapPanPreview() {
        if (!state.mapEl) return;
        state.mapEl.style.removeProperty("--pan-x");
        state.mapEl.style.removeProperty("--pan-y");
    }

    function endDrawMode() {
        state.drawing = false;
        state.drawStart = null;
        state.drawPointerId = null;
        state.mapEl?.classList.remove("is-drawing");
        state.leafletMap?.dragging.enable();
    }

    function installDrawHandlers() {
        if (!state.mapEl) return;

        const onPointerMove = (event) => {
            if (state.panStart && event.pointerId === state.panStart.pointerId) {
                const dx = event.clientX - state.panStart.x;
                const dy = event.clientY - state.panStart.y;
                const startCenter = lonLatToWorldPixel(
                    state.panStart.center.lon,
                    state.panStart.center.lat,
                    state.panStart.zoom,
                );
                const [lon, lat] = worldPixelToLonLat(
                    startCenter.x - dx,
                    startCenter.y - dy,
                    state.panStart.zoom,
                );
                state.center = { lon, lat };
                previewMapPan(dx, dy);
                return;
            }
            if (!state.drawing || !state.drawStart || event.pointerId !== state.drawPointerId) return;
            const rect = state.mapEl.getBoundingClientRect();
            const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
            const y = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
            const current = pointToLonLat(x, y, rect.width, rect.height);
            state.previewBoundary = rectangleGeometryFromPoints(state.drawStart, current);
            renderBoundary();
        };

        const onPointerUp = (event) => {
            if (state.panStart && event.pointerId === state.panStart.pointerId) {
                state.panStart = null;
                state.mapEl?.classList.remove("is-panning");
                clearMapPanPreview();
                renderBaseMap();
                return;
            }
            if (!state.drawing || event.pointerId !== state.drawPointerId) return;
            const rect = state.mapEl.getBoundingClientRect();
            const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
            const y = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
            const current = pointToLonLat(x, y, rect.width, rect.height);
            if (state.drawStart) {
                const geom = rectangleGeometryFromPoints(state.drawStart, current);
                setBoundary(geom, "已绘制评估范围");
                toast("边界已更新");
            }
            endDrawMode();
            renderBoundary();
        };

        state.mapEl.addEventListener("pointerdown", (event) => {
            const rect = state.mapEl.getBoundingClientRect();
            if (!state.drawing) {
                state.panStart = {
                    pointerId: event.pointerId,
                    x: event.clientX,
                    y: event.clientY,
                    zoom: state.zoom,
                    center: { ...state.center },
                };
                state.mapEl.setPointerCapture(event.pointerId);
                state.mapEl.classList.add("is-panning");
                return;
            }
            const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
            const y = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
            state.drawStart = pointToLonLat(x, y, rect.width, rect.height);
            state.drawPointerId = event.pointerId;
            state.mapEl.setPointerCapture(event.pointerId);
            state.previewBoundary = null;
            renderBoundary();
        });

        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
        window.addEventListener("pointercancel", onPointerUp);
        window.addEventListener("resize", renderBaseMap);
        state.mapEl.addEventListener("wheel", (event) => {
            event.preventDefault();
            setMapZoom(state.zoom + (event.deltaY < 0 ? 1 : -1));
        }, { passive: false });
    }

    function installLeafletDrawHandlers() {
        const map = state.leafletMap;
        if (!map) return;
        let drawStart = null;

        map.on("mousedown", (event) => {
            if (!state.drawing) return;
            drawStart = event.latlng;
            state.previewBoundary = null;
        });
        map.on("mousemove", (event) => {
            if (!state.drawing || !drawStart) return;
            state.previewBoundary = rectangleGeometryFromPoints(
                [drawStart.lng, drawStart.lat],
                [event.latlng.lng, event.latlng.lat],
            );
            renderBoundary();
        });
        map.on("mouseup", (event) => {
            if (!state.drawing || !drawStart) return;
            const geometry = rectangleGeometryFromPoints(
                [drawStart.lng, drawStart.lat],
                [event.latlng.lng, event.latlng.lat],
            );
            drawStart = null;
            setBoundary(geometry, "已绘制评估范围");
            endDrawMode();
            toast("边界已更新");
        });
    }

    async function loadUserBasemaps() {
        state.basemaps = [ESRI_BASEMAP];
        if (!window.Auth?.getToken()) {
            populateBasemapSelector();
            return;
        }
        try {
            const response = await authedFetch(`${API}/api/map-services/list`);
            if (!response.ok) throw new Error("无法读取 iServer 地图服务");
            const payload = await response.json();
            (payload.services || []).forEach((service) => {
                (service.maps || []).forEach((mapName) => {
                    state.basemaps.push({
                        id: `iserver:${service.service_name}:${mapName}`,
                        name: `iServer · ${mapName}`,
                        type: "iserver",
                        service_name: service.service_name,
                        map_name: mapName,
                    });
                });
            });
        } catch (error) {
            toast(error instanceof Error ? error.message : "iServer 底图列表加载失败", "error");
        }
        populateBasemapSelector();
    }

    function initFallbackMap() {
        state.mapEl = $("map");
        if (window.L) {
            state.leafletMap = L.map(state.mapEl, { zoomControl: false, attributionControl: true })
                .setView([LUONAN_CENTER.lat, LUONAN_CENTER.lon], 11);
            state.basemapConfig = ESRI_BASEMAP;
            state.leafletBasemap = L.tileLayer(ESRI_BASEMAP.tile_url, {
                attribution: ESRI_BASEMAP.attribution,
                minZoom: ESRI_BASEMAP.min_zoom,
                maxZoom: ESRI_BASEMAP.max_zoom,
            }).addTo(state.leafletMap);
            state.leafletMap.on("zoomend", updateMapControls);
            state.leafletMap.on("moveend", () => {
                const center = state.leafletMap.getCenter();
                state.center = { lon: center.lng, lat: center.lat };
            });
            installLeafletDrawHandlers();
            setBoundary(SAMPLE_BOUNDARY, "使用洛南候选范围");
            populateBasemapSelector();
            updateMapControls();
            return;
        }
        renderBaseMap();
        installDrawHandlers();
        setBoundary(SAMPLE_BOUNDARY, "使用洛南候选范围");
    }

    async function loadCapabilities() {
        setChip("iserver-chip", "iServer 检测中", "is-warning");
        setChip("scene-chip", "3D 检测中", "is-warning");
        try {
            const response = await fetch(`${API}/api/land-assessment/capabilities`);
            if (!response.ok) throw new Error(`能力接口返回 ${response.status}`);
            const caps = await response.json();
            state.capabilities = caps;

            setChip("iserver-chip", caps.iServer ? "iServer 在线" : "iServer 离线", caps.iServer ? "is-online" : "is-offline");
            setChip("scene-chip", `${caps["3d_scenes"]?.length || 0} 个 3D 场景`, caps["3d_scenes"]?.length ? "is-online" : "is-warning");
            setCapability("cap-overlay", caps.spatial_analyst ? "可调用" : "未发布");
            setCapability("cap-dem", caps.land_layers?.water?.length && caps.land_layers?.roads?.length ? "已发布" : "未发布");
            setCapability("cap-raster", caps.dem_available ? "可调用" : "未发布");
            setCapability("cap-scenes", caps.realspace_available ? "可调用" : "未发布");
            const view3d = $("view-3d");
            view3d.disabled = !caps.realspace_available;
            view3d.title = caps.realspace_available ? "三维视图" : "未发布 Realspace 三维服务";
            if (!caps.realspace_available && state.mode === "3d") setView("2d");
            await loadUserBasemaps();

        } catch (error) {
            setChip("iserver-chip", "iServer 未知", "is-offline");
            setChip("scene-chip", "3D 未知", "is-offline");
            setCapability("cap-overlay", "未知");
            setCapability("cap-dem", "未知");
            setCapability("cap-raster", "未知");
            setCapability("cap-scenes", "未知");
            toast(error instanceof Error ? error.message : "能力检测失败", "error");
        }
    }
    function buildRequest(options = state.analysisOptions) {
        const constraintDatasets = (options.constraint_datasets || "")
            .split(",")
            .map((name) => name.trim())
            .filter(Boolean);
        const roadDatasource = (options.road_datasource || "").trim();
        const roadDataset = (options.road_dataset || "").trim();
        return {
            boundary: state.boundary,
            target_use: options.target_use || "general",
            buffer_distance_m: Number(options.buffer_distance_m) || 0,
            use_3d: Boolean(options.use_3d),
            scene_name: options.scene_name || null,
            weights: options.weights,
            constraint_datasets: constraintDatasets.length ? constraintDatasets : null,
            accessibility_layers: roadDatasource && roadDataset
                ? [{ datasource_name: roadDatasource, dataset_name: roadDataset, label: "道路", kind: "road", weight: 1 }]
                : null,
        };
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&#39;",
            '"': "&quot;",
        })[char]);
    }

    function fieldMarkup(id, label, value, options = {}) {
        const type = options.type || "text";
        const attributes = [
            `id="${id}"`,
            `type="${type}"`,
            `value="${escapeHtml(value)}"`,
        ];
        if (options.placeholder) attributes.push(`placeholder="${escapeHtml(options.placeholder)}"`);
        if (options.min !== undefined) attributes.push(`min="${options.min}"`);
        if (options.max !== undefined) attributes.push(`max="${options.max}"`);
        if (options.step !== undefined) attributes.push(`step="${options.step}"`);
        return `<label class="field"><span>${label}</span><input ${attributes.join(" ")}></label>`;
    }

    function targetUseMarkup(value) {
        const options = [
            ["general", "综合用地"],
            ["agriculture", "农业利用"],
            ["construction", "建设适宜"],
            ["ecology", "生态保护"],
        ];
        return `<label class="field"><span>目标用途</span><select id="dialog-target-use">${options
            .map(([key, label]) => `<option value="${key}"${key === value ? " selected" : ""}>${label}</option>`)
            .join("")}</select></label>`;
    }

    function sceneMarkup(value) {
        const scenes = state.capabilities?.["3d_scenes"] || [];
        const options = [['', '自动选择']].concat(scenes.map((scene) => [
            scene.scene_name || scene.service_name,
            scene.scene_name || scene.service_name,
        ]));
        return `<label class="field"><span>三维场景</span><select id="dialog-scene-name">${options
            .map(([key, label]) => `<option value="${escapeHtml(key)}"${key === value ? " selected" : ""}>${escapeHtml(label)}</option>`)
            .join("")}</select></label>`;
    }

    function processingField(id, label, value, options = {}) {
        return fieldMarkup(`processing-${id}`, label, value, options);
    }

    function buildProcessingDialogContent(action) {
        const options = state.processingOptions;
        const source = `<div class="dialog-grid">${processingField("datasource", "数据源", options.datasource, { placeholder: "例如 China100" })}${processingField("dataset", "输入数据集", options.dataset, { placeholder: "iServer 已发布数据集" })}</div>`;
        if (action === "terrain_slope") {
            return `${source}<div class="dialog-grid"><label class="field"><span>坡度单位</span><select id="processing-slope-type"><option value="DEGREE">度（DEGREE）</option><option value="PERCENT_RISE">百分比（PERCENT_RISE）</option></select></label>${processingField("z-factor", "高程系数", options.z_factor, { type: "number", min: 0.0001, step: 0.1 })}</div>`;
        }
        if (action === "terrain_aspect") return source;
        if (action === "terrain_hillshade") {
            return `${source}<div class="dialog-grid">${processingField("azimuth", "光源方位角（°）", options.azimuth, { type: "number", min: 0, max: 360, step: 1 })}${processingField("altitude", "光源高度角（°）", options.altitude, { type: "number", min: 0, max: 90, step: 1 })}</div>`;
        }
        if (action === "density_kernel") {
            return `${source}<div class="dialog-grid">${processingField("search-radius", "搜索半径（m）", options.search_radius, { type: "number", min: 1, step: 1 })}${processingField("cell-size", "像元大小（m）", options.cell_size, { type: "number", min: 1, step: 1 })}</div>${processingField("population-field", "权重字段", options.population_field, { placeholder: "可选" })}`;
        }
        if (action === "density_point") {
            return `${source}<div class="dialog-grid">${processingField("cell-size", "像元大小（m）", options.cell_size, { type: "number", min: 1, step: 1 })}${processingField("search-radius", "搜索半径（m）", options.search_radius, { type: "number", min: 1, step: 1 })}</div>${processingField("population-field", "权重字段", options.population_field, { placeholder: "可选" })}`;
        }
        if (action === "overlay_weighted") {
            return `${processingField("datasource", "数据源", options.datasource, { placeholder: "例如 China100" })}${processingField("output-dataset", "输出数据集", options.output_dataset, { placeholder: "可选" })}<label class="field"><span>叠加图层 JSON</span><textarea id="processing-layers-json" rows="7" spellcheck="false">${escapeHtml(options.layers_json)}</textarea></label>`;
        }
        const interpolation = `${source}<div class="dialog-grid">${processingField("z-field", "数值字段", options.z_field, { placeholder: "例如 elevation" })}${processingField("cell-size", "像元大小（m）", options.cell_size, { type: "number", min: 1, step: 1 })}</div>`;
        if (action === "interpolation_idw") {
            return `${interpolation}<div class="dialog-grid">${processingField("power", "距离幂次", options.power, { type: "number", min: 0.1, step: 0.1 })}${processingField("search-radius", "搜索半径（m）", options.search_radius, { type: "number", min: 1, step: 1 })}</div>`;
        }
        return `${interpolation}<label class="field"><span>变异函数</span><select id="processing-variogram-type"><option value="SPHERICAL">球状（SPHERICAL）</option><option value="EXPONENTIAL">指数（EXPONENTIAL）</option><option value="GAUSSIAN">高斯（GAUSSIAN）</option><option value="LINEAR">线性（LINEAR）</option></select></label>`;
    }

    function buildDialogContent(action) {
        if (PROCESSING_TOOLS[action]) return buildProcessingDialogContent(action);
        const options = state.analysisOptions;
        const targetUse = targetUseMarkup(options.target_use);
        const bufferDistance = fieldMarkup("dialog-buffer-distance", "缓冲距离（m）", options.buffer_distance_m, { type: "number", min: 0, max: 5000, step: 100 });
        const constraints = fieldMarkup("dialog-constraint-datasets", "约束图层", options.constraint_datasets, { placeholder: "数据集名称，逗号分隔" });
        const roads = `<div class="dialog-grid">${fieldMarkup("dialog-road-datasource", "道路数据源", options.road_datasource, { placeholder: "数据源" })}${fieldMarkup("dialog-road-dataset", "道路数据集", options.road_dataset, { placeholder: "数据集" })}</div>`;
        const threeD = `<div class="dialog-section"><label class="dialog-toggle"><input id="dialog-use-3d" type="checkbox"${options.use_3d ? " checked" : ""}><span>启用 3D 场景核验</span></label>${sceneMarkup(options.scene_name)}</div>`;

        if (action === "land_summary" || action === "admin_context") return "无需额外参数，直接使用当前评估范围。";
        if (action === "water_constraint") return constraints;
        if (action === "buffer") return bufferDistance;
        if (action === "road_access") return roads;

        return `
            ${targetUse}
            <section class="dialog-section"><h3 class="dialog-section-title">空间分析</h3>${bufferDistance}${constraints}${roads}</section>
            <section class="dialog-section"><h3 class="dialog-section-title">因子权重</h3><div class="weight-grid">
                ${fieldMarkup("dialog-weight-terrain", "地形", options.weights.terrain, { type: "number", min: 0, max: 1, step: 0.01 })}
                ${fieldMarkup("dialog-weight-constraint", "约束", options.weights.constraint, { type: "number", min: 0, max: 1, step: 0.01 })}
                ${fieldMarkup("dialog-weight-accessibility", "可达", options.weights.accessibility, { type: "number", min: 0, max: 1, step: 0.01 })}
                ${fieldMarkup("dialog-weight-ecology", "生态", options.weights.ecology, { type: "number", min: 0, max: 1, step: 0.01 })}
            </div></section>
            ${threeD}`;
    }

    function readDialogValue(id, fallback = "") {
        return $(id)?.value ?? fallback;
    }

    function collectDialogOptions() {
        const previous = state.analysisOptions;
        const next = {
            ...previous,
            target_use: readDialogValue("dialog-target-use", previous.target_use),
            buffer_distance_m: Number(readDialogValue("dialog-buffer-distance", previous.buffer_distance_m)) || 0,
            constraint_datasets: readDialogValue("dialog-constraint-datasets", previous.constraint_datasets).trim(),
            road_datasource: readDialogValue("dialog-road-datasource", previous.road_datasource).trim(),
            road_dataset: readDialogValue("dialog-road-dataset", previous.road_dataset).trim(),
            scene_name: readDialogValue("dialog-scene-name", previous.scene_name),
            use_3d: $("dialog-use-3d") ? $("dialog-use-3d").checked : previous.use_3d,
            weights: {
                terrain: Number(readDialogValue("dialog-weight-terrain", previous.weights.terrain)) || 0,
                constraint: Number(readDialogValue("dialog-weight-constraint", previous.weights.constraint)) || 0,
                accessibility: Number(readDialogValue("dialog-weight-accessibility", previous.weights.accessibility)) || 0,
                ecology: Number(readDialogValue("dialog-weight-ecology", previous.weights.ecology)) || 0,
            },
        };
        state.analysisOptions = next;
        return next;
    }

    function collectProcessingOptions(action) {
        const get = (id, fallback = "") => readDialogValue(`processing-${id}`, fallback).trim();
        const numeric = (id, fallback) => Number(readDialogValue(`processing-${id}`, fallback));
        const next = {
            ...state.processingOptions,
            datasource: get("datasource", state.processingOptions.datasource),
            dataset: get("dataset", state.processingOptions.dataset),
            slope_type: readDialogValue("processing-slope-type", state.processingOptions.slope_type),
            z_factor: numeric("z-factor", state.processingOptions.z_factor),
            azimuth: numeric("azimuth", state.processingOptions.azimuth),
            altitude: numeric("altitude", state.processingOptions.altitude),
            search_radius: numeric("search-radius", state.processingOptions.search_radius),
            cell_size: numeric("cell-size", state.processingOptions.cell_size),
            population_field: get("population-field", state.processingOptions.population_field),
            z_field: get("z-field", state.processingOptions.z_field),
            power: numeric("power", state.processingOptions.power),
            variogram_type: readDialogValue("processing-variogram-type", state.processingOptions.variogram_type),
            output_dataset: get("output-dataset", state.processingOptions.output_dataset),
            layers_json: readDialogValue("processing-layers-json", state.processingOptions.layers_json),
        };
        state.processingOptions = next;
        const base = { datasource: next.datasource, dataset: next.dataset };
        if (action === "terrain_slope") return { ...base, slope_type: next.slope_type, z_factor: next.z_factor };
        if (action === "terrain_aspect") return base;
        if (action === "terrain_hillshade") return { ...base, azimuth: next.azimuth, altitude: next.altitude };
        if (action === "density_kernel") return { ...base, search_radius: next.search_radius, cell_size: next.cell_size || null, population_field: next.population_field || null };
        if (action === "density_point") return { ...base, cell_size: next.cell_size, search_radius: next.search_radius, population_field: next.population_field || null };
        if (action === "interpolation_idw") return { ...base, z_field: next.z_field, cell_size: next.cell_size, power: next.power, search_radius: next.search_radius || null };
        if (action === "interpolation_kriging") return { ...base, z_field: next.z_field, cell_size: next.cell_size, variogram_type: next.variogram_type };
        try {
            const layers = JSON.parse(next.layers_json);
            if (!Array.isArray(layers) || !layers.length) throw new Error("至少需要一个图层");
            return { datasource: next.datasource, layers, output_dataset: next.output_dataset || null };
        } catch (error) {
            throw new Error(`叠加图层 JSON 无效：${error.message}`);
        }
    }

    function openAnalysisDialog(action) {
        const dialog = $("analysis-dialog");
        const tool = ALL_ANALYSIS_TOOLS[action];
        state.activeAnalysis = action;
        $("analysis-dialog-title").textContent = action === "evaluate" ? "综合评价" : tool.label;
        $("analysis-dialog-submit").querySelector("span").textContent = action === "evaluate" ? "生成结论" : "运行分析";
        $("analysis-dialog-body").innerHTML = buildDialogContent(action);
        if (dialog.open) dialog.close();
        dialog.showModal();
    }

    function factorLabel(name) {
        return {
            terrain: "地形",
            constraint: "约束",
            accessibility: "可达性",
            ecology: "生态",
        }[name] || name;
    }

    function renderFactors(factors) {
        const list = $("factor-list");
        if (!list) return;
        if (!Array.isArray(factors) || !factors.length) {
            list.innerHTML = '<div class="empty-state">暂无结果</div>';
            return;
        }
        list.replaceChildren(...factors.map((factor) => {
            const item = document.createElement("div");
            const score = Math.max(0, Math.min(100, Number(factor.score) || 0));
            item.className = "factor-item";
            item.innerHTML = `
                <strong>${factorLabel(factor.name)}</strong>
                <span class="factor-track"><span class="factor-fill" style="--value:${score}%"></span></span>
                <span>${score.toFixed(1)}</span>
            `;
            const fill = item.querySelector(".factor-fill");
            if (fill) fill.style.width = `${score}%`;
            return item;
        }));
    }

    function renderRecommendations(items) {
        const list = $("recommendation-list");
        if (!list) return;
        const recommendations = Array.isArray(items) && items.length ? items : ["暂无建议。"];
        list.replaceChildren(...recommendations.map((text) => {
            const li = document.createElement("li");
            li.textContent = text;
            return li;
        }));
    }

    function renderResult(result) {
        const score = Number(result.overall_score) || 0;
        $("score-ring").style.setProperty("--score", String(Math.max(0, Math.min(100, score))));
        $("overall-score").textContent = score ? score.toFixed(1) : "--";
        $("grade-label").textContent = result.grade ? `等级 ${result.grade}` : "未评估";
        $("decision-text").textContent = result.decision || "完成评估";
        $("summary-text").textContent = result.summary || "";
        $("last-run-id").textContent = result.run_id || "已完成";
        renderRecommendations(result.recommendations);
        renderMapResult("综合评价", score);

        const report = $("report-link");
        if (result.report_path) {
            report.href = `/api/land-assessment/runs/${result.run_id}/report`;
            report.classList.remove("is-disabled");
        } else {
            report.href = "#";
            report.classList.add("is-disabled");
        }
    }

    async function runAssessment(options) {
        if (!state.boundary) {
            toast("请先指定评估边界", "error");
            return;
        }

        state.runningTool = "evaluate";
        updateToolButtons();

        try {
            const response = await authedFetch(`${API}/api/land-assessment/evaluate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(buildRequest(options)),
            });
            if (response.status === 401 || response.status === 403) {
                throw new Error("请先登录后再运行评估");
            }
            if (!response.ok) {
                const detail = await response.json().catch(() => ({}));
                throw new Error(detail.detail || `评估接口返回 ${response.status}`);
            }
            const result = await response.json();
            renderResult(result);
            renderMapResult("土地资源证据", null, result.visualization);
            state.assessmentCompleted = true;
            toast("空间证据包已生成");
        } catch (error) {
            toast(error instanceof Error ? error.message : "评估失败", "error");
        } finally {
            state.runningTool = null;
            updateToolButtons();
        }
    }

    function resultColor(score) {
        if (score >= 80) return "#15803d";
        if (score >= 60) return "#d97706";
        return "#b91c1c";
    }

    function renderMapResult(label, score, visualization) {
        if (!state.leafletMap || !state.boundary || !window.L) return;
        if (state.analysisResultLayer) state.leafletMap.removeLayer(state.analysisResultLayer);
        const color = resultColor(Number(score) || 0);
        const labelText = Number.isFinite(Number(score)) ? `${label} ${Number(score).toFixed(1)}` : label;
        const data = visualization?.features?.length ? visualization : state.boundary;
        state.analysisResultLayer = L.geoJSON(data, {
            style: {
                color,
                weight: 3,
                fillColor: color,
                fillOpacity: 0.22,
            },
            onEachFeature(feature, layer) {
                const properties = feature?.properties || {};
                const name = properties.NAME || properties.Name || properties.name || properties.NAMECHN;
                if (name) layer.bindTooltip(String(name), { sticky: true });
            },
            onEachFeature(feature, layer) {
                const name = feature?.properties?.administrative_name;
                if (name) layer.bindPopup(`行政区：${escapeHtml(name)}`);
            },
        }).addTo(state.leafletMap);
        state.analysisResultLayer.bindTooltip(labelText, {
            permanent: true,
            direction: "center",
            className: "analysis-result-tooltip",
        });
    }

    function getToolDetail(tool, payload) {
        const result = payload?.result || {};
        return result[tool.resultKey] || {};
    }

    function formatToolMetric(key, value, unit) {
        if (key === "enabled") return value ? "已启用" : "未启用";
        if (key === "administrative_names") return Array.isArray(value) && value.length ? value.join("、") : "--";
        if (Array.isArray(value)) return `${value.length} ${unit}`.trim();
        const number = Number(value);
        if (!Number.isFinite(number)) return "--";
        if (key.endsWith("_ratio") || key.endsWith("_pct")) return `${formatNumber(number * (key.endsWith("_ratio") ? 100 : 1), 1)}%`;
        return `${formatNumber(number, 1)}${unit ? ` ${unit}` : ""}`;
    }

    function renderStageResults() {
        const container = $("stage-result-list");
        const counter = $("tool-run-count");
        const completed = Object.values(state.toolResults);
        const toolCount = getPinnedToolIds().length;
        if (counter) counter.textContent = `${completed.length} / ${toolCount}`;
        if (!container) return;
        if (!completed.length) {
            container.innerHTML = '<div class="empty-state stage-empty"><i class="fa-solid fa-chart-column"></i><span>尚未运行分析工具</span></div>';
            return;
        }

        const cards = Object.entries(state.toolResults)
            .sort(([, left], [, right]) => right.completedAt - left.completedAt)
            .map(([id, result]) => {
                const tool = ALL_ANALYSIS_TOOLS[id];
                const detail = result.detail;
                const score = Number(detail.score);
                const card = document.createElement("article");
                card.className = "stage-result-card";

                const heading = document.createElement("div");
                heading.className = "stage-result-heading";
                const title = document.createElement("strong");
                const status = document.createElement("span");
                title.textContent = tool.label;
                status.textContent = Number.isFinite(score) ? score.toFixed(1) : "已完成";
                heading.append(title, status);

                const source = document.createElement("p");
                source.className = "stage-source";
                source.textContent = detail.source || tool.sourceLabel;
                card.append(heading, source);

                if (Number.isFinite(score)) {
                    const track = document.createElement("span");
                    const fill = document.createElement("span");
                    track.className = "stage-score-track";
                    fill.className = "stage-score-fill";
                    fill.style.width = `${Math.max(0, Math.min(100, score))}%`;
                    track.append(fill);
                    card.append(track);
                }

                const metrics = (tool.metrics || [])
                    .map(([key, label, unit]) => ({ key, label, value: detail[key], unit }))
                    .filter((metric) => metric.value !== undefined && metric.value !== null);
                if (metrics.length) {
                    const grid = document.createElement("dl");
                    grid.className = "stage-metrics";
                    metrics.forEach((metric) => {
                        const item = document.createElement("div");
                        const term = document.createElement("dt");
                        const definition = document.createElement("dd");
                        term.textContent = metric.label;
                        definition.textContent = formatToolMetric(metric.key, metric.value, metric.unit);
                        item.append(term, definition);
                        grid.append(item);
                    });
                    card.append(grid);
                }

                if (detail.note) {
                    const note = document.createElement("p");
                    note.className = "stage-note";
                    note.textContent = detail.note;
                    card.append(note);
                }
                return card;
            });
        container.replaceChildren(...cards);
        container.scrollTop = 0;
    }

    function renderStageFactors() {
        const factors = Object.entries(state.toolResults)
            .map(([id, item]) => ({ id, tool: ALL_ANALYSIS_TOOLS[id], detail: item.detail }))
            .filter((item) => item.tool.factor && Number.isFinite(Number(item.detail.score)))
            .map((item) => ({
                name: item.tool.factor,
                score: Number(item.detail.score),
                source: item.detail.source || item.tool.sourceLabel,
            }));
        renderFactors(factors);
    }

    function updateToolButtons() {
        document.querySelectorAll("[data-tool]").forEach((button) => {
            const id = button.dataset.tool;
            const completed = Boolean(state.toolResults[id]);
            button.classList.toggle("is-complete", completed);
            button.classList.toggle("is-running", state.runningTool === id);
            button.disabled = state.runningTool === id;
        });
    }

    function updateAssessmentScope() {
        const scope = $("assessment-scope");
        if (!scope) return;
        const completed = Object.keys(state.toolResults).length;
        scope.textContent = `${completed} / ${getPinnedToolIds().length} 个分析工具已完成`;
    }

    function clearWorkflow() {
        state.toolResults = {};
        state.runningTool = null;
        state.assessmentCompleted = false;
        if (state.analysisResultLayer && state.leafletMap) {
            state.leafletMap.removeLayer(state.analysisResultLayer);
            state.analysisResultLayer = null;
        }
        renderStageResults();
        updateToolButtons();
        updateAssessmentScope();
        toast("已清除阶段成果");
    }

    async function runTool(toolId, options) {
        if (PROCESSING_TOOLS[toolId]) {
            await runProcessingTool(toolId, options);
            return;
        }
        if (!state.boundary) {
            toast("请先指定评估边界", "error");
            return;
        }
        const tool = ALL_ANALYSIS_TOOLS[toolId];
        if (!tool) return;
        state.runningTool = toolId;
        updateToolButtons();
        try {
            const response = await authedFetch(`${API}/api/land-assessment/diagnostics/${tool.component}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(buildRequest(options)),
            });
            if (response.status === 401 || response.status === 403) {
                throw new Error("请先登录后再运行专题诊断");
            }
            if (!response.ok) {
                const detail = await response.json().catch(() => ({}));
                throw new Error(detail.detail || `诊断接口返回 ${response.status}`);
            }
            const payload = await response.json();
            const detail = getToolDetail(tool, payload);
            if (!Object.keys(detail).length) throw new Error("分析接口未返回可展示结果");
            state.toolResults[toolId] = { detail, completedAt: Date.now() };
            renderMapResult(tool.label, detail.score, payload.visualization || detail.visualization);
            renderStageResults();
            updateAssessmentScope();
            toast(`${tool.label}完成`);
        } catch (error) {
            toast(error instanceof Error ? error.message : "分析工具调用失败", "error");
        } finally {
            state.runningTool = null;
            updateToolButtons();
        }
    }

    async function runProcessingTool(toolId, parameters) {
        const tool = PROCESSING_TOOLS[toolId];
        if (!tool) return;
        if (!parameters?.datasource || (toolId !== "overlay_weighted" && !parameters?.dataset)) {
            toast("请填写 iServer 数据源和输入数据集", "error");
            return;
        }
        state.runningTool = toolId;
        updateToolButtons();
        try {
            const response = await authedFetch(`${API}${tool.endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(parameters),
            });
            if (response.status === 401 || response.status === 403) throw new Error("请先登录后再运行 iServer 分析");
            if (!response.ok) {
                const detail = await response.json().catch(() => ({}));
                throw new Error(detail.detail || `分析接口返回 ${response.status}`);
            }
            const payload = await response.json();
            state.toolResults[toolId] = {
                completedAt: Date.now(),
                detail: {
                    source: tool.sourceLabel,
                    result_id: payload.result_id || payload.result?.newResourceID || "--",
                    note: payload.message || "iServer 已生成处理结果。",
                },
            };
            renderStageResults();
            updateAssessmentScope();
            toast(`${tool.label}完成`);
        } catch (error) {
            toast(error instanceof Error ? error.message : "iServer 地理处理失败", "error");
        } finally {
            state.runningTool = null;
            updateToolButtons();
        }
    }
    function setView(mode) {
        if (mode === "3d" && !state.capabilities?.realspace_available) {
            toast("当前 iServer 未发布 Realspace 三维服务", "error");
            return;
        }
        const is3d = mode === "3d";
        state.mode = mode;
        document.body.classList.toggle("is-3d", is3d);
        $("view-2d").classList.toggle("is-active", !is3d);
        $("view-3d").classList.toggle("is-active", is3d);
    }

    function bindEvents() {
        $("open-decision-agent").addEventListener("click", () => {
            $("decision-agent").classList.add("is-open");
            $("decision-agent").setAttribute("aria-hidden", "false");
        });
        $("close-decision-agent").addEventListener("click", () => {
            $("decision-agent").classList.remove("is-open");
            $("decision-agent").setAttribute("aria-hidden", "true");
        });
        $("agent-form").addEventListener("submit", (event) => {
            event.preventDefault();
            sendToDecisionAgent();
        });
        document.querySelectorAll("[data-agent-prompt]").forEach((button) => {
            button.addEventListener("click", () => sendToDecisionAgent(button.dataset.agentPrompt));
        });
        $("refresh-capabilities").addEventListener("click", loadCapabilities);
        $("reset-workflow").addEventListener("click", clearWorkflow);
        $("login-link").addEventListener("click", () => {
            if (window.Auth?.getToken()) window.Auth.logout();
            else window.location.href = "login.html";
        });
        $("draw-boundary").addEventListener("click", () => beginDrawMode());
        $("use-sample-boundary").addEventListener("click", () => setBoundary(SAMPLE_BOUNDARY, "使用洛南候选范围"));
        $("clear-boundary").addEventListener("click", () => {
            state.boundary = null;
            state.previewBoundary = null;
            $("boundary-status").querySelector("span").textContent = "未指定";
            renderBoundary();
        });
        $("focus-map").addEventListener("click", fitBoundary);
        $("reset-map").addEventListener("click", () => {
            endDrawMode();
            state.previewBoundary = null;
            $("boundary-status").querySelector("span").textContent = state.boundary
                ? "当前评估范围"
                : "未指定";
            state.center = { ...LUONAN_CENTER };
            state.zoom = 11;
            if (state.leafletMap) state.leafletMap.setView([LUONAN_CENTER.lat, LUONAN_CENTER.lon], state.zoom);
            else renderBaseMap();
            toast("已重置地图视图");
        });
        $("draw-boundary-map").addEventListener("click", beginDrawMode);
        $("zoom-in").addEventListener("click", () => setMapZoom(state.zoom + 1));
        $("zoom-out").addEventListener("click", () => setMapZoom(state.zoom - 1));
        $("basemap-select").addEventListener("change", (event) => {
            changeBasemap(event.target.value).catch((error) => toast(error instanceof Error ? error.message : "底图切换失败", "error"));
        });
        $("analysis-tool-grid").addEventListener("click", (event) => {
            const button = event.target.closest("[data-tool]");
            if (button) openAnalysisDialog(button.dataset.tool);
        });
        document.querySelectorAll("[data-dialog-close]").forEach((button) => {
            button.addEventListener("click", () => $("analysis-dialog").close());
        });
        $("analysis-dialog").addEventListener("cancel", () => { state.activeAnalysis = null; });
        $("analysis-dialog-form").addEventListener("submit", (event) => {
            event.preventDefault();
            const action = state.activeAnalysis;
            let options;
            try {
                options = PROCESSING_TOOLS[action] ? collectProcessingOptions(action) : collectDialogOptions();
            } catch (error) {
                toast(error instanceof Error ? error.message : "参数无效", "error");
                return;
            }
            $("analysis-dialog").close();
            state.activeAnalysis = null;
            if (action === "evaluate") runAssessment(options);
            else runTool(action, options);
        });
        $("view-2d").addEventListener("click", () => setView("2d"));
        $("view-3d").addEventListener("click", () => {
            if (!state.capabilities?.realspace_available) {
                toast("当前 iServer 未发布 Realspace 三维服务", "error");
                return;
            }
            window.location.href = "map3d.html";
        });
    }

    function initAuthState() {
        const button = $("login-link");
        if (!button) return;
        if (window.Auth?.getToken()) {
            button.querySelector("span").textContent = "退出";
            button.querySelector("i").className = "fa-solid fa-right-from-bracket";
        }
    }

    function init() {
        initFallbackMap();
        renderToolbox();
        bindEvents();
        renderStageResults();
        updateAssessmentScope();
        initAuthState();
        loadCapabilities();
        const requestedTool = new URLSearchParams(window.location.search).get("tool");
        if (requestedTool && ALL_ANALYSIS_TOOLS[requestedTool]) {
            window.history.replaceState({}, "", window.location.pathname);
            openAnalysisDialog(requestedTool);
        }
        window.addEventListener("storage", (event) => {
            if (event.key !== PINNED_TOOLS_KEY) return;
            renderToolbox();
            updateAssessmentScope();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
