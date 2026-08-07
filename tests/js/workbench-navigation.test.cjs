const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const html = fs.readFileSync(
  path.resolve(__dirname, '..', '..', 'frontend', 'index.html'),
  'utf8',
);

test('workbench three-dimensional navigation opens the real map3d page', () => {
  assert.match(html, /<script src="shell-navigation\.js"><\/script>/);

  const navigation = fs.readFileSync(
    path.resolve(__dirname, '..', '..', 'frontend', 'shell-navigation.js'),
    'utf8',
  );
  assert.match(navigation, /href: "map3d\.html"/);
});
