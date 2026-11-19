# RBF redesign — implementation plan

Prepared 1 November 2026. Branch `codex/bilingual-daily-fx` @ `c98d02c`.
Layouts: [REDESIGN_WIREFRAMES.md](REDESIGN_WIREFRAMES.md).

This plan covers the **task hierarchy, prototype entry and Lab information
architecture** only. It grants itself no authority to merge, deploy, buy
services, change research findings or build the gated evaluator.

## 0. Reconciliation with the bilingual/FX work

The design audit was taken at `3a25c17`. HEAD has since moved through four
commits of bilingual/FX correctness work (`6723495`, `068ee0a`, `aea7957`,
`d3fe88e`) plus a handoff (`c98d02c`). **Every line reference in the mandate is
stale and was resolved against current code before use.** None of that work is
reset, amended, discarded or duplicated. Design commits stay separate from the
functional-fix commits already on the branch.

The mandate is not read as approval of the FX branch, and the FX commits are not
read as approval of this design.

## 1. Phases

Each phase is one or more reviewable commits. Phases are sequential; a phase
does not start until the previous one's suite run is green.

### Phase A — navigation and prototype entry
| File | Change |
|---|---|
| `frontend/index.html` | hero action block: `[[Try the prototype]]` primary, both paper editions beside it, Lab secondary; move the action block **above** the long context paragraph; add `Prototype` and `Papers` to the desktop nav. **The conceptual figure stays in the hero's right-hand column — no DOM relocation** (one decision, see below and wireframes §1.4) |
| `frontend/institutional.css` | `.intro{align-items:start}` so the copy is not vertically centred against the taller figure cell; compact the intro band using existing spacing/type tokens; style the hero action block; no new tokens, no new theme |
| `frontend/i18n/en.json`, `vi.json` | new keys for the hero action block and nav items, in both catalogues |
| `frontend/demo.html` | retarget the nav's primary button from `go('apply')` to the workbench anchor; rename `Read the methodology` to match its actual target |

**Acceptance for A:** homepage primary prototype and paper actions in the first
viewport at 1366×768 and 1440×900; prototype entry visible at 390×844 and
360×800 without opening the menu; every existing index.html anchor still
resolves.

### Phase B — prototype workbench first
| File | Change |
|---|---|
| `frontend/demo.html` | reorder: compact title + one sentence + one limitation, then `.proof-card` workbench, then the hero essay, `hero-rule`, `data-strip`, and the existing argument / how-it-works sections; add the `#prototype` anchor and route it; foreground revenue / growth / returns with the other three controls behind a `▸ More inputs` disclosure that keeps them in the DOM; rename preset labels to plain descriptions of their actual values |
| `frontend/institutional.css` | two-column workbench on desktop, intentional stack on mobile; 44px minimum touch targets on presets and the disclosure |
| `frontend/i18n/*.json` | preset label keys, disclosure label, the compacted title and limitation copy |

**Preset relabelling**, from the actual values in `HERO_PRESETS`:

| key | current label | actual values | proposed label |
|---|---|---|---|
| `strong` | Strong operator | 185M₫, +22%, 2.8% ret, 4.9★, 1.8% late, 680d | High revenue, low returns |
| `growth` | Fast-growth | 140M₫, +52%, 4.5% ret, 4.7★, 3.5% late, 240d | Fast growth, young store |
| `volatile` | Volatile | 110M₫, −14%, 13% ret, 4.1★, 12% late, 390d | Declining, high returns |
| `thin` | Thin-file | 42M₫, +14%, 9% ret, 4.0★, 9% late, 38d | Small, new store |

"Strong operator" and "Thin-file" read as borrower segments. The proposed labels
describe the *inputs* and claim nothing about creditworthiness.

**Acceptance for B:** presets, controls and the result panel begin in the first
viewport at 1366×768 and 1440×900 without scrolling past an introduction; at
390×844 and 360×800 the presets and at least one meaningful input are visible
initially and the result is reachable within one viewport of scrolling, at
unreduced type size; toggling `More inputs` never changes a hidden control's
value; no write action can fire from a navigation test.

