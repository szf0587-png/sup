(function () {
    "use strict";

    const PINNED_TOOLS_KEY = "land-resource.pinned-iserver-tools.v1";
    const MAX_PINNED_TOOLS = 6;
    const DEFAULT_PINNED_TOOLS = ["land_summary", "water_constraint", "buffer", "road_access", "admin_context"];
    const WORKBENCH_TOOLS = {
        land_summary: { label: "范围统计", icon: "fa-vector-square", family: "assessment", category: "土地评估", endpoint: "/api/land-assessment/diagnostics/land_summary", description: "统计当前框选边界的近似地理面积。", requirement: "评估边界；可选项目 ID。" },
        water_constraint: { label: "水体约束", icon: "fa-water", family: "assessment", category: "土地评估", endpoint: "/api/land-assessment/diagnostics/water_constraint", description: "查询已发布水面、湖泊与河流图层是否和边界相交。", requirement: "评估边界；可选择参与查询的水体图层。" },
        buffer: { label: "缓冲统计", icon: "fa-circle-notch", family: "assessment", category: "土地评估", endpoint: "/api/land-assessment/diagnostics/buffer", description: "按指定距离生成评估边界的真实 iServer 缓冲区。", requirement: "评估边界、缓冲距离；可选项目 ID。" },
        road_access: { label: "道路空间查询", icon: "fa-road", family: "assessment", category: "土地评估", endpoint: "/api/land-assessment/diagnostics/road_access", description: "查询与评估边界相交的已发布道路要素。", requirement: "评估边界、道路数据源和道路数据集。" },
        admin_context: { label: "行政区定位", icon: "fa-building-columns", family: "assessment", category: "土地评估", endpoint: "/api/land-assessment/diagnostics/admin_context", description: "定位边界所在省级行政区，返回名称并在地图上高亮。", requirement: "评估边界；可选项目 ID。" },
    };
    const TOOLS = {
        terrain_slope: {
            label: "坡度分析", icon: "fa-mountain-sun", family: "terrain", category: "地形分析", endpoint: "/api/spatial-analysis/terrain/slope",
            description: "从已发布 DEM 计算坡度栅格，可选择角度或百分比表达。", requirement: "数据源、DEM 数据集；可选坡度单位与高程系数。",
        },
        terrain_aspect: {
            label: "坡向分析", icon: "fa-compass", family: "terrain", category: "地形分析", endpoint: "/api/spatial-analysis/terrain/aspect",
            description: "从已发布 DEM 计算每个像元的朝向角度。", requirement: "数据源、DEM 数据集。",
        },
        terrain_hillshade: {
            label: "山体阴影", icon: "fa-sun", family: "terrain", category: "地形分析", endpoint: "/api/spatial-analysis/terrain/hillshade",
            description: "以指定光照方位和高度生成地形阴影栅格。", requirement: "数据源、DEM 数据集、光源方位角与高度角。",
        },
        density_kernel: {
            label: "核密度分析", icon: "fa-bullseye", family: "density", category: "密度分析", endpoint: "/api/spatial-analysis/density/kernel",
            description: "根据点要素分布计算连续空间密度表面。", requirement: "数据源、点数据集、搜索半径；可选像元大小和权重字段。",
        },
        density_point: {
            label: "点密度分析", icon: "fa-grip", family: "density", category: "密度分析", endpoint: "/api/spatial-analysis/density/point",
            description: "按邻域统计点要素数量，生成单位面积密度栅格。", requirement: "数据源、点数据集、像元大小、搜索半径；可选权重字段。",
        },
        overlay_weighted: {
            label: "加权叠加", icon: "fa-layer-group", family: "overlay", category: "栅格叠加", endpoint: "/api/spatial-analysis/overlay/weighted",
            description: "对已重分类的栅格因子进行加权组合，支持综合适宜性计算。", requirement: "数据源、图层及权重，所有权重之和必须为 1.0。",
        },
        interpolation_idw: {
            label: "IDW 插值", icon: "fa-chart-area", family: "interpolation", category: "空间插值", endpoint: "/api/spatial-analysis/interpolation/idw",
            description: "利用反距离权重从采样点生成连续预测表面。", requirement: "数据源、点数据集、数值字段、像元大小；可选幂次和搜索半径。",
        },
        interpolation_kriging: {
            label: "Kriging 插值", icon: "fa-wave-square", family: "interpolation", category: "空间插值", endpoint: "/api/spatial-analysis/interpolation/kriging",
            description: "基于变异函数模型从采样点估计连续空间表面。", requirement: "数据源、点数据集、数值字段、像元大小、变异函数类型。",
        },
    };
    const ALL_TOOLS = { ...WORKBENCH_TOOLS, ...TOOLS };
    const defaults = { datasource: "China100", dataset: "", slope_type: "DEGREE", z_factor: 1, azimuth: 315, altitude: 45, search_radius: 1000, cell_size: 100, population_field: "", z_field: "", power: 2, variogram_type: "SPHERICAL", output_dataset: "", layers_json: '[{"dataset":"","weight":1,"reclass_table":[]}]' };
    const state = { filter: "all", activeTool: null, nativeOperation: null, nativeOperations: [], nativeSearch: "", options: { ...defaults }, dragId: null };
    const $ = (id) => document.getElementById(id);

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
        })[char]);
    }

    function toast(message, error = false) {
        const item = document.createElement("div");
        item.className = `toast${error ? " is-error" : ""}`;
        item.textContent = message;
        $("toast-region").append(item);
        window.setTimeout(() => item.remove(), 3600);
    }

    function getPinned() {
        try {
            const parsed = JSON.parse(localStorage.getItem(PINNED_TOOLS_KEY) || "null");
            return Array.isArray(parsed) ? parsed.filter((id) => ALL_TOOLS[id]).slice(0, MAX_PINNED_TOOLS) : [...DEFAULT_PINNED_TOOLS];
        } catch {
            return [...DEFAULT_PINNED_TOOLS];
        }
    }

    function savePinned(ids) {
        localStorage.setItem(PINNED_TOOLS_KEY, JSON.stringify(ids.slice(0, MAX_PINNED_TOOLS)));
        renderDefaultCatalog();
        renderCatalog();
        renderPinned();
    }

    function renderDefaultCatalog() {
        const container = $("default-tool-grid");
        if (!container) return;
        const pinned = getPinned();
        container.replaceChildren(...Object.entries(WORKBENCH_TOOLS).map(([id, tool]) => {
            const isPinned = pinned.includes(id);
            const item = document.createElement("article");
            item.className = "default-tool";
            item.innerHTML = `
                <a class="default-tool-link" href="index.html?tool=${encodeURIComponent(id)}"><i class="fa-solid ${tool.icon}"></i><strong>${tool.label}</strong></a>
                <button class="default-pin${isPinned ? " is-pinned" : ""}" type="button" data-pin="${id}" aria-label="${isPinned ? "取消固定" : "固定到工作台"}" title="${isPinned ? "取消固定" : "固定到工作台"}"><i class="fa-${isPinned ? "solid" : "regular"} fa-bookmark"></i></button>`;
            return item;
        }));
    }

    function renderCatalog() {
        const pinned = getPinned();
        const items = Object.entries(TOOLS).filter(([, tool]) => state.filter === "all" || tool.family === state.filter);
        $("tool-card-grid").replaceChildren(...items.map(([id, tool]) => {
            const isPinned = pinned.includes(id);
            const card = document.createElement("article");
            card.className = "process-card";
            card.innerHTML = `
                <div class="tool-icon"><i class="fa-solid ${tool.icon}"></i></div>
                <div><p class="tool-category">${tool.category}</p><h3>${tool.label}</h3><p class="tool-description">${tool.description}</p><p class="tool-requirement"><strong>参数：</strong>${tool.requirement}</p></div>
                <button class="pin-toggle${isPinned ? " is-pinned" : ""}" type="button" data-pin="${id}" aria-label="${isPinned ? "取消固定" : "固定到工作台"}" title="${isPinned ? "取消固定" : "固定到工作台"}"><i class="fa-${isPinned ? "solid" : "regular"} fa-bookmark"></i></button>
                <footer><span class="api-tag">${tool.endpoint}</span><button class="open-tool" type="button" data-open="${id}">${TOOLS[id] ? "设置参数" : "前往工作台"}</button></footer>
            `;
            return card;
        }));
    }

    function renderPinned() {
        const pinned = getPinned();
        $("pin-count").textContent = `${pinned.length} / ${MAX_PINNED_TOOLS}`;
        const list = $("pinned-list");
        if (!pinned.length) {
            list.innerHTML = '<li class="pin-empty">尚未固定工具</li>';
            return;
        }
        list.replaceChildren(...pinned.map((id) => {
            const tool = ALL_TOOLS[id];
            const item = document.createElement("li");
            item.className = "pinned-item";
            item.draggable = true;
            item.dataset.pinned = id;
            item.innerHTML = `<i class="fa-solid ${tool.icon}"></i><span>${tool.label}</span><button class="unpin" type="button" data-unpin="${id}" aria-label="移除 ${tool.label}" title="移除"><i class="fa-solid fa-xmark"></i></button>`;
            return item;
        }));
    }

    function renderNativeCatalog() {
        const container = $("native-operation-list");
        const counter = $("native-operation-count");
        if (!state.nativeOperations.length) {
            container.innerHTML = '<div class="native-empty">当前服务未返回原生算子目录。</div>';
            if (counter) counter.textContent = "0 个算子";
            return;
        }
        const geometryCount = state.nativeOperations.filter((item) => item.scope === "geometry").length;
        const datasetOperations = state.nativeOperations.filter((item) => item.scope === "dataset");
        const datasetTargetCount = datasetOperations.reduce((total, item) => total + (item.datasets?.length || 0), 0);
        if (counter) counter.textContent = `${geometryCount} 几何 + ${datasetOperations.length} 类数据集（${datasetTargetCount} 数据集实例）`;
        const search = state.nativeSearch.trim().toLowerCase();
        const operations = search
            ? state.nativeOperations.filter((operation) => `${operation.name} ${operation.scope} ${(operation.datasets || []).map((dataset) => dataset.name).join(" ")}`.toLowerCase().includes(search))
            : state.nativeOperations;
        if (!operations.length) {
            container.innerHTML = '<div class="native-empty">没有匹配的 iServer 原生算子</div>';
            return;
        }
        container.replaceChildren(...operations.map((operation) => {
            const item = document.createElement("article");
            item.className = "native-operation";
            item.innerHTML = `<div><strong>${escapeHtml(operation.name)}</strong><small>${operation.scope === "geometry" ? "几何对象" : `${operation.datasets.length} 个可用数据集`}</small></div><button type="button" data-native-open="${escapeHtml(operation.id)}" aria-label="设置 ${escapeHtml(operation.name)} 原生参数" title="设置原生参数"><i class="fa-solid fa-code"></i></button>`;
            return item;
        }));
    }

    async function loadNativeCatalog() {
        try {
            const response = await fetch("/api/spatial-analysis/native-catalog");
            if (!response.ok) throw new Error();
            const payload = await response.json();
            state.nativeOperations = [...(payload.geometry_operations || []), ...(payload.dataset_operations || [])];
            renderNativeCatalog();
        } catch {
            $("native-operation-list").innerHTML = '<div class="native-empty">无法读取 iServer 原生算子目录。</div>';
            $("native-operation-count").textContent = "读取失败";
        }
    }

    function togglePin(id) {
        const pinned = getPinned();
        const index = pinned.indexOf(id);
        if (index >= 0) pinned.splice(index, 1);
        else {
            if (pinned.length >= MAX_PINNED_TOOLS) {
                toast("工作台最多固定 6 个工具，请先移除一个。", true);
                return;
            }
            pinned.push(id);
        }
        savePinned(pinned);
    }

    function field(id, label, value, options = {}) {
        const type = options.type || "text";
        const attrs = [`id="field-${id}"`, `type="${type}"`, `value="${escapeHtml(value)}"`];
        if (options.placeholder) attrs.push(`placeholder="${escapeHtml(options.placeholder)}"`);
        if (options.min !== undefined) attrs.push(`min="${options.min}"`);
        if (options.max !== undefined) attrs.push(`max="${options.max}"`);
        if (options.step !== undefined) attrs.push(`step="${options.step}"`);
        return `<label class="field"><span>${label}</span><input ${attrs.join(" ")}></label>`;
    }

    function sourceFields() {
        return `<div class="field-grid">${field("datasource", "数据源", state.options.datasource, { placeholder: "例如 China100" })}${field("dataset", "输入数据集", state.options.dataset, { placeholder: "iServer 已发布数据集" })}</div>`;
    }

    function buildForm(id) {
        const o = state.options;
        const source = sourceFields();
        if (id === "terrain_slope") return `${source}<div class="field-grid"><label class="field"><span>坡度单位</span><select id="field-slope-type"><option value="DEGREE">度（DEGREE）</option><option value="PERCENT_RISE">百分比（PERCENT_RISE）</option></select></label>${field("z-factor", "高程系数", o.z_factor, { type: "number", min: .0001, step: .1 })}</div>`;
        if (id === "terrain_aspect") return source;
        if (id === "terrain_hillshade") return `${source}<div class="field-grid">${field("azimuth", "光源方位角（°）", o.azimuth, { type: "number", min: 0, max: 360, step: 1 })}${field("altitude", "光源高度角（°）", o.altitude, { type: "number", min: 0, max: 90, step: 1 })}</div>`;
        if (id === "density_kernel") return `${source}<div class="field-grid">${field("search-radius", "搜索半径（m）", o.search_radius, { type: "number", min: 1, step: 1 })}${field("cell-size", "像元大小（m）", o.cell_size, { type: "number", min: 1, step: 1 })}</div>${field("population-field", "权重字段", o.population_field, { placeholder: "可选" })}`;
        if (id === "density_point") return `${source}<div class="field-grid">${field("cell-size", "像元大小（m）", o.cell_size, { type: "number", min: 1, step: 1 })}${field("search-radius", "搜索半径（m）", o.search_radius, { type: "number", min: 1, step: 1 })}</div>${field("population-field", "权重字段", o.population_field, { placeholder: "可选" })}`;
        if (id === "overlay_weighted") return `${field("datasource", "数据源", o.datasource, { placeholder: "例如 China100" })}${field("output-dataset", "输出数据集", o.output_dataset, { placeholder: "可选" })}<label class="field"><span>叠加图层 JSON</span><textarea id="field-layers-json" rows="7" spellcheck="false">${escapeHtml(o.layers_json)}</textarea><span class="field-help">每个图层包含 dataset、weight 和可选 reclass_table；权重总和必须为 1.0。</span></label>`;
        const interpolation = `${source}<div class="field-grid">${field("z-field", "数值字段", o.z_field, { placeholder: "例如 elevation" })}${field("cell-size", "像元大小（m）", o.cell_size, { type: "number", min: 1, step: 1 })}</div>`;
        if (id === "interpolation_idw") return `${interpolation}<div class="field-grid">${field("power", "距离幂次", o.power, { type: "number", min: .1, step: .1 })}${field("search-radius", "搜索半径（m）", o.search_radius, { type: "number", min: 1, step: 1 })}</div>`;
        return `${interpolation}<label class="field"><span>变异函数</span><select id="field-variogram-type"><option value="SPHERICAL">球状（SPHERICAL）</option><option value="EXPONENTIAL">指数（EXPONENTIAL）</option><option value="GAUSSIAN">高斯（GAUSSIAN）</option><option value="LINEAR">线性（LINEAR）</option></select></label>`;
    }

    function openTool(id) {
        if (WORKBENCH_TOOLS[id]) {
            window.location.href = `index.html?tool=${encodeURIComponent(id)}`;
            return;
        }
        const tool = TOOLS[id];
        if (!tool) return;
        state.activeTool = id;
        state.nativeOperation = null;
        $("process-family").textContent = tool.category;
        $("process-dialog-title").textContent = tool.label;
        $("process-body").innerHTML = buildForm(id);
        const dialog = $("process-dialog");
        if (dialog.open) dialog.close();
        dialog.showModal();
    }

    function openNativeTool(operationId) {
        const operation = state.nativeOperations.find((item) => item.id === operationId);
        if (!operation) return;
        state.nativeOperation = operation;
        state.activeTool = null;
        $("process-family").textContent = "Native REST";
        $("process-dialog-title").textContent = operation.name;
        const datasetSelect = operation.scope === "dataset"
            ? `<label class="field"><span>数据集资源</span><select id="native-dataset-path"><option value="">选择 iServer 已发布数据集</option>${operation.datasets.map((dataset) => `<option value="${escapeHtml(dataset.path)}">${escapeHtml(dataset.name)}</option>`).join("")}</select></label>`
            : '<p class="field-help">该算子直接针对输入几何对象运行。</p>';
        $("process-body").innerHTML = `${datasetSelect}<label class="field"><span>iServer 原始参数 JSON</span><textarea id="native-parameters" rows="10" spellcheck="false">{}</textarea><span class="field-help">参数对象将不经转换直接传递给 iServer REST 资源，请按该算子的原生参数契约填写。</span></label>`;
        const dialog = $("process-dialog");
        if (dialog.open) dialog.close();
        dialog.showModal();
    }

    function value(id, fallback = "") { return $("field-" + id)?.value ?? fallback; }
    function number(id, fallback) { return Number(value(id, fallback)); }

    function collectRequest(id) {
        const next = {
            ...state.options,
            datasource: value("datasource", state.options.datasource).trim(), dataset: value("dataset", state.options.dataset).trim(),
            slope_type: value("slope-type", state.options.slope_type), z_factor: number("z-factor", state.options.z_factor),
            azimuth: number("azimuth", state.options.azimuth), altitude: number("altitude", state.options.altitude),
            search_radius: number("search-radius", state.options.search_radius), cell_size: number("cell-size", state.options.cell_size),
            population_field: value("population-field", state.options.population_field).trim(), z_field: value("z-field", state.options.z_field).trim(),
            power: number("power", state.options.power), variogram_type: value("variogram-type", state.options.variogram_type),
            output_dataset: value("output-dataset", state.options.output_dataset).trim(), layers_json: value("layers-json", state.options.layers_json),
        };
        state.options = next;
        const base = { datasource: next.datasource, dataset: next.dataset };
        if (id === "terrain_slope") return { ...base, slope_type: next.slope_type, z_factor: next.z_factor };
        if (id === "terrain_aspect") return base;
        if (id === "terrain_hillshade") return { ...base, azimuth: next.azimuth, altitude: next.altitude };
        if (id === "density_kernel") return { ...base, search_radius: next.search_radius, cell_size: next.cell_size || null, population_field: next.population_field || null };
        if (id === "density_point") return { ...base, cell_size: next.cell_size, search_radius: next.search_radius, population_field: next.population_field || null };
        if (id === "interpolation_idw") return { ...base, z_field: next.z_field, cell_size: next.cell_size, power: next.power, search_radius: next.search_radius || null };
        if (id === "interpolation_kriging") return { ...base, z_field: next.z_field, cell_size: next.cell_size, variogram_type: next.variogram_type };
        try {
            const layers = JSON.parse(next.layers_json);
            if (!Array.isArray(layers) || !layers.length) throw new Error("至少需要一个图层");
            return { datasource: next.datasource, layers, output_dataset: next.output_dataset || null };
        } catch (error) { throw new Error(`叠加图层 JSON 无效：${error.message}`); }
    }

    async function submitTool() {
        const tool = TOOLS[state.activeTool];
        if (!tool) return;
        let payload;
        try { payload = collectRequest(state.activeTool); } catch (error) { toast(error.message, true); return; }
        if (!payload.datasource || (state.activeTool !== "overlay_weighted" && !payload.dataset)) { toast("请填写 iServer 数据源和输入数据集。", true); return; }
        const submit = $("process-form").querySelector(".run-button");
        submit.disabled = true;
        try {
            const response = window.Auth?.getToken() ? await window.Auth.fetch(tool.endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }) : await fetch(tool.endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.detail || `接口返回 ${response.status}`);
            $("process-dialog").close();
            toast(`${tool.label}已提交。结果资源：${result.result_id || result.result?.newResourceID || "已生成"}`);
        } catch (error) { toast(error.message || "iServer 地理处理失败", true); } finally { submit.disabled = false; }
    }

    async function submitNativeTool() {
        const operation = state.nativeOperation;
        if (!operation) return;
        let parameters;
        try {
            parameters = JSON.parse($("native-parameters").value || "{}");
            if (!parameters || Array.isArray(parameters) || typeof parameters !== "object") throw new Error("参数必须是 JSON 对象");
        } catch (error) {
            toast(`原始参数 JSON 无效：${error.message}`, true);
            return;
        }
        const datasetPath = $("native-dataset-path")?.value || null;
        if (operation.scope === "dataset" && !datasetPath) {
            toast("请选择 iServer 已发布数据集资源。", true);
            return;
        }
        const submit = $("process-form").querySelector(".run-button");
        submit.disabled = true;
        try {
            const request = { operation_id: operation.id, dataset_path: datasetPath, parameters };
            const response = window.Auth?.getToken() ? await window.Auth.fetch("/api/spatial-analysis/native-execute", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) }) : await fetch("/api/spatial-analysis/native-execute", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.detail || `接口返回 ${response.status}`);
            $("process-dialog").close();
            toast(`${operation.name}已提交至 iServer。`);
        } catch (error) { toast(error.message || "原生算子执行失败", true); } finally { submit.disabled = false; }
    }

    async function checkServer() {
        const chip = $("server-status");
        try {
            const response = await fetch("/api/system/status");
            if (!response.ok) throw new Error();
            const payload = await response.json();
            const online = payload?.services?.iserver === "online" || payload?.iserver === "online" || payload?.iserver === true;
            chip.classList.add(online ? "is-online" : "is-offline");
            chip.innerHTML = `<i></i>iServer ${online ? "在线" : "离线"}`;
        } catch {
            chip.classList.add("is-offline");
            chip.innerHTML = "<i></i>iServer 不可用";
        }
    }

    function bindEvents() {
        document.querySelectorAll(".tool-tab").forEach((button) => button.addEventListener("click", () => { state.filter = button.dataset.filter; document.querySelectorAll(".tool-tab").forEach((tab) => tab.classList.toggle("is-active", tab === button)); renderCatalog(); }));
        $("default-tool-grid").addEventListener("click", (event) => { const pin = event.target.closest("[data-pin]"); if (pin) togglePin(pin.dataset.pin); });
        $("tool-card-grid").addEventListener("click", (event) => { const pin = event.target.closest("[data-pin]"); const open = event.target.closest("[data-open]"); if (pin) togglePin(pin.dataset.pin); if (open) openTool(open.dataset.open); });
        $("native-operation-list").addEventListener("click", (event) => { const button = event.target.closest("[data-native-open]"); if (button) openNativeTool(button.dataset.nativeOpen); });
        $("native-operation-search").addEventListener("input", (event) => { state.nativeSearch = event.target.value || ""; renderNativeCatalog(); });
        $("pinned-list").addEventListener("click", (event) => { const remove = event.target.closest("[data-unpin]"); if (remove) togglePin(remove.dataset.unpin); });
        $("pinned-list").addEventListener("dragstart", (event) => { const item = event.target.closest("[data-pinned]"); if (!item) return; state.dragId = item.dataset.pinned; item.classList.add("is-dragging"); });
        $("pinned-list").addEventListener("dragend", (event) => event.target.closest("[data-pinned]")?.classList.remove("is-dragging"));
        $("pinned-list").addEventListener("dragover", (event) => event.preventDefault());
        $("pinned-list").addEventListener("drop", (event) => { event.preventDefault(); const target = event.target.closest("[data-pinned]"); if (!target || !state.dragId || target.dataset.pinned === state.dragId) return; const ids = getPinned(); const from = ids.indexOf(state.dragId); const to = ids.indexOf(target.dataset.pinned); ids.splice(from, 1); ids.splice(to, 0, state.dragId); savePinned(ids); state.dragId = null; });
        $("reset-pins").addEventListener("click", () => { savePinned([...DEFAULT_PINNED_TOOLS]); toast("已恢复默认工具。 "); });
        document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => $("process-dialog").close()));
        $("process-form").addEventListener("submit", (event) => { event.preventDefault(); if (state.nativeOperation) submitNativeTool(); else submitTool(); });
    }

    function init() { renderDefaultCatalog(); renderCatalog(); renderPinned(); renderNativeCatalog(); bindEvents(); checkServer(); loadNativeCatalog(); }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true }); else init();
})();
