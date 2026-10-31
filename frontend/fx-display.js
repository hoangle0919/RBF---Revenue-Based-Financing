/* Approximate USD equivalents — presentation only.
 *
 * THE RULE THIS FILE EXISTS TO ENFORCE: the VND value is authoritative and is
 * never derived from, replaced by, or round-tripped through its USD display.
 * Callers pass the ORIGINAL INTEGER VND, never a formatted string scraped from
 * the DOM. Locale formatting differs between languages; the mathematical amount
 * does not, and parsing "185.000.000" back out of a page is how that invariant
 * gets broken.
 *
 * ONE SNAPSHOT PER RENDERED GROUP. A result panel takes a single quote and
 * converts every figure in it with that one rate, so the numbers reconcile with
 * each other and with the single reference date shown beside them. A refresh
 * replaces the whole group atomically. It never changes a VND figure.
 *
 * Converted totals can differ by a cent or two from the sum of individually
 * rounded USD lines. That is explained in the UI, not corrected by adjusting
 * a VND total.
 */
(function (global) {
  'use strict';

  var PREF_KEY = 'rbf.amountDisplay';   // 'vnd' | 'dual'
  var quote = null;                      // last /api/fx payload
  var mode = 'dual';

  // F2: a page left open must not keep presenting an ageing quote as current.
  var REFRESH_MS = 60 * 60 * 1000;       // hourly; NOT high-frequency polling
  var REVALIDATE_AFTER_MS = 15 * 60 * 1000;  // on refocus, if older than this
  var FRESH_MAX_AGE_DAYS = 3;            // mirrors backend/fx.py
  var STALE_MAX_AGE_DAYS = 7;
  var fetchedAtMs = 0;
  var inFlight = false;
  var generation = 0;                    // stale-response guard
  var timer = null;

  function t(key, vars) {
    return (global.RBF_I18N && global.RBF_I18N.t(key, vars)) || '';
  }

  function readPref() {
    try {
      var v = global.localStorage.getItem(PREF_KEY);
      return (v === 'vnd' || v === 'dual') ? v : 'dual';
    } catch (e) { return 'dual'; }
  }
  function writePref(v) {
    try { global.localStorage.setItem(PREF_KEY, v); } catch (e) { /* ignore */ }
  }

  /* ── Exact cents, no binary floating point ───────────────────────────────
   * The previous implementation used Math.round((vnd / rate) * 100) / 100 and
   * claimed agreement with the backend's decimal ROUND_HALF_UP. It did not:
   * 25,125 VND at 25,000 is exactly 1.005, which the backend renders 1.01 and
   * binary float rendered 1.00. Integer arithmetic over BigInt removes the
   * representation error rather than hiding it.
   *
   *   usd      = vnd / (num / 10^k)       where rate = num / 10^k
   *   cents    = vnd * 10^k * 100 / num   rounded half-up
   */
  var MAX_VND = 1e15;                    // generous upper bound, still exact

  function exactUsd(vnd, rateStr) {
    if (typeof BigInt !== 'function') return null;
    // Reject rather than coerce: a non-integer or unsafe amount is a caller
    // error, and a silently rounded display value would hide it.
    var n = typeof vnd === 'string' ? Number(vnd) : vnd;
    if (typeof n !== 'number' || !isFinite(n) || n < 0 || n > MAX_VND) return null;
    if (Math.floor(n) !== n) return null;
    var m = /^(\d+)(?:\.(\d+))?$/.exec(String(rateStr).trim());
    if (!m) return null;
    var frac = m[2] || '';
    var num = BigInt(m[1] + frac);       // rate scaled by 10^k
    if (num <= 0n) return null;
    var scale = 10n ** BigInt(frac.length);

    var numerator = BigInt(n) * scale * 100n;
    var q = numerator / num;
    var r = numerator % num;
    if (r * 2n >= num) q += 1n;          // half-up, positive values only

    var cents = q % 100n;
    var whole = q / 100n;
    return whole.toString() + '.' + cents.toString().padStart(2, '0');
  }

  function groupThousands(decimalStr) {
    var parts = decimalStr.split('.');
    var vi = global.RBF_I18N && global.RBF_I18N.lang === 'vi';
    var sep = vi ? '.' : ',';
    var dec = vi ? ',' : '.';
    return parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, sep) + dec + parts[1];
  }

  function toUsd(vnd) {
    if (!quote || !quote.vnd_per_usd) return null;
    var exact = exactUsd(vnd, quote.vnd_per_usd);
    return exact === null ? null : groupThousands(exact);
  }

  /* F2: age is recomputed from the reference date against the current UTC day,
   * not read once from the server snapshot. A tab open across midnight, or
   * across a failed refresh, must not keep calling a week-old rate fresh. */
  function ageDays() {
    if (!quote || !quote.reference_date) return null;
    var parts = /^(\d{4})-(\d{2})-(\d{2})$/.exec(quote.reference_date);
    if (!parts) return null;
    var ref = Date.UTC(+parts[1], +parts[2] - 1, +parts[3]);
    var now = new Date();
    var today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    return Math.floor((today - ref) / 86400000);
  }

  function effectiveStatus() {
    if (!quote || quote.status === 'unavailable' || !quote.vnd_per_usd) return 'unavailable';
    var age = ageDays();
    if (age === null || age < 0) return 'unavailable';
    if (age <= FRESH_MAX_AGE_DAYS) return 'ok';
    if (age <= STALE_MAX_AGE_DAYS) return 'stale';
    return 'unavailable';                // older than the band: suppress
  }

  function usable() {
    var st = effectiveStatus();
    return st === 'ok' || st === 'stale';
  }

  /** Secondary line for one amount, or '' when USD must be suppressed. */
  function line(vnd) {
    if (mode !== 'dual' || !usable()) return '';
    var usd = toUsd(vnd);
    return usd === null ? '' : t('fx.approx', { usd: usd });
  }

  /** The dated provenance note that must accompany any USD figure. */
  function provenance() {
    if (!usable()) return { text: t('fx.unavailable'), warn: true };
    var parts = [t('fx.refLine', { date: quote.reference_date })];
    if (effectiveStatus() === 'stale') parts.push(t('fx.stale', { days: ageDays() }));
    if (quote.refresh_failed) parts.push(t('fx.cached'));
    return { text: parts.join(' \u00b7 '),
             warn: effectiveStatus() === 'stale' || !!quote.refresh_failed };
  }

  function refresh() {
    // One client refresh at a time; a response from a superseded request is
    // discarded rather than overwriting a newer one.
    if (inFlight) return Promise.resolve(quote);
    inFlight = true;
    var mine = ++generation;
    return fetch('/api/fx', { credentials: 'omit' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (q) {
        if (mine !== generation) return quote;   // superseded
        quote = q; fetchedAtMs = Date.now(); render(); return q;
      })
      .catch(function () {
        if (mine !== generation) return quote;
        // Keep the last quote and let age handling decide; a failed refresh is
        // not evidence the previous rate became wrong.
        if (quote) { quote.refresh_failed = true; } else { quote = null; }
        render(); return quote;
      })
      .then(function (q) { inFlight = false; return q; },
            function () { inFlight = false; return quote; });
  }

  /* Declarative binding: an element carrying data-vnd="<integer>" gets a
   * sibling .fx-line. The integer attribute is the source of truth, so a
   * language switch re-renders from the number and not from the rendered text. */
  function render() {
    global.document.querySelectorAll('[data-vnd]').forEach(function (el) {
      var raw = el.getAttribute('data-vnd');
      var sib = el.nextElementSibling;
      var has = sib && sib.classList && sib.classList.contains('fx-line');
      var txt = line(raw);
      if (!txt) { if (has) sib.remove(); return; }
      if (!has) {
        sib = global.document.createElement('span');
        sib.className = 'fx-line';
        el.insertAdjacentElement('afterend', sib);
      }
      sib.textContent = txt;
    });

    var p = provenance();
    global.document.querySelectorAll('[data-fx-note]').forEach(function (el) {
      el.textContent = (mode === 'dual') ? p.text : '';
      el.classList.toggle('fx-warn', !!p.warn && mode === 'dual');
    });

    global.document.querySelectorAll('[data-fx-option]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-fx-option') === mode ? 'true' : 'false');
    });
  }

  function setMode(next) {
    if (next !== 'vnd' && next !== 'dual') return;
    mode = next;
    writePref(next);
    render();
  }

  function maybeRevalidate() {
    // Only when the page is actually being looked at, and only if what we hold
    // has had time to age. Returning to a tab left open overnight must not keep
    // showing yesterday's quote as current.
    if (global.document.visibilityState === 'hidden') return;
    if (!quote || Date.now() - fetchedAtMs > REVALIDATE_AFTER_MS) refresh();
    else render();   // the day may have rolled over; recompute age either way
  }

  function startLifecycle() {
    if (timer) return;
    timer = global.setInterval(function () {
      if (global.document.visibilityState !== 'hidden') refresh();
    }, REFRESH_MS);
    global.document.addEventListener('visibilitychange', maybeRevalidate);
    global.addEventListener('focus', maybeRevalidate);
  }

  function init() {
    mode = readPref();
    global.document.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('[data-fx-option]') : null;
      if (b) { e.preventDefault(); setMode(b.getAttribute('data-fx-option')); }
    });
    // Labels are language-dependent; the rate is not. Re-render, do not refetch.
    global.addEventListener('rbf:languagechange', render);
    startLifecycle();
    refresh();
  }

  global.RBF_FX = {
    line: line, provenance: provenance, refresh: refresh, render: render,
    setMode: setMode, exactUsd: exactUsd, ageDays: ageDays,
    effectiveStatus: effectiveStatus, maybeRevalidate: maybeRevalidate,
    get mode() { return mode; }, get quote() { return quote; },
    // test seam: inject a quote without a network round-trip
    _setQuoteForTests: function (q, at) { quote = q; fetchedAtMs = at || Date.now(); render(); }
  };

  if (global.document.readyState === 'loading') {
    global.document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})(window);
