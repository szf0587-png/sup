const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');

const repositoryRoot = path.resolve(__dirname, '..', '..');
const showcaseRoot = path.resolve(repositoryRoot, '..', 'tianyan-showcase');
const showcaseHtml = fs.readFileSync(path.join(showcaseRoot, 'index.html'), 'utf8');
const showcaseConfig = fs.readFileSync(path.join(showcaseRoot, 'config.js'), 'utf8');

const allowedConsolePaths = new Set([
  '/index.html',
  '/data-center.html',
  '/iserver-tools.html',
  '/map3d.html',
  '/golden_standard.html',
]);

test('showcase workbench links enter real console pages through safe login next URLs', () => {
  assert.doesNotMatch(showcaseHtml, /href=["']screens\//);

  const links = [...showcaseHtml.matchAll(
    /<a\b[^>]*href=["']([^"']+)["'][^>]*data-console-path=["']([^"']+)["'][^>]*>/g,
  )];
  assert.ok(links.length >= 10, 'expected every former showcase screen link to be replaced');

  const destinations = new Set();
  for (const [, href, consolePath] of links) {
    assert.ok(allowedConsolePaths.has(consolePath), `unexpected console destination: ${consolePath}`);
    assert.match(href, /\/login\.html\?next=/);
    assert.equal(new URL(href).searchParams.get('next'), consolePath);
    destinations.add(consolePath);
  }

  assert.deepEqual(
    destinations,
    new Set(['/map3d.html', '/iserver-tools.html', '/data-center.html']),
  );
});

test('showcase config rewrites allowed destinations through the deployment login URL', () => {
  const context = { window: { TIANYAN_WORKBENCH_BASE: 'https://console.example/' } };
  vm.runInNewContext(showcaseConfig, context);

  for (const consolePath of ['/map3d.html', '/iserver-tools.html', '/data-center.html']) {
    const target = new URL(context.window.tianyanConsoleUrl(consolePath));
    assert.equal(target.origin, 'https://console.example');
    assert.equal(target.pathname, '/login.html');
    assert.equal(target.searchParams.get('next'), consolePath);
  }
  assert.equal(
    new URL(context.window.tianyanConsoleUrl('https://evil.example/')).searchParams.get('next'),
    '/index.html',
  );
});
