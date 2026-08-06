const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const html = fs.readFileSync(
  path.resolve(__dirname, '..', '..', 'frontend', 'index.html'),
  'utf8',
);

test('workbench three-dimensional navigation opens the real map3d page', () => {
  assert.match(html, /<a[^>]+href="map3d\.html"[^>]+aria-label="三维场景"/);
});