### Phase C — guided Lab
| File | Change |
|---|---|
| `frontend/lab.html` | purpose statement + simulation qualifier; four starter scenarios with `▾ All 13 scenarios`; **ONE `SHOW ME` selector** (Payments / Target recovery / Completion — descriptive labels, no Q numbers) driving one result card and its chart, not a second competing control; the card names all four contracts by descriptive name with the distinguishing term visible and the id as a secondary reference, with statistic, unit, horizon and its own caveat; the ten sections become seven optional panels keeping their existing ids; anchor migration so `#s-burden` and `#s-recovery` drive the selector and the rest open their panel |
| `backend/lab.py` | presentation metadata only — **already done in the correction commit below**: the FIX-A / RBF-ILL pair is named, exact equality is handled, and the share-of-own-target denominator is stated. Phase C adds only translation keys for new copy. No engine, canonical-result, generator or schema change |
| `frontend/i18n/*.json` | question copy, starter scenario labels, panel labels, the corrected summary sentences — in both catalogues |

**Acceptance for C:** scenario selector and the first question/result begin in
the initial desktop viewport; mobile reaches the first comparison promptly;
every metric, scenario and contract still reachable; `#s-scn`, `#s-arms`,
`#s-burden`, `#s-hpb`, `#s-recovery`, `#s-dur`, `#s-under`, `#s-find`,
`#s-limits`, `#s-prov` all still reveal and scroll to their content on load,
reload, back and forward.

### Phase D — integrated verification
No feature work. Responsive, state, keyboard, bilingual and FX verification
across all three pages, with evidence recorded.

### The conceptual diagram — one decision

**It stays in the hero's right-hand column on desktop and renders below the
actions on mobile. No DOM relocation.** Both this plan and the wireframes now
say only that.

`.intro` is `grid-template-columns:1.1fr 1fr` with `.intro-copy` first and
`.contract-figure` second (`institutional.css:32`); at `max-width:820px`
(`institutional.css:216`) it collapses to one column, so on mobile the figure
already renders after the action block.

**Corrected measurement.** An earlier draft of this plan estimated the intro
band at ~480px from the CSS and concluded the action row was already in the
first viewport. That was wrong. Measured in the browser at 1366×768:

| | measured |
|---|---|
| `.intro` band | 127 → 931px (overruns the 768px fold by 163px) |
| `#intro-title` | starts at 330px |
| `.intro-actions` | **starts at 715px — clipped at the fold** |
| `.contract-figure` | 209 → 847px |
| page height | 4339px |

The cause is `align-items:center` vertically centring the shorter copy cell
against the 638px-tall figure cell — exactly the second-column effect Codex
warned about, and the reason a CSS reading got it wrong. So the homepage needs
**priority and compaction**, not priority alone, and the two fixes are
`align-items:start` plus moving the action block above the context paragraph.
Projected lift: 715px → roughly 470px. That is a projection; the measured number
after implementation is what gets reported.

Full table: [evidence/redesign/measured-baseline.md](../evidence/redesign/measured-baseline.md).

## 2. The one backend correctness change, and its scope

`backend/lab.py::_summary` currently reads:

```python
faster = "the fixed arm" if fa["recovery_ratio"].get("12", 0) >= ill["recovery_ratio"].get("12", 0) \
    else "the revenue-based arm"
```

Two defects, both inside the mandate's "presentation metadata/copy" scope:

1. **Equality is mis-stated.** At exact equality `>=` selects "the fixed arm"
   and the sentence asserts it "has recovered more by month 12", which is false.
   **This is latent, not live:** month-12 recovery was computed for all 13
   registered scenarios and no pair is exactly equal (fixed is
   0.923076923076923 in every scenario; the RBF values range 0.443 to 1.0). The
   fix adds an explicit equal branch rather than waiting for an artifact that
   produces a tie.
2. **The pair is not named.** The sentence says "the fixed arm" and "the
   revenue-based arm" while comparing specifically FIX-A against RBF-ILL. Two
   fixed arms and two revenue-based arms exist. The sentence must name the pair.

