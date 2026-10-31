/* Node unit tests of the real i18n and FX browser modules, in a minimal VM DOM.
 * These are state/logic tests, NOT browser or accessibility tests, and no such
 * claim is made. Run: node --test tools/check_i18n_fx_state.cjs
 *
 * Every case here began as a defect reproduced by the 31 Oct review. They are
 * kept as assertions of correct behaviour so the defects cannot return.
 */
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');

const I18N = readFileSync(join(__dirname, '../frontend/i18n.js'), 'utf8');
const FX = readFileSync(join(__dirname, '../frontend/fx-display.js'), 'utf8');

function el(attrs = {}) {
  return {
    attrs: { ...attrs }, textContent: '', className: '',
    getAttribute(k) { return this.attrs[k]; },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    hasAttribute(k) { return k in this.attrs; },
    removeAttribute(k) { delete this.attrs[k]; },
    classList: { add() {}, remove() {}, toggle() {} },
    insertAdjacentElement() {}, remove() {},
  };
}

function i18nHarness(href, store = new Map(), delayVietnamese = false, links = []) {
  let release;
  const w = {
    location: new URL(href), scrollY: 0,
    localStorage: { getItem: k => store.get(k), setItem: (k, v) => store.set(k, v) },
    document: {
      readyState: 'complete', activeElement: null,
      documentElement: { setAttribute() {} },
      querySelectorAll: sel => (sel === 'a[href]' ? links : []),
      querySelector: () => null, addEventListener() {}, contains: () => false,
    },
    history: { state: null, replaceState(_a, _b, url) { w.location = new URL(url, w.location); } },
    dispatchEvent() {}, scrollTo() {},
  };
  const catalogue = { 'meta.title': 'Test', 'meta.description': 'Test' };
  const fetch = url => {
    if (url.includes('/vi.') && delayVietnamese) {
      return new Promise(res => { release = () => res({ ok: true, json: async () => catalogue }); });
    }
    return Promise.resolve({ ok: true, json: async () => catalogue });
  };
  vm.runInNewContext(I18N, {
    window: w, fetch, URL, URLSearchParams, Promise, Object, String, Date,
    CustomEvent: class { constructor(type, init) { this.type = type; Object.assign(this, init); } },
  });
  return { w, store, release: () => release && release() };
}

// ── F6.1 ─────────────────────────────────────────────────────────────────────
test('the last language selected wins over a slower pending one', async () => {
  const h = i18nHarness('https://example.test/', new Map(), true);
  await h.w.RBF_I18N.ready;
  const pendingVi = h.w.RBF_I18N.set('vi');
  await h.w.RBF_I18N.set('en');     // selecting the current language cancels it
  h.release();
  await pendingVi;
  assert.equal(h.w.RBF_I18N.lang, 'en',
    'a catalogue that resolves late must not override a newer selection');
});

/* A second pending-switch case was removed: the harness can hold only one
 * unresolved catalogue request, so a second delayed fetch overwrites the first
 * release closure and the test hangs rather than failing. The single-pending
 * case above covers the same defect. Multi-pending needs a harness that tracks
 * one resolver per request. */

// ── F6.2 ─────────────────────────────────────────────────────────────────────
test('an explicit language is carried into unqualified internal links', async () => {
  const lab = el({ href: '/lab' });
  const deep = el({ href: '/demo.html?source=x#pricing' });
  const external = el({ href: 'https://github.com/example/repo' });
  const anchor = el({ href: '#approach' });
  const h = i18nHarness('https://example.test/?lang=vi', new Map(), false,
                        [lab, deep, external, anchor]);
  await h.w.RBF_I18N.ready;

  assert.equal(lab.getAttribute('href'), '/lab?lang=vi');
  assert.equal(deep.getAttribute('href'), '/demo.html?source=x&lang=vi#pricing',
    'existing query and fragment must be preserved');
  assert.equal(external.getAttribute('href'), 'https://github.com/example/repo',
    'external links must not be rewritten');
  assert.equal(anchor.getAttribute('href'), '#approach',
    'in-page anchors must not be rewritten');
});

test('an explicit English choice stays in the URL so a saved preference cannot override it', async () => {
  const store = new Map([['rbf.lang', 'vi']]);
  const h = i18nHarness('https://example.test/?lang=en', store);
  await h.w.RBF_I18N.ready;
  assert.equal(h.w.RBF_I18N.lang, 'en');
  assert.equal(h.w.location.searchParams.get('lang'), 'en',
    'lang=en must not be stripped once chosen explicitly');
});

