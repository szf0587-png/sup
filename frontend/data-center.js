(function () {
    "use strict";

    const state = {
        projectId: "",
        projects: [],
        assets: [],
        selectedAsset: null,
        pendingDelete: null,
    };

    const byId = (id) => document.getElementById(id);
    const assetEndpoint = (assetId = "") => `/api/projects/${state.projectId}/iserver-assets${assetId ? `/${assetId}` : ""}`;

    function showToast(message, kind = "info") {
        const host = byId("toast-region");
        const toast = document.createElement("div");
        toast.className = `toast${kind === "error" ? " is-error" : kind === "warning" ? " is-warning" : ""}`;
        toast.textContent = message;
        host.appendChild(toast);
        window.setTimeout(() => toast.remove(), 4200);
    }

    function setFooter(message) {
        const target = byId("footer-state");
        if (target) target.textContent = message;
    }

    function formatDate(value) {
        if (!value) return "--";
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN", { dateStyle: "short", timeStyle: "short" });
    }

    function getDetail(response, fallback) {
        return response?.detail || response?.message || fallback;
    }

    async function readJson(response) {
        try { return await response.json(); } catch { return {}; }
    }

    function resetDetails() {
        state.selectedAsset = null;
        byId("detail-state").hidden = false;
        byId("detail-body").hidden = true;
        document.querySelectorAll(".asset-table tbody tr").forEach((row) => row.classList.remove("is-selected"));
    }

    function renderProjects() {
        const select = byId("project-select");
        select.replaceChildren();
        if (!state.projects.length) {
            select.add(new Option("暂无项目，请先创建项目", ""));
            state.projectId = "";
            return;
        }
        state.projects.forEach((project) => select.add(new Option(project.name, project.id)));
        const activeId = state.projects.find((project) => project.is_active)?.id;
        state.projectId = state.projectId || activeId || state.projects[0].id;
        select.value = state.projectId;
        const project = state.projects.find((item) => item.id === state.projectId);
        byId("metric-project").textContent = project?.name || "未选择项目";
    }

    function renderAssets() {
        const body = byId("asset-table-body");
        const empty = byId("empty-state");
        body.replaceChildren();
        empty.classList.remove("is-error");
        empty.innerHTML = '<i class="fa-solid fa-box-open" aria-hidden="true"></i><strong>选择项目开始管理数据</strong><span>已登记的 iServer 服务会显示在这里。</span>';
        byId("asset-count").textContent = `${state.assets.length} 项`;
        byId("metric-total").textContent = String(state.assets.length);
        byId("metric-active").textContent = String(state.assets.filter((asset) => asset.is_active).length);
        byId("metric-sources").textContent = String(new Set(state.assets.map((asset) => asset.datasource_name)).size);

        if (!state.assets.length) {
            empty.hidden = false;
            resetDetails();
            return;
        }
        empty.hidden = true;
        state.assets.forEach((asset) => {
            const row = document.createElement("tr");
            row.dataset.assetId = asset.id;
            row.innerHTML = `
                <td><span class="asset-name"></span><span class="asset-sub"></span></td>
                <td><span class="type-badge"></span></td>
                <td><span class="asset-sub asset-datasource"></span><span class="asset-sub asset-dataset"></span></td>
                <td><span class="status-badge"></span></td>
                <td><div class="row-actions"><button class="row-action inspect-action" type="button" title="查看详情" aria-label="查看详情"><i class="fa-solid fa-eye"></i></button><button class="row-action publish-action" type="button" title="发布或取消发布" aria-label="发布或取消发布"><i class="fa-solid fa-cloud-arrow-up"></i></button><button class="row-action is-danger delete-action" type="button" title="删除服务" aria-label="删除服务"><i class="fa-solid fa-trash-can"></i></button></div></td>`;
            row.querySelector(".asset-name").textContent = asset.service_name;
            row.querySelector(".asset-sub").textContent = asset.service_url || "iServer 服务";
            row.querySelector(".type-badge").textContent = asset.service_type;
            row.querySelector(".asset-datasource").textContent = asset.datasource_name;
            row.querySelector(".asset-dataset").textContent = asset.dataset_name;
            const status = row.querySelector(".status-badge");
            status.textContent = asset.lifecycle_status || (asset.is_active ? "published" : "imported");
            status.classList.toggle("is-offline", asset.lifecycle_status === "publish_failed" || asset.lifecycle_status === "unpublish_failed");
            row.querySelector(".inspect-action").addEventListener("click", () => selectAsset(asset.id));
            row.querySelector(".publish-action").addEventListener("click", async () => {
                try { await togglePublication(asset); } catch (error) { showToast(error.message, "error"); }
            });
            row.querySelector(".delete-action").addEventListener("click", () => openDeleteDialog(asset));
            row.addEventListener("dblclick", () => selectAsset(asset.id));
            body.appendChild(row);
        });
        if (state.selectedAsset) selectAsset(state.selectedAsset.id, false);
    }

    async function loadProjects() {
        const response = await Auth.fetch("/api/projects");
        const data = await readJson(response);
        if (!response.ok) throw new Error(getDetail(data, "项目列表读取失败"));
        state.projects = Array.isArray(data.projects) ? data.projects : [];
        renderProjects();
    }

    async function loadAssets() {
        if (!state.projectId) {
            state.assets = [];
            renderAssets();
            setFooter("没有可用项目");
            return;
        }
        setFooter("正在读取项目数据");
        const response = await Auth.fetch(assetEndpoint());
        const data = await readJson(response);
        if (!response.ok) throw new Error(getDetail(data, "项目数据读取失败"));
        state.assets = Array.isArray(data.assets) ? data.assets : [];
        renderAssets();
        const project = state.projects.find((item) => item.id === state.projectId);
        byId("metric-project").textContent = project?.name || state.projectId;
        byId("metric-updated").textContent = `最近刷新 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
        setFooter(`已加载 ${state.assets.length} 项资产`);
    }

    async function loadServerStatus() {
        const badge = byId("iserver-status");
        try {
            const response = await fetch("/api/system/status");
            const data = await response.json();
            const online = data?.services?.iserver === "online";
            badge.classList.toggle("is-online", online);
            badge.classList.toggle("is-offline", !online);
            badge.querySelector("span").textContent = online ? "iServer 在线" : "iServer 离线，可管理登记记录";
        } catch {
            badge.classList.add("is-offline");
            badge.querySelector("span").textContent = "iServer 状态未知";
        }
    }

    async function selectAsset(assetId, loadRemote = true) {
        const asset = state.assets.find((item) => item.id === assetId);
        if (!asset) return;
        state.selectedAsset = asset;
        document.querySelectorAll(".asset-table tbody tr").forEach((row) => row.classList.toggle("is-selected", row.dataset.assetId === asset.id));
        byId("detail-state").hidden = true;
        byId("detail-body").hidden = false;
        byId("detail-type").textContent = asset.service_type;
        byId("detail-name").textContent = asset.service_name;
        byId("detail-url").textContent = asset.service_url || "未配置服务 URL";
        byId("detail-datasource").textContent = asset.datasource_name;
        byId("detail-dataset").textContent = asset.dataset_name;
        byId("detail-created").textContent = formatDate(asset.created_at);
        const publishButton = byId("toggle-publish-asset");
        publishButton.textContent = asset.lifecycle_status === "published" ? "取消发布" : "发布到 iServer";
        byId("metadata-output").textContent = loadRemote ? "正在读取…" : "保留上次读取结果";
        byId("preview-output").textContent = loadRemote ? "正在读取…" : "保留上次读取结果";
        if (!loadRemote) return;

        byId("metadata-state").textContent = "读取中";
        byId("preview-state").textContent = "读取中";
        try {
            const response = await Auth.fetch(`${assetEndpoint(asset.id)}/metadata`);
            const data = await readJson(response);
            if (!response.ok) throw new Error(getDetail(data, "元数据不可用"));
            byId("metadata-output").textContent = JSON.stringify(data, null, 2);
            byId("metadata-state").textContent = data.source === "iserver" ? "iServer" : "本地记录";
        } catch (error) {
            byId("metadata-output").textContent = error.message;
            byId("metadata-state").textContent = "不可用";
        }
        try {
            const response = await Auth.fetch(`${assetEndpoint(asset.id)}/preview`);
            const data = await readJson(response);
            if (!response.ok) throw new Error(getDetail(data, "预览不可用"));
            byId("preview-output").textContent = data.preview ? JSON.stringify(data.preview, null, 2) : (data.message || "该服务类型没有要素预览");
            byId("preview-state").textContent = data.preview ? "前 100 条" : "不适用";
        } catch (error) {
            byId("preview-output").textContent = error.message;
            byId("preview-state").textContent = "不可用";
        }
    }

    async function togglePublication(asset) {
        const isPublished = asset.lifecycle_status === "published";
        const lifecyclePath = isPublished ? "/unpublish" : "/publish";
        const response = await Auth.fetch(`${assetEndpoint(asset.id)}${lifecyclePath}`, { method: "POST" });
        const data = await readJson(response);
        if (!response.ok) throw new Error(getDetail(data, isPublished ? "取消发布失败" : "发布失败，可稍后重试"));
        showToast(isPublished ? "服务已取消发布" : "服务已发布到 iServer");
        await loadAssets();
        if (state.selectedAsset?.id === asset.id) await selectAsset(asset.id);
    }

    function openDeleteDialog(asset) {
        state.pendingDelete = asset;
        byId("confirm-name").textContent = asset.service_name;
        byId("confirm-dialog").showModal();
    }

    async function deleteAsset() {
        const asset = state.pendingDelete;
        if (!asset) return;
        const button = byId("confirm-delete");
        button.disabled = true;
        try {
            const response = await Auth.fetch(assetEndpoint(asset.id), { method: "DELETE" });
            const data = await readJson(response);
            if (!response.ok) throw new Error(getDetail(data, "删除服务失败，未修改本地记录"));
            byId("confirm-dialog").close();
            state.pendingDelete = null;
            showToast("iServer 服务已删除，项目登记已同步移除");
            resetDetails();
            await loadAssets();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            button.disabled = false;
        }
    }

    function openAssetDialog() {
        if (!state.projectId) {
            showToast("请先创建或选择一个项目", "warning");
            return;
        }
        byId("asset-form").reset();
        byId("asset-dialog").showModal();
    }

    async function registerAsset(event) {
        event.preventDefault();
        if (!state.projectId) return;
        const form = new FormData(event.currentTarget);
        const file = form.get("asset_file");
        if (!(file instanceof File) || !file.name) { showToast("请选择 GeoJSON 数据文件", "warning"); return; }
        const button = byId("submit-asset");
        button.disabled = true;
        try {
            const upload = new FormData();
            upload.append("file", file);
            const name = String(form.get("dataset_name") || "").trim();
            if (name) upload.append("name", name);
            const uploadResponse = await Auth.fetch("/api/datasets/upload", { method: "POST", body: upload });
            const uploaded = await readJson(uploadResponse);
            if (!uploadResponse.ok) throw new Error(getDetail(uploaded, "数据上传失败"));
            const projectResponse = await Auth.fetch(`/api/projects/${state.projectId}/datasets`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: uploaded.id }) });
            const projectData = await readJson(projectResponse);
            if (!projectResponse.ok) throw new Error(getDetail(projectData, "数据集未加入项目"));
            const response = await Auth.fetch(`${assetEndpoint()}/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: uploaded.id }) });
            const data = await readJson(response);
            if (!response.ok) throw new Error(getDetail(data, "数据导入失败"));
            byId("asset-dialog").close();
            showToast("数据已导入当前项目，可发布到 iServer");
            await loadAssets();
        } catch (error) { showToast(error.message, "error"); }
        finally { button.disabled = false; }
    }

    async function initialize() {
        await Auth.checkAuth();
        try {
            const user = await Auth.getCurrentUser();
            byId("user-chip").textContent = user.display_name || user.username || "当前用户";
        } catch { /* checkAuth handles the redirect */ }
        loadServerStatus();
        try { await loadProjects(); await loadAssets(); }
        catch (error) { byId("empty-state").classList.add("is-error"); byId("empty-state").innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i><strong>数据读取失败</strong><span></span>`; byId("empty-state").querySelector("span").textContent = error.message; showToast(error.message, "error"); }
    }

    byId("project-select").addEventListener("change", async (event) => { state.projectId = event.target.value; resetDetails(); try { await loadAssets(); } catch (error) { showToast(error.message, "error"); } });
    byId("refresh-button").addEventListener("click", async () => { try { await loadProjects(); await loadAssets(); showToast("项目数据已刷新"); } catch (error) { showToast(error.message, "error"); } });
    byId("register-button").addEventListener("click", openAssetDialog);
    byId("asset-form").addEventListener("submit", registerAsset);
    byId("toggle-publish-asset").addEventListener("click", async () => {
        if (!state.selectedAsset) return;
        try { await togglePublication(state.selectedAsset); } catch (error) { showToast(error.message, "error"); }
    });
    byId("delete-asset-button").addEventListener("click", () => state.selectedAsset && openDeleteDialog(state.selectedAsset));
    byId("confirm-form").addEventListener("submit", (event) => { event.preventDefault(); deleteAsset(); });
    byId("close-detail").addEventListener("click", resetDetails);
    byId("logout-button").addEventListener("click", () => Auth.logout());
    document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));
    initialize();
})();
