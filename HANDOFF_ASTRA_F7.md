# Handoff — Codex review of `3a25c17`, findings F1–F8 complete

Branch `codex/bilingual-daily-fx`, head **`d3fe88e`**. Committed locally only.
Not pushed, not merged, not deployed. The retrospective evaluator gate is still
closed.

## Status by finding

| | Finding | Status |
|---|---|---|
| F1 | USD equivalents not wired to the pages | done (`068ee0a`), verified in browser: 3 amounts on demo, 8 on Lab, exact agreement with the backend |
| F2 | 390px header overflow | done (`aea7957`) |
| F3 | fx single-flight flag could leak on an unexpected error | done (`6723495`), release and publish happen in one lock transition |
| F4 | public error taxonomy could echo exception text | done (`6723495`) |
| F5 | browser/backend cent disagreement | done (`6723495`), BigInt exact arithmetic, half-up, test pins agreement |
| F6 | i18n race + URL language continuity | done (`6723495`), desired-language token + explicit flag |
| F7 | Lab presentation not localized | **done this pass (`d3fe88e`)** — detail below |
| F8 | 390px / viewport regression guard | done (`aea7957`) |

## F7, what was actually built

The Lab rendered prose straight from the API's English fields. The fix is
**additive**: every prose field keeps its English value and gains a sibling
`<field>_key`, plus `<field>_params` / `<field>_param_keys` where a figure is
interpolated, and `text_parts` on findings. `lab.html` resolves them through
`apiText()` / `apiProse()`, which prefer the catalogue entry the API names and
fall back to the API's own English. Nothing was replaced — pinned across all 13
scenarios by `test_the_metadata_is_additive_every_english_field_survives`.

Keyed: metric definitions (6 × 3), assumptions (5), glossary (9 terms + 9
definitions — the term is reader copy, not an id), claim taxonomy (5 × 2),
artifact roles (4), the under-reporting note, arm chart labels.

Catalogues: **729 keys each, in parity**.

Also in F7, per your review:
- An open contract-details panel and its keyboard focus now survive a language
  switch. `renderArms()` rebuilds with `innerHTML`, so state is captured before
  the write and restored after it, keyed by **arm id** rather than position.
- `repaintDynamicCopy()` in `demo.html` now covers `renderStats`,
  `renderCounts`, `renderCharts` and `renderTable`. None of their copy carries a
  `data-i18n` attribute, so the runtime's attribute pass could not reach it;
  without this it stayed in whichever language was active when the dashboard
  last loaded. Guarded on `stats` being non-null so it is skipped before the
  first load rather than throwing.
- The proper-name / identifier allowlist is now committed and documented, as
  `tools/residual_english.json`, with the scanner as
  `tools/scan_residual_english.js`. Every entry records **why** it is exempt.

## The 102-node gap is closed on the Lab page

Run with the committed scanner, every `<details>` expanded:

| Page / state | Rendered text nodes | Suspects |
|---|---|---|
| `/lab?lang=vi`, each of 13 scenarios | 441–460 | **0** |
| `/demo.html?lang=vi` — apply / dashboard / privacy | 21–33 visible | 0 |
| `/?lang=vi` | 127 | 1, documented below |

The scan is a heuristic reporting *suspects*, not verdicts — a Vietnamese
sentence with no diacritic would be missed. Every printed line was read.

## Two defects this pass found in its own earlier work

1. **A re-frozen cap factor.** Keying the *resolved* `chart_label` wrote
   `Revenue-based 1.0945×` into a translation string — re-freezing the exact
   figure `chart_label_fmt` exists in `lab.py` to keep artifact-derived. The
   format is translated now; the factor travels as a parameter. Same for the
   illustrative arm's name. A test caught this, not a reading.
2. **A wrong-shape rewrite.** `renderDefs(d)` already receives
   `metric_definitions` as `d`; a blind replacement introduced
   `d.metric_definitions.*` inside it, which would have thrown at runtime.

## Open, and NOT claimed fixed

- **`<noscript>` fallback is English only** (`index.html`). `<noscript>`
  content is inert while JavaScript runs, so the i18n runtime can never reach
  it; with JavaScript off there is no runtime either. It carries
  `data-i18n="figure.noscript"` for a future server-side language pass.
- **A pre-existing frozen figure in the repo's own English prose.**
  `METRIC_DEFINITIONS["duration_months_mean"]["why"]` quotes a computed share
  ("temp_closure leaves 2.0% of paths incomplete at f = 1.20"); the Vietnamese
  mirrors it verbatim. Exempted **by name** in `test_lab_localization.py` with
  the reason written out, not silently allowed. Fixing it means parameterising
  that sentence from the temp_closure artifact.
- **`SIGNAL_LABEL` in `demo.html` is dead code** holding six English strings;
  nothing reads it. The live why-panel and chips use translated keys. Left as
  out of scope.
- **Number formatting is internally inconsistent** and was deliberately not
  changed: `num()` / `pct()` print a dot decimal in both languages ("13.0
  tháng", "37.87%") while the money formatter follows Vietnamese convention
  ("8.615,00 USD"). Translated prose was normalised to the dot form so a quoted
  figure matches what the page prints beside it, and a test pins that. If you
  want the formatters unified, that is a separate change with its own
  regression surface.
- Not executed: the nine Playwright Lab browser tests, the English viewport
  matrix, `index.html` at all widths. VoiceOver was not used.

## Verification actually run

- `python3 -m pytest backend/tests -q` → **664 passed, 11 skipped**
- `python3 tools/check_i18n.py` → parity, every referenced key resolves
- `node tools/check_i18n_fx_state.cjs` → 11/11
- Every new guard was checked against a deliberately reintroduced defect and
  observed to fail — the two API-label guards, the cap-factor parameter guard,
  the panel-state guard, the dashboard-repaint guard.
- Browser pane against a local server: 13 Lab scenarios in Vietnamese; English
  re-render after a switch; `FIX-A`'s panel stayed open with focus on its
  `<summary>` across the switch; the dashboard repaint was exercised with a
  **stubbed dataset injected in the page**, not real admin data, since that
  needs credentials that were not entered; 8 USD equivalents still rendering,
  so F1 is intact.

## What I'd like reviewed

1. Whether the additive shape is the one you intended, specifically
   `glossary_keyed` and `assumptions_keyed` arriving *beside* the original
   `glossary` dict and `assumptions` string list rather than replacing them.
2. Whether the cap-factor test's scope is the right call. A broader rule — any
   number in a translation string that also appears anywhere in the payload —
   was written, run, and rejected: it collides with month labels (12 / 18 / 24)
   and with hand-typed study assumptions already in the source English, so it
   reported noise. The narrowed rule and that reasoning are both in the
   docstring.
3. Whether the `duration_months_mean.why` exemption should instead be fixed now
   by parameterising the sentence from the temp_closure artifact.
