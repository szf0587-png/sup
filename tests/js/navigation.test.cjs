const test = require('node:test');
const assert = require('node:assert/strict');
const { resolveNextPath } = require('../../frontend/js/navigation.js');

test('allows only known internal console paths', () => {
  assert.equal(resolveNextPath('/map3d.html'), '/map3d.html');
  assert.equal(resolveNextPath('/data-center.html?project=project_1'), '/data-center.html?project=project_1');
  assert.equal(resolveNextPath('/not-a-console.html'), '/index.html');
});

test('rejects external redirect targets', () => {
  assert.equal(resolveNextPath('https://evil.example/steal'), '/index.html');
  assert.equal(resolveNextPath('//evil.example/steal'), '/index.html');
});
