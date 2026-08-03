# Competition Platform Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将“天眼寻珍·苍穹”升级为展示站、认证、多用户 iServer 数据管理、真实土地评估、三维地形和 AI 助理贯通的可复现比赛作品。

**Architecture:** 保留 FastAPI + SQLAlchemy + 原生 HTML/JavaScript 的现有分层，通过后端统一代理 iServer 和第三方 AI，浏览器不直接持有 iServer 管理员凭据或第三方 API Key。公开展示站只承担项目介绍，所有“进入工作台”入口都进入真实认证流程，认证后访问同一套真实控制台。

**Tech Stack:** Python 3.12、FastAPI、SQLAlchemy 2.x、SQLite、SuperMap iServer 2026、iObjects Python、SuperMap3D/Cesium、原生 JavaScript、pytest、Playwright、OpenAI-compatible API。

## Global Constraints

- SuperMap 产品版本不得低于 2025（V12.0.0）；目标运行环境固定为 SuperMap iServer 2026。
- 比赛核心评分结果不得使用固定值、随机数或未标注的模拟数据。
- 所有用户资源查询必须以服务端解析的 `current_user.id` 为边界，禁止接受客户端传入的 `user_id` 作为授权依据。
- iServer 管理员凭据和第三方 AI API Key 只存在于服务端，禁止写入 HTML、JavaScript、日志、Git 或浏览器存储。
- 静态展示页不得伪造“iServer 已连接”“分析完成”等实时状态。
- 每个阶段必须独立通过测试和人工验收后才能进入下一阶段。
- 不把 `supermap-iserver-ext_ai3d-2026-windows-x64-bin` 的 21.85 GB 官方运行环境放入参赛作品压缩包。

---

## Delivery Sequence

```text
M0 基线与环境冻结
  -> M1 三维地形真实渲染
  -> M2 展示站、登录与真实工作台贯通
  -> M3 多用户 iServer 项目数据中心
  -> M4 真实土地评估证据链
  -> M5 多供应商 AI 助理
  -> M6 比赛提交包与演示验收
```

M1、M2、M3 对应团队提出的前三项需求；M5 对应 AI 对话需求。M4 是进入 M5 前的强制门槛，因为 AI 不能掩盖核心算法仍为模拟值的问题。

---

