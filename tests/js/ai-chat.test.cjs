const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');

const script = fs.readFileSync(path.resolve(__dirname, '..', '..', 'frontend', 'ai-chat.js'), 'utf8');
const formatApiError = vm.runInNewContext(`${script.match(/function formatApiError\(detail\)\{.*?\n/)[0]}; formatApiError`);

test('AI provider settings normalize provider IDs and render structured validation errors', () => {
  assert.match(script, /function formatApiError\(detail\)/);
  assert.match(script, /provider:\s*provider\.toLowerCase\(\)/);
  assert.doesNotMatch(script, /alert\(error\.message\)/);
});

test('AI provider validation errors identify the invalid field instead of rendering an object', () => {
  const message = formatApiError([{ loc: ['body', 'provider'], msg: 'String should match pattern' }]);
  assert.equal(message, 'provider：String should match pattern');
  assert.doesNotMatch(message, /\[object Object\]/);
});
