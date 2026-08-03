const test = require('node:test');
const assert = require('node:assert/strict');
const { TerrainController } = require('../../frontend/js/3d/terrain-controller.js');

test('terrain visibility swaps the viewer provider instead of a scene layer', () => {
  const ellipsoid = { kind: 'ellipsoid' };
  const engine = { EllipsoidTerrainProvider: class { constructor() { return ellipsoid; } } };
  const viewer = { terrainProvider: null, scene: { requestRender() {} } };
  const state = { terrainProvider: null, terrainEnabled: false, exaggeration: 1 };
  const controller = new TerrainController({ engine, viewer, state });
  const sct = { kind: 'sct' };

  controller.setProvider(sct);
  controller.setVisible(true);
  assert.equal(viewer.terrainProvider, sct);
  assert.equal(state.terrainEnabled, true);
  controller.setVisible(false);
  assert.equal(viewer.terrainProvider, ellipsoid);
  assert.equal(state.terrainEnabled, false);
});

test('terrain exaggeration is applied to the scene', () => {
  const viewer = { terrainProvider: null, scene: { terrainExaggeration: 1, verticalExaggeration: 1 } };
  const state = { terrainProvider: null, terrainEnabled: false, exaggeration: 1 };
  const controller = new TerrainController({ engine: {}, viewer, state });

  controller.setExaggeration(2);

  assert.equal(viewer.scene.terrainExaggeration, 2);
  assert.equal(viewer.scene.verticalExaggeration, 2);
  assert.equal(state.exaggeration, 2);
});