### Task 0: Freeze a Reproducible Baseline

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `docs/ENVIRONMENT_BASELINE.md`
- Create: `tests/test_system_contract.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: existing `server.main:app`, `/api/system/status`, `/api/land-assessment/capabilities`
- Produces: one documented Python environment and a baseline contract test suite used by every later milestone

- [ ] Pin runtime dependencies to versions verified on the competition machine; add `pytest`, `pytest-cov`, `httpx`, and `playwright` to `requirements-dev.txt`.
- [ ] Create a fresh `.venv`, install both requirement files, and record Python, iServer, iObjects, browser, and OS versions in `docs/ENVIRONMENT_BASELINE.md`.
- [ ] Add contract tests asserting that the app starts, static pages load, authentication protects private APIs, and `/api/system/status` reports one canonical version.
- [ ] Unify README, application metadata, and status output on version `4.2.0`.
- [ ] Run `python -m pytest -q`; expected result: all baseline tests pass with no import errors.
- [ ] Commit with `chore: freeze competition runtime baseline`.

**Gate M0:** A new developer can create the environment and run the baseline suite using only repository instructions.

---

### Task 1: Make SCT Terrain Visibly Real

**Files:**
- Modify: `server/api/scene_3d.py`
- Modify: `server/integrations/iserver_client.py`
- Modify: `frontend/map3d.html`
- Create: `frontend/js/3d/terrain-controller.js`
- Create: `tests/test_scene_3d.py`
- Create: `tests/e2e/test_terrain_toggle.py`
- Modify: `docs/3D_TERRAIN_DIAGNOSIS.md`

**Interfaces:**
- Consumes: iServer Realspace discovery, SCT service URL, terrain bounds, SuperMap3D runtime
- Produces: `GET /api/scene-3d/terrain/diagnostics` and `TerrainController.enable()`, `disable()`, `focus()`, `setExaggeration(value)`

- [ ] Add a backend terrain diagnostic response containing `available`, `provider_type`, `service_url`, `terrain_url`, `bounds`, `layer_name`, and `reason`.
- [ ] Add tests for online SCT, missing SCT, malformed bounds, and iServer-offline responses.
- [ ] Extract terrain lifecycle code from inline `map3d.html` into `terrain-controller.js`; remove the duplicate `toggleLayer()` declarations.
- [ ] Keep terrain Provider visibility separate from Realspace scene-layer visibility; toggling terrain must replace `viewer.terrainProvider`, while ordinary layers use `scene.layers`.
- [ ] Initialize the SCT Provider with visible rendering, wait for readiness, assign it to the Viewer, request render, then fly to the returned bounds.
- [ ] Display the actual mode in the UI: `SuperMap SCT`, `Cesium online terrain`, or `ellipsoid plane`; never label a fallback as the real洛南 terrain.
- [ ] Add an end-to-end test that captures enabled and disabled canvas screenshots and asserts a non-trivial pixel difference plus changed camera pick heights.
- [ ] Run `python -m pytest tests/test_scene_3d.py tests/e2e/test_terrain_toggle.py -q`; expected result: all terrain tests pass.
- [ ] Commit with `fix: render and toggle real SCT terrain`.

**Gate M1:** At the same camera pose, terrain on/off and 1x/2x exaggeration produce visibly and measurably different output.

---

### Task 2: Connect Showcase, Login, and Real Console

**Files:**
- Modify: `D:/supermap/tianyan-showcase/index.html`
- Create: `D:/supermap/tianyan-showcase/config.js`
- Modify: `frontend/login.html`
- Modify: `frontend/auth.js`
- Modify: `frontend/navbar.js`
- Modify: `frontend/index.html`
- Modify: `frontend/iserver-tools.html`
- Modify: `frontend/map3d.html`
- Modify: `frontend/golden_standard.html`
- Create: `tests/e2e/test_authenticated_navigation.py`

**Interfaces:**
- Consumes: existing JWT login and private console pages
- Produces: safe same-origin `next` navigation and public-to-private application flow

- [ ] Define `WORKBENCH_BASE_URL` in showcase `config.js`; all showcase calls-to-action must use `${WORKBENCH_BASE_URL}/login.html?next=/index.html`.
- [ ] Parse `next` on the login page and accept only allowlisted same-origin paths: `/index.html`, `/data-center.html`, `/iserver-tools.html`, `/map3d.html`, and `/golden_standard.html`.
- [ ] After successful login, navigate to the validated `next`; after token expiry, return to login with the current page encoded as `next`.
- [ ] Replace showcase links to `screens/*.html` with real authenticated console URLs; exclude the three fictional screens from the published showcase build.
- [ ] Remove static online-state claims from the public site. Public copy may state capabilities but not current service health.
- [ ] Add consistent navigation among the real workbench, data center, iServer tools, model library, 3D scene, AI assistant, and public project introduction.
- [ ] Add Playwright tests for unauthenticated redirect, successful redirect, rejected external `next`, token expiry, and navigation among all real pages.
- [ ] Run `python -m pytest tests/e2e/test_authenticated_navigation.py -q`; expected result: all navigation cases pass.
- [ ] Commit with `feat: connect showcase to authenticated console`.

**Gate M2:** A judge can start at the public introduction, log in once, and reach every real console without entering a fictional page.

---

### Task 3: Build the Multi-user iServer Project Data Center

**Files:**
- Modify: `server/models/iserver_service.py`
- Modify: `server/models/dataset.py`
- Create: `server/schemas/iserver_asset.py`
- Create: `server/services/iserver_asset_service.py`
- Create: `server/api/iserver_assets.py`
- Modify: `server/main.py`
- Modify: `server/integrations/iserver_client.py`
- Create: `frontend/data-center.html`
- Create: `frontend/data-center.css`
- Create: `frontend/data-center.js`
- Create: `tests/test_iserver_assets.py`
- Create: `scripts/migrate_v42.py`

**Interfaces:**
- Consumes: `current_user`, existing `Project`, `Dataset`, `IServerService`, and iServer REST client
- Produces: project-scoped asset inventory and controlled lifecycle endpoints

**Required API:**

```text
GET    /api/projects/{project_id}/iserver-assets
POST   /api/projects/{project_id}/iserver-assets/import
POST   /api/projects/{project_id}/iserver-assets/{asset_id}/publish
POST   /api/projects/{project_id}/iserver-assets/{asset_id}/unpublish
GET    /api/projects/{project_id}/iserver-assets/{asset_id}/preview
GET    /api/projects/{project_id}/iserver-assets/{asset_id}/metadata
DELETE /api/projects/{project_id}/iserver-assets/{asset_id}
```

- [ ] Add `project_id`, lifecycle status, publication timestamps, and last error fields to `IServerService`; migrate existing SQLite databases idempotently with `scripts/migrate_v42.py`.
- [ ] Implement `IServerAssetService` so every query filters by both `project_id` and `current_user.id` before contacting iServer.
- [ ] Generate server-side resource names as `u_<user-id-prefix>_p_<project-id-prefix>_<sanitized-name>` and reject collisions.
- [ ] Implement import, publish, unpublish, preview, metadata, and soft-delete endpoints; never return iServer administrator credentials.
- [ ] Build `data-center.html` with project selector, data-source tree, asset table, metadata drawer, map preview, upload/import dialog, publication status, and recoverable error states.
- [ ] Reuse the current dataset upload and metadata APIs instead of duplicating local-file persistence.
- [ ] Add tests proving user A cannot list, preview, publish, or delete user B assets even when IDs are guessed.
- [ ] Add tests for iServer offline, duplicate names, unsupported formats, invalid CRS, failed publication, and successful retry.
- [ ] Run `python -m pytest tests/test_iserver_assets.py -q`; expected result: all authorization and lifecycle tests pass.
- [ ] Commit with `feat: add project-scoped iServer data center`.

**Gate M3:** Two test users see disjoint project resources and can independently import, preview, publish, unpublish, and delete their own assets.

---

### Task 4: Replace Simulated Competition Results with Evidence

**Files:**
- Modify: `server/services/town_ranking.py`
- Modify: `server/services/parcel_evaluation.py`
- Modify: `server/services/greenhouse_detection.py`
- Modify: `server/config.py`
- Modify: `server/services/report_builder.py`
- Modify: `data/manifest.json`
- Create: `data/vector/luonan_towns.geojson`
- Create: `data/vector/luonan_constraints.geojson`
- Create: `data/raster/luonan_dem.tif`
- Create: `data/gee_cache/ndvi_2023_luonan.json`
- Create: `data/gee_cache/lst_2023_luonan.json`
- Create: `tests/test_real_assessment.py`
- Create: `scripts/verify_case_study.py`

**Interfaces:**
- Consumes: real洛南 boundaries, DEM, constraints, NDVI/LST cache, gold standard, iServer/iObjects operations
- Produces: reproducible Top-N ranking, parcel evaluation, evidence metadata, and report artifacts

- [ ] Import legally distributable case data into the repository data package; fill source, license, acquisition date, CRS, resolution, and SHA-256 in `manifest.json`.
- [ ] Replace random AHP values in `town_ranking.py` with slope, aspect, elevation, climate reclassification and zonal statistics outputs.
- [ ] Replace fixed parcel AHP score and synthetic phenology curves with values extracted for the submitted parcel geometry.
- [ ] Set `AI_REALTIME_ENABLED` and `AI_PRECOMPUTED_AVAILABLE` from actual model/snapshot readiness checks rather than constants.
- [ ] If greenhouse inference is not completed, exclude its score from the competition total and label the evidence unavailable; never substitute a simulated density.
- [ ] Return `data_mode`, source dataset IDs, timestamps, weights, intermediate metrics, and degradation reason with every assessment.
- [ ] Include those evidence fields in the generated report so a result can be traced back to its inputs.
- [ ] Add deterministic tests for known fixtures, low coverage exclusion, missing inputs, and score recomputation.
- [ ] Run `python scripts/verify_case_study.py`; expected result: one frozen project produces stable Top-5, parcel score, map layers, and report checksums.
- [ ] Run `python -m pytest tests/test_real_assessment.py -q`; expected result: no scored path reports `mock`, `simulated`, `default`, or random output.
- [ ] Commit with `feat: complete evidence-backed assessment workflow`.

**Gate M4:** The fixed case can run offline from packaged data and every displayed score is traceable to real input data and a documented calculation.

---

### Task 5: Add a Per-user Multi-provider AI Assistant

**Files:**
- Create: `server/models/ai_provider_config.py`
- Create: `server/models/ai_conversation.py`
- Create: `server/models/ai_message.py`
- Modify: `server/models/__init__.py`
- Create: `server/schemas/ai.py`
- Create: `server/services/ai/encryption.py`
- Create: `server/services/ai/provider_gateway.py`
- Create: `server/services/ai/context_service.py`
- Create: `server/api/ai.py`
- Modify: `server/main.py`
- Modify: `server/config.py`
- Modify: `requirements.txt`
- Create: `frontend/ai-assistant.html`
- Create: `frontend/ai-assistant.css`
- Create: `frontend/ai-assistant.js`
- Create: `tests/test_ai_assistant.py`
- Modify: `scripts/migrate_v42.py`

**Interfaces:**
- Consumes: authenticated user, active project, owned datasets, assessment reports, encrypted provider credentials
- Produces: isolated provider settings, conversations, messages, streaming responses, and read-only GIS context tools

**Required API:**

```text
GET    /api/ai/providers
POST   /api/ai/providers
POST   /api/ai/providers/{provider_id}/test
DELETE /api/ai/providers/{provider_id}
GET    /api/ai/conversations
POST   /api/ai/conversations
GET    /api/ai/conversations/{conversation_id}
DELETE /api/ai/conversations/{conversation_id}
POST   /api/ai/conversations/{conversation_id}/messages
```

- [ ] Add per-user provider, conversation, and message tables; all repository queries must include `user_id == current_user.id`.
- [ ] Encrypt API Keys using a server-side `AI_KEY_ENCRYPTION_SECRET`; responses expose only provider, model, status, and key suffix.
- [ ] Implement OpenAI-compatible adapters for OpenAI, DeepSeek, Qwen, Zhipu, Moonshot, and an HTTPS-only custom endpoint.
- [ ] Resolve custom hostnames and block loopback, link-local, private, metadata-service, and non-HTTPS destinations to prevent SSRF.
- [ ] Implement connection testing, timeout, cancellation, rate limiting, token/usage metadata, and normalized provider errors.
- [ ] Build project-aware context from platform documentation, current project metadata, owned datasets, and completed assessment reports.
- [ ] Limit initial assistant tools to read-only operations: list projects, describe datasets, explain assessment factors, summarize reports, and recommend iServer operations.
- [ ] Build the AI page with provider selector, masked-key management, conversation list, project context selector, streaming messages, retry, stop, rename, and delete.
- [ ] Add tests for cross-user isolation, encrypted storage, masked responses, invalid keys, provider timeout, SSRF blocking, prompt/tool authorization, and conversation deletion.
- [ ] Run `python -m pytest tests/test_ai_assistant.py -q`; expected result: all provider and tenant-isolation tests pass without real paid API calls.
- [ ] Commit with `feat: add project-aware multi-provider AI assistant`.

**Gate M5:** Two users can configure different providers and retain separate histories; neither can access the other's key, conversations, projects, datasets, or reports.

---

### Task 6: Harden the Competition Submission and Demo

**Files:**
- Modify: `scripts/prepare-submission.ps1`
- Modify: `scripts/verify-coldstart.ps1`
- Create: `scripts/verify-demo-path.ps1`
- Create: `docs/SUPERMAP_TECHNICAL_EVIDENCE.md`
- Create: `docs/DEMO_SCRIPT.md`
- Modify: `README.md`
- Modify: `data/manifest.json`
- Update: official submission DOCX/XLSX/PPTX artifacts outside the source repository

**Interfaces:**
- Consumes: all milestone gates and frozen case-study outputs
- Produces: competition-compliant folder tree, deployment package, evidence report, screenshots, and demo script

- [ ] Make the package builder generate the required `CD<团队邀请码>` folder hierarchy and reject missing mandatory artifacts.
- [ ] Exclude Git metadata, `.bak`, `.omo`, local databases, user uploads, secrets, caches not used by the frozen case, and the 21.85 GB official iServer extension directory.
- [ ] Generate checksums without appending duplicate entries on repeated builds.
- [ ] Add secret scanning for default passwords, API Keys, JWT secrets, iServer credentials, personal absolute paths, and private user data.
- [ ] Run cold-start deployment on a clean machine and verify login, data center, real assessment, terrain toggle, report export, and AI assistant isolation.
- [ ] Create `SUPERMAP_TECHNICAL_EVIDENCE.md` mapping every judged capability to its iServer/iObjects service, request, input dataset, output, screenshot, and source file.
- [ ] Write an 8-10 minute scenario-based demo: public value proposition -> login -> project data -> real spatial assessment -> 3D terrain verification -> report -> AI explanation.
- [ ] Capture at least three 1920x1080 representative screenshots and a full demo recording under 20 minutes.
- [ ] Run `scripts/verify-demo-path.ps1`; expected result: every demo step reports PASS and all expected artifacts exist.
- [ ] Commit with `chore: prepare verified competition submission`.

**Gate M6:** A clean machine can reproduce the full judge-facing scenario without source edits, personal paths, undisclosed mock data, or external developer setup.

---

## Terra Execution Rules

1. Terra receives only one milestone at a time, beginning with Task 0.
2. Before editing, Terra must inspect the listed files and preserve unrelated user changes.
3. Each milestone follows red-green testing and ends with the exact gate evidence.
4. A failed gate blocks the next milestone; feature work must not bypass it.
5. Terrain and browser tasks require desktop and mobile screenshots plus canvas-pixel validation.
6. After every milestone, update this document's checklist and record the commit hash and verification output in `docs/DAILY_LOG_20260803.md` or a new dated continuation log.

## Final Acceptance Matrix

| Requirement | Milestone | Acceptance evidence |
|---|---|---|
| 用户项目数据管理 | M3 | Cross-user isolation tests + real iServer lifecycle demo |
| 三维地形真实显示 | M1 | SCT requests + terrain on/off pixel and elevation difference |
| 展示站进入真实工作台 | M2 | Playwright authenticated navigation trace |
| AI 对话与 BYOK | M5 | Encrypted-key and tenant-isolation tests |
| 核心决策结果真实 | M4 | Frozen-case checksums and zero simulated scored paths |
| 比赛材料可提交 | M6 | Clean-machine cold-start and package validator PASS |