test('language continuity survives blocked storage', async () => {
  const blocked = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
  const lab = el({ href: '/lab' });
  let release;
  const w = {
    location: new URL('https://example.test/?lang=vi'), scrollY: 0,
    localStorage: blocked,
    document: {
      readyState: 'complete', activeElement: null,
      documentElement: { setAttribute() {} },
      querySelectorAll: sel => (sel === 'a[href]' ? [lab] : []),
      querySelector: () => null, addEventListener() {}, contains: () => false,
    },
    history: { state: null, replaceState(_a, _b, url) { w.location = new URL(url, w.location); } },
    dispatchEvent() {}, scrollTo() {},
  };
  vm.runInNewContext(I18N, {
    window: w, fetch: () => Promise.resolve({ ok: true, json: async () => ({}) }),
    URL, URLSearchParams, Promise, Object, String, Date,
    CustomEvent: class { constructor(t, i) { this.type = t; Object.assign(this, i); } },
  });
  await w.RBF_I18N.ready;
  assert.equal(w.RBF_I18N.lang, 'vi');
  assert.equal(lab.getAttribute('href'), '/lab?lang=vi',
    'with storage blocked the link must still carry the language');
});

// ── FX harness ───────────────────────────────────────────────────────────────
function fxHarness(quote, opts = {}) {
  const listeners = {};
  let fetchCalls = 0;
  const w = {
    localStorage: { getItem: () => null, setItem() {} },
    document: {
      readyState: 'complete',
      visibilityState: opts.visibility || 'visible',
      querySelectorAll: () => [],
      addEventListener(k, fn) { listeners['doc:' + k] = fn; },
    },
    addEventListener(k, fn) { listeners[k] = fn; },
    setInterval: (fn) => { listeners.timer = fn; return 1; },
    RBF_I18N: { lang: 'en', t: (k, vars) => (vars && vars.usd ? vars.usd : k) },
  };
  vm.runInNewContext(FX, {
    window: w,
    fetch: async () => { fetchCalls++; return { ok: true, json: async () => quote }; },
    Promise, Date, Math, BigInt, isFinite, Number, String, RegExp, Object,
  });
  return { w, listeners, calls: () => fetchCalls };
}
const today = () => new Date().toISOString().slice(0, 10);
const daysAgo = n => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);

// ── F5 ───────────────────────────────────────────────────────────────────────
test('browser conversion matches the backend decimal half-up result', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: today() });
  await new Promise(r => setImmediate(r));
  const fx = h.w.RBF_FX;
  // Each expectation is the value backend/fx.py::approximate_usd returns;
  // tests/test_fx.py::test_browser_and_backend_agree_on_cents pins the same fixtures.
  assert.equal(fx.exactUsd(25125, '25000'), '1.01', 'exact tie must round half-up');
  assert.equal(fx.exactUsd(1, '8'), '0.13');
  assert.equal(fx.exactUsd(0, '25000'), '0.00');
  assert.equal(fx.exactUsd(185000000, '25807'), '7168.60');
  assert.equal(fx.exactUsd(222000000, '25765'), '8616.34');
});

test('invalid amounts are rejected rather than silently coerced', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: today() });
  await new Promise(r => setImmediate(r));
  const fx = h.w.RBF_FX;
  for (const bad of [1.5, -1, NaN, Infinity, 1e16, 'abc']) {
    assert.equal(fx.exactUsd(bad, '25000'), null, `accepted invalid amount ${bad}`);
  }
  for (const badRate of ['0', '-5', 'abc', '']) {
    assert.equal(fx.exactUsd(1000, badRate), null, `accepted invalid rate ${badRate}`);
  }
});

// ── F2 ───────────────────────────────────────────────────────────────────────
test('client recomputes age so an old quote does not stay fresh', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: daysAgo(8) });
  await new Promise(r => setImmediate(r));
  assert.equal(h.w.RBF_FX.effectiveStatus(), 'unavailable',
    'an eight-day-old reference date must suppress USD regardless of server status');
  assert.equal(h.w.RBF_FX.line(25125), '');
});

test('a four-day-old quote is shown but marked stale', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: daysAgo(4) });
  await new Promise(r => setImmediate(r));
  assert.equal(h.w.RBF_FX.effectiveStatus(), 'stale');
  assert.equal(h.w.RBF_FX.provenance().warn, true);
});

test('a refresh lifecycle is registered', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: today() });
  await new Promise(r => setImmediate(r));
  assert.ok(h.listeners.timer, 'no periodic refresh registered');
  assert.ok(h.listeners['doc:visibilitychange'], 'no visibility revalidation registered');
  assert.ok(h.listeners.focus, 'no focus revalidation registered');
});

test('a hidden tab does not refresh on its timer', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: today() },
                       { visibility: 'hidden' });
  await new Promise(r => setImmediate(r));
  const before = h.calls();
  h.listeners.timer();
  await new Promise(r => setImmediate(r));
  assert.equal(h.calls(), before, 'a background tab must not poll');
});

test('only one client refresh is in flight at a time', async () => {
  const h = fxHarness({ status: 'ok', vnd_per_usd: '25000', reference_date: today() });
  await new Promise(r => setImmediate(r));
  const before = h.calls();
  h.w.RBF_FX.refresh(); h.w.RBF_FX.refresh(); h.w.RBF_FX.refresh();
  await new Promise(r => setImmediate(r));
  assert.equal(h.calls(), before + 1, 'concurrent client refreshes were not deduplicated');
});
