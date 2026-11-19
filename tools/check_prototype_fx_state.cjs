/* R4: the prototype's money bindings must not outlive the result they convert.
 *
 * Run: node tools/check_prototype_fx_state.cjs
 *
 * Clearing a result used to set the VND text to a dash while leaving
 * data-vnd in place. fx-display reads the ATTRIBUTE, not the text, so the
 * previous USD amount stayed on screen -- and repainted on the next render() --
 * beside a dash and a "no current result" message. This drives the real
 * bindMoney/unbindMoney/clearHeroResult source out of demo.html rather than a
 * copy of it, so the test cannot drift from the page.
 */
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const DEMO = readFileSync(join(__dirname, '../frontend/demo.html'), 'utf8');

/* ── a DOM stub just large enough for these three functions ─────────────── */
function makeEl(id) {
  return {
    id,
    attrs: {},
    textContent: '',
    className: '',
    nextElementSibling: null,
    classList: { contains: c => false, toggle() {}, add() {}, remove() {} },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; },
    removeAttribute(k) { delete this.attrs[k]; },
    remove() { this.removed = true; },
  };
}

function harness() {
  const ids = ['hd-box', 'hd-word', 'hd-tier', 'hd-limit', 'hd-rate', 'hd-pd',
               'hd-dur', 'hd-apr', 'hero-chips', 'hero-reason',
               'hero-full-link', 'hero-retry', 'hero-foot'];
  const els = {};
  ids.forEach(i => { els[i] = makeEl(i); });

  // the USD line fx-display would have inserted after the advance
  const fxLine = makeEl('fx-line');
  fxLine.className = 'fx-line';
  fxLine.classList = { contains: c => c === 'fx-line' };
  fxLine.textContent = '≈ 12,930.00 USD';
  els['hd-limit'].nextElementSibling = fxLine;
  els['hd-limit'].setAttribute('data-vnd', '185000000');
  els['hd-limit'].textContent = '185,000,000₫';

  const ctx = {
    document: { getElementById: id => els[id] || makeEl(id) },
    setI18nText() {},
    heroLastData: {}, heroLastMs: 1, heroPlaceholderKey: null,
    window: {},
    Number, Math, String, Object,
  };

  // Pull the three real functions out of the page source.
  const grab = name => {
    const i = DEMO.indexOf(`function ${name}(`);
    if (i < 0) throw new Error(`${name} not found in demo.html`);
    const j = DEMO.indexOf('\n}', i);
    return DEMO.slice(i, j + 2);
  };
  const src = [grab('bindMoney'), grab('unbindMoney'), grab('clearHeroResult')].join('\n');
  const fn = new Function('document', 'setI18nText', 'window',
    src + '\nreturn {bindMoney, unbindMoney, clearHeroResult};');
  return { api: fn(ctx.document, ctx.setI18nText, ctx.window), els, fxLine };
}

test('clearHeroResult unbinds data-vnd from every output figure', () => {
  const { api, els } = harness();
  assert.equal(els['hd-limit'].getAttribute('data-vnd'), '185000000');
  api.clearHeroResult('demo.hero.d.unavailable');
  assert.equal(els['hd-limit'].getAttribute('data-vnd'), null,
    'a dash must not keep a USD binding alive');
  for (const id of ['hd-tier', 'hd-limit', 'hd-rate', 'hd-pd', 'hd-dur', 'hd-apr']) {
    assert.equal(els[id].textContent, '—');
    assert.equal(els[id].getAttribute('data-vnd'), null, id);
  }
});

test('clearHeroResult removes the adjacent .fx-line', () => {
  const { api, fxLine } = harness();
  api.clearHeroResult('demo.hero.d.updating');
  assert.equal(fxLine.removed, true,
    'the converted sibling must not outlive the figure it converts');
});

test('bindMoney with an invalid amount unbinds rather than leaving a stale one', () => {
  const { api, els, fxLine } = harness();
  api.bindMoney(els['hd-limit'], null);
  assert.equal(els['hd-limit'].getAttribute('data-vnd'), null);
  assert.equal(fxLine.removed, true);
});

test('bindMoney with a valid amount binds the integer, not the formatted text', () => {
  const { api, els } = harness();
  api.bindMoney(els['hd-limit'], 92500000);
  assert.equal(els['hd-limit'].getAttribute('data-vnd'), '92500000');
});

test('the workbench carries its own dated conversion note and control', () => {
  const card = DEMO.slice(DEMO.indexOf('id="prototype"'), DEMO.indexOf('id="about-this-prototype"'));
  assert.ok(card.includes('data-fx-note'),
    'the workbench must show the reference date and status where the amounts are');
  assert.ok(card.includes('data-fx-option'),
    'and the amount-display control beside them');
});
