const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..', '..');
const pages = [
  'index.html',
  'data-center.html',
  'iserver-tools.html',
  'map3d.html',
  'golden_standard.html',
  'ai-chat.html',
];

test('all console pages load the same navigation component', () => {
  for (const page of pages) {
    const html = fs.readFileSync(path.join(root, 'frontend', page), 'utf8');
    assert.match(html, /app-shell\.css/);
    assert.match(html, /shell-navigation\.js/);
  }
});

test('shared navigation keeps a fixed console order', () => {
  const script = fs.readFileSync(path.join(root, 'frontend', 'shell-navigation.js'), 'utf8');
  const expected = [
    'index.html',
    'data-center.html',
    'iserver-tools.html',
    'map3d.html',
    'golden_standard.html',
    'ai-chat.html',
  ];
  const positions = expected.map((href) => script.indexOf(`href: "${href}"`));
  assert.ok(positions.every((position) => position >= 0));
  assert.deepEqual([...positions].sort((a, b) => a - b), positions);
});

test('workbench does not require the replaced sidebar decision-agent trigger', () => {
  const script = fs.readFileSync(path.join(root, 'frontend', 'land-workbench.js'), 'utf8');
  assert.match(script, /const sideDecisionAgent = \$\("open-decision-agent"\);/);
  assert.match(script, /if \(sideDecisionAgent\) sideDecisionAgent\.addEventListener/);
});
