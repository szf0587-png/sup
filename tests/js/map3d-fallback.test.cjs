const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const html = fs.readFileSync(path.resolve(__dirname, '..', '..', 'frontend', 'map3d.html'), 'utf8');

test('3D page creates an explicit offline preview instead of returning blank', () => {
  assert.match(html, /function openOfflinePreview\(reason\)/);
  assert.match(html, /openOfflinePreview\(payload\.reason/);
  assert.match(html, /iServer 离线预览/);
});

test('3D page offers the SuperMap iClient runtime before the Cesium fallback', () => {
  assert.match(html, /function getIserverRuntimeRoot\(\)/);
  assert.match(html, /contextPath}\/static\/iClient3DForWebGL\//);
  assert.match(html, /@supermap\/iclient3d-webgl@11\.1\.4\/Cesium\//);
  assert.match(html, /\$\{superMapCdnRoot\}Cesium\.js/);
  assert.match(html, /CESIUM_BASE_URL/);
  assert.match(html, /typeof engine\.SuperMapTerrainProvider/);
  assert.match(html, /addS3MTilesLayerByScp/);
  assert.match(html, /function findSceneLayer\(/);
});

test('SCT terrain is opened as a Realspace layer before any Cesium fallback', () => {
  const realspaceOpen = html.indexOf('await viewer.scene.open(state.config.scene_url, state.config.scene_resource');
  const cesiumTerrainFallback = html.indexOf('state.terrainProvider = await createTerrainProvider(engine)');

  assert.ok(realspaceOpen >= 0);
  assert.ok(cesiumTerrainFallback >= 0);
  assert.ok(realspaceOpen < cesiumTerrainFallback);
  assert.match(html, /viewer\.scene\.globe\.depthTestAgainstTerrain = true/);
});

test('terrain camera keeps the published scene altitude instead of forcing a high flat view', () => {
  assert.doesNotMatch(html, /Math\.max\(SAFE_CAMERA_HEIGHT, Number\(view\.height\) \* 4\)/);
  assert.match(html, /Math\.max\(1200, Number\(view\.height\) \* 1\.35\)/);
  assert.match(html, /pitch: engine\.Math\.toRadians\(-48\)/);
});

test('native Realspace terrain reapplies elevation exaggeration after the scene configuration loads', () => {
  assert.match(html, /exaggeration: 4/);
  const openAt = html.indexOf('await viewer.scene.open(state.config.scene_url, state.config.scene_resource');
  const nativeLoad = html.slice(openAt, openAt + 1400);

  assert.match(nativeLoad, /setExaggeration\(4\)/);
});

test('Realspace reports SCT as open only after its TerrainFileLayer exists in the browser scene', () => {
  assert.match(html, /async function waitForTerrainLayer\(viewer, source\)/);
  assert.match(html, /state\.terrainLayer \|\|= await waitForTerrainLayer\(viewer, terrainSource\)/);
  assert.match(html, /nativeTerrainOpened = Boolean\(state\.terrainLayer\)/);
  assert.doesNotMatch(html, /nativeTerrainOpened = Boolean\(state\.terrainDiagnostics\?\.available\)/);
});

test('map control buttons invoke camera actions and the globe button toggles imagery without leaving 3D', () => {
  assert.match(html, /\$\("home-view"\)\.addEventListener\("click", homeView\)/);
  assert.match(html, /\$\("tilt-view"\)\.addEventListener\("click", setTilt\)/);
  assert.match(html, /function toggleReferenceImagery\(\)/);
  assert.match(html, /if \(!state\.terrainLayer\) \{ toast\("SCT 地形尚未渲染，不能隐藏影像底图"\); return; \}/);
  assert.match(html, /imageryLayers\.get\(index\)\.show/);
  assert.doesNotMatch(html, /morphTo2D\(0\.7\)/);
  assert.match(html, /\$\("scene-mode"\)\.addEventListener\("click", toggleReferenceImagery\)/);
});
