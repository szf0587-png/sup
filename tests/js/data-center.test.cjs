const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(root, 'frontend', 'data-center.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'frontend', 'data-center.js'), 'utf8');

test('data center page exposes project-scoped asset workflow', () => {
  assert.match(html, /id="project-select"/);
  assert.match(html, /id="asset-table-body"/);
  assert.match(html, /data-center\.js/);
  assert.match(js, /\/api\/projects\/\$\{state\.projectId\}\/iserver-assets/);
  assert.match(js, /Auth\.fetch/);
  assert.match(js, /metadata/);
  assert.match(js, /preview/);
  assert.match(js, /DELETE/);
  assert.match(js, /\/publish/);
  assert.match(js, /\/unpublish/);
  assert.match(js, /\/api\/datasets\/upload/);
});

test('data center page keeps service registration and offline state visible', () => {
  assert.match(html, /id="asset-dialog"/);
  assert.match(html, /id="iserver-status"/);
  assert.match(html, /id="empty-state"/);
  assert.match(js, /showToast/);
  assert.match(js, /iServer/);
});
