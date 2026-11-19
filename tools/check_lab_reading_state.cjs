/* Execute the actual Lab presentation/orchestration JavaScript against real
 * backend artifact payloads and a minimal DOM. No browser layout or screen
 * reader claim is made. Python imports lab only (no database or HTTP server).
 * Run: node --test tools/check_lab_reading_state.cjs
 */
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { execFileSync } = require('node:child_process');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const root = join(__dirname, '..');
const html = readFileSync(join(root, 'frontend/lab.html'), 'utf8');
const script = html.match(/<script>\s*("use strict";[\s\S]*?)<\/script>/)[1];
assert.match(script, /\ninit\(\);\s*$/);
const source = script.replace(/\ninit\(\);\s*$/, '\n');
const catalogues = Object.fromEntries(['en', 'vi'].map(lang => [lang,
  JSON.parse(readFileSync(join(root, 'frontend/i18n', lang + '.json'), 'utf8'))]));
const payloads = JSON.parse(execFileSync(process.env.PYTHON || 'python3', ['-c',
  'import json,sys;sys.path.insert(0,"backend");import lab;print(json.dumps({s["key"]:lab.comparison(s["key"]) for s in lab.scenarios()}))'],
  { cwd: root, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' }, encoding: 'utf8' }));
const clone = data => JSON.parse(JSON.stringify(data));
const escape = text => String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function setup(lang = 'en') {
  const nodes = new Map(), listeners = {}, requests = [];
  let document;
  function node(id = '') {
    let text = '', markup = '';
    const n = {
      id, dataset: {}, attrs: {}, hidden: false, open: false, tagName: 'DIV',
      style: {}, value: '', parentElement: null, children: [],
      set textContent(value) { text = String(value); markup = escape(text); },
      get textContent() { return text; },
      set innerHTML(value) { markup = String(value); text = markup.replace(/<[^>]*>/g, ''); },
      get innerHTML() { return markup; },
      setAttribute(k, v) { this.attrs[k] = String(v); },
      getAttribute(k) { return this.attrs[k] ?? null; },
      hasAttribute(k) { return k in this.attrs; },
      removeAttribute(k) { delete this.attrs[k]; },
      addEventListener() {}, querySelector() { return null; },
      querySelectorAll() { return this.children; },
      classList: { toggle() {}, add() {}, remove() {} },
      scrollIntoView() { this.scrolled = true; },
      focus() { document.activeElement = this; },
    };
    return n;
  }
  const get = id => { if (!nodes.has(id)) nodes.set(id, node(id)); return nodes.get(id); };
  const pills = Object.keys(payloads).map(key => { const n = node(); n.dataset.k = key; return n; });
  get('showme').children = ['payments', 'recovery', 'completion'].map(q => {
    const n = node(); n.dataset.q = q; return n;
  });
  document = {
    title: 'Lab', body: node('body'), documentElement: node('html'), activeElement: null,
    getElementById: get, createElement: () => node(), querySelector: () => null,
    addEventListener() {}, querySelectorAll: selector => selector.includes('#scn-groups button') ? pills : [],
  };
  const window = { console: { warn() {} }, matchMedia: () => ({ matches: true }),
    addEventListener: (event, fn) => { listeners[event] = fn; },
    RBF_I18N: { lang, t(key, params = {}) {
      let out = catalogues[this.lang][key] || '';
      for (const [k, v] of Object.entries(params)) out = out.split('{' + k + '}').join(String(v));
      return out;
    } },
  };
  const context = vm.createContext({ document, window, console: window.console,
    location: { hash: '' }, setTimeout() {}, clearTimeout() {},
    getComputedStyle: () => ({ getPropertyValue: () => '' }),
    fetch: url => new Promise(resolve => requests.push({ url, resolve })),
  });
  vm.runInContext(source, context);
  // These secondary renderers are outside this harness's scope. The guided
  // comparison, scenario selector, request/error state and anchor router run
  // unmodified; separate browser tests cover their integration with charts.
  for (const name of ['renderArms', 'renderLegend', 'renderDuration', 'renderDefs',
    'renderFindings', 'renderPanels', 'drawCharts', 'renderProvenance', 'renderUnderreporting']) {
    context[name] = () => {};
  }
  function render(data, question) {
    context.STATE.data = clone(data);
    context.STATE.scenario = data.scenario.key;
    context.selectQuestion(question);
  }
  return { context, get, pills, document, node, requests, render,
    language(value) { window.RBF_I18N.lang = value; listeners['rbf:languagechange'](); },
  };
}
function displayed(s) {
  return [...s.get('pair').innerHTML.matchAll(/class="mark-val mono">([^<]*)</g)].map(m => m[1]);
}
function expected(data, q) {
  return ['FIX-A', 'RBF-ILL'].map(id => {
    const a = data.arms.find(arm => arm.id === id);
    const value = q === 'payments' ? a.burden.max : q === 'recovery' ? a.recovery_ratio['12'] : a.completed_share;
    return value == null ? '—' : (value * 100).toFixed(q === 'payments' ? 2 : 1) + '%';
  });
}
function finish(request, data, status = 200) {
  request.resolve({ ok: status === 200, status, headers: { get: () => '' }, json: async () => data });
}

test('13 scenarios × 3 questions × 2 languages render both API values without drift', () => {
  assert.equal(Object.keys(payloads).length, 13);
  for (const lang of ['en', 'vi']) {
    const s = setup(lang);
    for (const [key, data] of Object.entries(payloads)) {
      for (const question of ['payments', 'recovery', 'completion']) {
        s.render(data, question);
        assert.deepEqual(displayed(s), expected(data, question), lang + '/' + key + '/' + question);
        assert.equal(s.get('compare-scn').textContent, s.context.apiText(data.scenario, 'label'));
        assert.match(s.get('pair').innerHTML, /FIX-A[\s\S]*RBF-ILL/);
        assert.equal(s.get('showme').children.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
        assert.equal(s.get('guided-exclusions').hidden, question !== 'payments');
        assert(s.get('pair-scale').textContent.includes('100%'), 'registered scenarios share the stated 100% scale');
        const widths = [...s.get('pair').innerHTML.matchAll(/style="width:([\d.]+)%"/g)].map(m => m[1]);
        const expectedWidths = ['FIX-A', 'RBF-ILL'].map(id => {
          const a = data.arms.find(a => a.id === id);
          const value = question === 'payments' ? a.burden.max : question === 'recovery' ? a.recovery_ratio['12'] : a.completed_share;
          return (value * 100).toFixed(2);
        });
        assert.deepEqual(widths, expectedWidths, '100% shared bar scale must encode API values directly');
        for (const value of new Set(expected(data, question))) {
          assert(s.get('takeaway-text').textContent.includes(value), 'takeaway value ' + value);
        }
        // Independently derive the winning/equality branch from raw API fields,
        // not from the page's QUESTIONS or renderTakeaway implementation.
        const arms = ['FIX-A', 'RBF-ILL'].map(id => data.arms.find(a => a.id === id));
        const raw = arms.map(a => question === 'payments' ? a.burden.max : question === 'recovery' ? a.recovery_ratio['12'] : a.completed_share);
        const equal = Math.abs(raw[0] - raw[1]) < 1e-12;
        const first = question === 'payments' ? raw[0] <= raw[1] : raw[0] >= raw[1];
        const index = first ? 0 : 1;
        const formatted = expected(data, question);
        const params = equal ? { v: formatted[0] } : question === 'payments'
          ? { low: s.context.apiText(arms[index], 'name'), lowVal: formatted[index], highVal: formatted[1 - index] }
          : question === 'recovery'
            ? { ahead: s.context.apiText(arms[index], 'name'), aheadVal: formatted[index], behindVal: formatted[1 - index] }
            : { more: s.context.apiText(arms[index], 'name'), moreVal: formatted[index], lessVal: formatted[1 - index] };
        const branch = question === 'payments' ? (equal ? 'equal' : 'lower')
          : question === 'recovery' ? (equal ? 'level' : 'ahead') : (equal ? 'equal' : 'more');
        assert.equal(s.get('takeaway-text').textContent,
          s.context.window.RBF_I18N.t('lab.take.' + question + '.' + branch, params),
          'takeaway must identify the correct contract, including scenario-dependent recovery direction');
        assert(!/\{\w+\}/.test(s.get('pair-scope').textContent), 'scope substitutions resolved');
      }
    }
  }
});

test('equal values use the equality branch for all three questions', () => {
  const s = setup();
  const d = clone(payloads.stable);
  for (const a of d.arms) { a.burden.max = .25; a.recovery_ratio['12'] = .25; a.completed_share = .25; }
  for (const q of ['payments', 'recovery', 'completion']) {
    s.render(d, q);
    assert.match(s.get('takeaway-text').textContent, /same share/);
    assert.doesNotMatch(s.get('takeaway-text').textContent, /smaller|further along|More simulated/);
  }
});

test('null headline values are unavailable, never a zero or fabricated winner', () => {
  const s = setup();
  for (const q of ['payments', 'recovery', 'completion']) {
    const d = clone(payloads.stable), a = d.arms.find(x => x.id === 'FIX-A');
    if (q === 'payments') a.burden.max = null;
    else if (q === 'recovery') a.recovery_ratio['12'] = null;
    else a.completed_share = null;
    s.render(d, q);
    assert.equal(displayed(s)[0], '—');
    assert.match(s.get('takeaway-text').textContent, /not defined/);
    assert.doesNotMatch(s.get('pair').innerHTML, /NaN|Infinity/);
  }
});

test('missing burden and recovery objects render unavailable without throwing', () => {
  const s = setup();
  for (const question of ['payments', 'recovery']) {
    const d = clone(payloads.stable), a = d.arms.find(a => a.id === 'FIX-A');
    delete a[question === 'payments' ? 'burden' : 'recovery_ratio'];
    assert.doesNotThrow(() => s.render(d, question));
    assert.equal(displayed(s)[0], '—');
    assert.match(s.get('takeaway-text').textContent, /not defined/);
  }
});

test('two zero values remain zero-length marks and use a finite shared scale', () => {
  const s = setup();
  const d = clone(payloads.stable);
  for (const a of d.arms) { a.burden.max = 0; a.recovery_ratio['12'] = 0; a.completed_share = 0; }
  for (const q of ['payments', 'recovery', 'completion']) {
    s.render(d, q);
    const widths = [...s.get('pair').innerHTML.matchAll(/style="width:([\d.]+)%"/g)].map(m => m[1]);
    assert.deepEqual(widths, ['0.00', '0.00']);
    assert.doesNotMatch(s.get('pair').innerHTML, /NaN|Infinity/);
    assert.match(s.get('takeaway-text').textContent, /same share/);
  }
});

test('an incomplete comparison cannot retain the previous scenario answer', () => {
  const s = setup();
  s.render(payloads.stable, 'payments');
  const stale = s.get('pair').innerHTML;
  const d = clone(payloads.closure_m13);
  d.arms = d.arms.filter(a => a.id !== 'FIX-A');
  const pending = s.context.select('closure_m13');
  finish(s.requests[0], d);
  return pending.then(() => {
    assert(s.get('content').hidden || s.get('pair').innerHTML !== stale,
      'missing arm left the previous comparison visible');
  });
});

test('non-finite headline values display as unavailable, not NaN or Infinity', () => {
  const s = setup();
  for (const q of ['payments', 'recovery', 'completion']) {
    s.render(payloads.stable, q);
    const a = s.context.STATE.data.arms.find(a => a.id === 'FIX-A');
    if (q === 'payments') a.burden.max = NaN;
    else if (q === 'recovery') a.recovery_ratio['12'] = Infinity;
    else a.completed_share = NaN;
    s.context.renderGuided();
    assert.equal(displayed(s)[0], '—');
    assert.match(s.get('takeaway-text').textContent, /not defined/);
  }
});

test('language switch repaints comparison, takeaway, basis and label without changing figures', () => {
  const s = setup();
  s.render(payloads.closure_m13, 'recovery');
  const values = displayed(s), before = ['pair', 'takeaway-text', 'guided-basis', 'compare-scn'].map(id => s.get(id).textContent);
  s.language('vi');
  assert.deepEqual(displayed(s), values);
  ['pair', 'takeaway-text', 'guided-basis', 'compare-scn'].forEach((id, i) => assert.notEqual(s.get(id).textContent, before[i], id));
});

test('slow older response cannot replace the latest scenario, pill or comparison', async () => {
  const s = setup();
  const a = s.context.select('closure_m7'), b = s.context.select('growth');
  finish(s.requests[1], payloads.growth); await b;
  finish(s.requests[0], payloads.closure_m7); await a;
  assert.equal(s.context.STATE.scenario, 'growth');
  assert.deepEqual(displayed(s), expected(payloads.growth, 'payments'));
  assert.deepEqual(s.pills.filter(p => p.attrs['aria-pressed'] === 'true').map(p => p.dataset.k), ['growth']);
  assert.equal(s.get('scn-groups').attrs['aria-busy'], 'false');
  assert.equal(s.get('scenario-select').value, 'growth');
});

test('mobile selector preserves the current scenario label until a new response commits', async () => {
  const s = setup();
  s.context.STATE.scenario = 'stable';
  s.context.renderScenarios(Object.values(payloads).map(d => d.scenario));
  const select = s.get('scenario-select');
  select.value = 'growth'; select.onchange();
  assert.equal(select.value, 'stable');
  assert.equal(s.context.STATE.scenario, 'stable');
  finish(s.requests[0], payloads.growth);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(select.value, 'growth');
  assert.deepEqual(displayed(s), expected(payloads.growth, 'payments'));
});

test('failed current request hides stale answers and does not leak response details', async () => {
  const s = setup();
  s.render(payloads.stable, 'payments'); s.context.show('ready');
  const pending = s.context.select('growth');
  finish(s.requests[0], { detail: 'PRIVATE_RESPONSE_CONTENT' }, 500);
  assert.equal(await pending, false);
  assert(s.get('content').hidden);
  assert.equal(s.get('st-error').hidden, false);
  assert.equal(s.get('err-detail').textContent, catalogues.en['lab.error.5xx']);
  assert(!s.get('err-detail').textContent.includes('PRIVATE'));
});

test('a stale request failure cannot hide the newer successful comparison', async () => {
  const s = setup();
  s.context.show('ready');
  const old = s.context.select('closure_m7'), latest = s.context.select('growth');
  finish(s.requests[1], payloads.growth); await latest;
  finish(s.requests[0], { detail: 'PRIVATE_OLD_FAILURE' }, 500); await old;
  assert.equal(s.get('content').hidden, false);
  assert.equal(s.get('st-error').hidden, true);
  assert.equal(s.context.STATE.scenario, 'growth');
  assert.deepEqual(displayed(s), expected(payloads.growth, 'payments'));
});

test('every supported anchor opens ancestors and moves programmatic focus', () => {
  const s = setup();
  for (const id of ['s-scn', 's-guided', 's-detail', 's-arms', 's-burden', 's-recovery',
    's-dur', 's-hpb', 's-under', 's-find', 's-limits', 's-prov']) {
    const outer = s.node(); outer.tagName = 'DETAILS'; outer.parentElement = s.document.body;
    const target = s.get(id); target.parentElement = outer;
    s.context.location.hash = '#' + id;
    s.context.routeToAnchor();
    assert(outer.open, id);
    assert.equal(s.document.activeElement, target, id);
    assert(target.scrolled, id);
    assert.equal(target.attrs.tabindex, '-1');
  }
});