Nothing else in `lab.py` changes. No engine, no canonical result, no generator
fingerprint, no schema.

### Charts: no invented series

The API exposes burden as **`mean` / `p90` / `p95` / `max`** summary statistics
with **no monthly series**, recovery as **recorded checkpoints at months 12, 18
and 24**, and completion as a single share of 500 paths over the fixed 24-month
window. An earlier draft of the wireframe proposed a "Burden over time" control;
that invented a series the data does not contain and has been removed. The
existing `groupedBars()` renderer (`lab.html:844-905`) is reused unchanged.
`p95` is emitted today and never rendered — it may be shown, but nothing may be
labelled as a time series.

## 3. State checklist

Run on every page, in **both** languages, at every breakpoint in §4.

| State | Homepage | Prototype | Lab |
|---|---|---|---|
| empty / initial | hero renders without JS | workbench renders before first preview returns | loading skeleton |
| loading | — | `hero-foot` loading copy | `#st-loading` |
| error | — | retry button, previous result not shown as current | `#st-error` + retry |
| unavailable | — | — | `#st-unavailable` (artifacts absent) |
| success | — | result panel populated, full-result action enabled | content shown |
| focus visible | every link and button | presets, sliders, disclosure, full-result | scenario buttons, question controls, panels |
| disabled | — | full-result action disabled with no valid current result | — |
| language switch | copy swaps, scroll kept | input values, active result, focus, expanded disclosure all kept | scenario, expanded panels, focus all kept |
| currency switch | — | VND input unchanged, USD display toggles | VND unchanged, USD display toggles |
| stale async | — | older preview response cannot replace newer | older scenario response cannot replace newer |
| reduced motion | reveal animations suppressed | reveal animations suppressed | — |

## 4. Breakpoints to verify

Desktop 1366×768, 1440×900 · tablet 768 · mobile 390×844, 360×800.
Both languages at every size. Screenshots recorded; any unmet target stated
rather than hidden.

## 5. Anchor migration

| Anchor | Today | After |
|---|---|---|
| `#s-scn` … `#s-prov` | top-level section | panel id; deep link must **open** the panel, then scroll and move focus to its heading |
| `/lab#s-arms`, `#s-burden`, `#s-recovery` | linked from `index.html` lab-index | still linked; must resolve into the new panels |
| `/demo.html#privacy` | linked from the footer | unchanged |
| `#prototype` | does not exist | new workbench anchor, routed |

Tested on load, reload, back and forward — a `hashchange` handler alone is not
enough, because the first load fires no `hashchange`.

## 6. Verification evidence to produce

- `python3 -m pytest backend/tests -q` — executed / passed / failed / skipped reported separately
- `python3 tools/check_i18n.py` — catalogue parity and key resolution
- `node tools/check_i18n_fx_state.cjs`
- `node tools/scan_residual_english.js` via the browser on every redesigned page in Vietnamese
- New regression tests for: the `#prototype` route, the `More inputs` disclosure
  not resetting hidden values, every Lab anchor opening its panel, the named
  pair and equality branch in the summary
- SHA-256 of every protected research artifact and publication PDF, **before and
  after**, to show they are untouched
- Screenshots: 5 breakpoints × 2 languages × 3 pages

A clean screenshot is not a pass. Values rendered after the redesign are
compared against the API and artifacts for stable revenue, sustained decline,
temporary interruption and permanent closure, including the incomplete and
negative-rate cases.

## 7. Guardrails held throughout

- No real-data submission, no production database write, no administrator
  notification, no deployment during QA.
- The prototype's scorer influences its terms; it is not described as
  scoring-free or validated.
- The Lab's research simulation stays a separate system from the prototype.
- The proposed retrospective evaluator stays gated and is not presented as
  implemented.
- VoiceOver is not activated and no screen-reader pass is claimed.
- Research artifacts, engines, registered values and publication PDFs unchanged.
- No framework replacement, no new animation library, no promotional metrics.
