/* Fixtures for the residual-English scanner, including the MIXED-LANGUAGE case
 * it used to miss. Run: node tools/test_scan_residual_english.cjs
 *
 * The mixed fixture is the real defect: a Vietnamese wrapper around a whole
 * English paragraph. The old node-level diacritic test skipped the entire node
 * as soon as it saw one Vietnamese character, so the scanner reported zero
 * suspects while an untranslated paragraph was on screen.
 */
const test = require('node:test');
const assert = require('node:assert');
const { scanResidualEnglish } = require('./scan_residual_english.js');

function page(html) {
  const nodes = [];
  // A deliberately tiny DOM stub: the scanner only uses createTreeWalker,
  // parentElement, closest, nodeValue and querySelectorAll.
  for (const part of html) {
    nodes.push({
      nodeValue: part.text,
      parentElement: {
        id: part.id || '',
        className: part.cls || '',
        tagName: part.tag || 'P',
        closest: () => (part.ariaHidden ? {} : null),
      },
    });
  }
  let i = 0;
  global.document = {
    body: {},
    createTreeWalker: () => ({ nextNode: () => (i < nodes.length ? nodes[i++] : null) }),
    querySelectorAll: () => [],
  };
  global.NodeFilter = { SHOW_TEXT: 4 };
  i = 0;
  return scanResidualEnglish();
}

test('a fully Vietnamese node is not a suspect', () => {
  const r = page([{ text: 'Hệ số trần đã khớp chi phí là điểm gần nhất tìm được trên lưới tìm kiếm đã đăng ký.' }]);
  assert.strictEqual(r.suspects, 0);
});

test('a fully English node is a suspect', () => {
  const r = page([{ text: 'The cost-matched cap factor is the nearest point found on the registered search grid.' }]);
  assert.strictEqual(r.suspects, 1);
});

test('MIXED: a Vietnamese wrapper around an English paragraph IS reported', () => {
  const mixed =
    'Mỗi con số ở đây là kết quả mô phỏng theo các giả định đã nêu. ' +
    'The cost-matched cap factor is the NEAREST POINT FOUND ON THE REGISTERED ' +
    '0.0005-step search grid: it prices at 19.537656% against the benchmark.';
  const r = page([{ text: mixed, id: 'caveats' }]);
  assert.strictEqual(r.suspects, 1, 'the English sentence must be reported');
  assert.ok(r.list[0].text.startsWith('The cost-matched'), r.list[0].text);
  assert.strictEqual(r.list[0].mixedNode, true, 'flagged as a mixed node');
});

test('a proper name alone is not a suspect', () => {
  assert.strictEqual(page([{ text: 'TikTok Shop' }]).suspects, 0);
});

test('decorative aria-hidden text is skipped', () => {
  const r = page([{ text: 'RESEARCH 2026 and the rest of this is English prose', ariaHidden: true }]);
  assert.strictEqual(r.suspects, 0);
});
