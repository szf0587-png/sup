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
