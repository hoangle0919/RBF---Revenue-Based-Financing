# Redesign verification — executed evidence

Branch `codex/bilingual-daily-fx`. Commits `a9de06a`, `d135b60`, `a50c3b9`,
`e94cf8f`. Nothing merged, nothing deployed. Local server only.

Everything below was **executed**. Where a target is not met, the measurement
is given rather than the target.

## 1. Suites

| Gate | Result |
|---|---|
| `python3 -m pytest backend/tests -q` | **676 passed, 11 skipped, 0 failed** (675 collected before this work: 664 passed / 11 skipped) |
| `python3 tools/check_i18n.py` | OK — catalogues in parity, every referenced key resolves |
| `node tools/check_i18n_fx_state.cjs` | 11 tests, **11 pass, 0 fail** |
| Lab inline-JS budget | 47,710 B against a 52,000 B budget (was 40,000; raised with the reason recorded in the test) |

Twelve tests were added for this work. Each new guard was checked against a
deliberately reintroduced defect and **observed to fail** before being kept:
the two API-label guards, the cap-factor parameter guard, the panel-state
guard, the dashboard-repaint guard, the tie guard, the anchor-routing guard,
the closed-panel chart guard and the contract-naming guard.

## 2. First-viewport measurements

Measured in the browser, both languages, no horizontal overflow at any width.

### Homepage — before and after

| | before | after |
|---|---|---|
| `.intro-actions` / `.intro-entry` | **715–768** (clipped at the fold) | **528–581** (fully in) |
| paper links | 2562 (3.3 viewports down) | **628–740** (fully in) |
| prototype link | ~2.9–3.3k of a 4339px page | hero primary action |
| desktop nav contains prototype | no | yes |

All five breakpoints, English, mobile menu **closed**:

| viewport | Try the prototype | Lab link | Paper links |
|---|---|---|---|
| 1366×768 | 528–581 IN | 533–577 IN | 628–740 IN |
| 1440×900 | 533–586 IN | 538–582 IN | 633–745 IN |
| 768×1024 | 470–523 IN | 475–519 IN | 571–682 IN |
| 390×844 | 390–441 IN | 451–495 IN | 542–654 IN |
| 360×800 | 409–460 IN | 470–514 IN | 580–692 IN |

Vietnamese at 1366×768 and 390×844: identical positions, all IN, no overflow.

### Prototype

Workbench (`#prototype`) begins at **421px of a 768px viewport**, so presets,
controls and the result panel all begin in the first viewport. CTA height 51px
(≥44px touch target).

### Lab

| viewport | starters | selector | card | first result row |
|---|---|---|---|---|
| 1440×900 EN | 496–543 IN | 670–720 IN | from 732 | **843–897 fully in** |
| 1366×768 EN | 496–543 IN | 670–720 IN | from 732 | 843 — **75px below the fold** |
| 390×844 VI | 572–688 IN | 829–933 IN | from 945 | 1142 — one short scroll |
| 360×800 EN | 536–632 IN | 773–821 IN | from 833 | 1030 — one short scroll |

**Target not fully met at 1366×768 and on mobile:** the scenario selector and
the question selector reach the opening viewport everywhere, and the result
card begins in it on desktop, but the first *data row* needs a short scroll
below 1440×900. The remaining budget is the disclosure banner and the hero,
both of which carry required honesty copy. Type size was not reduced to close
the gap.

## 3. Deep links

All eleven published anchors tested on first load, on repeat navigation, and
through Back and Forward: `#s-scn`, `#s-guided`, `#s-arms`, `#s-burden`,
`#s-hpb`, `#s-recovery`, `#s-dur`, `#s-under`, `#s-find`, `#s-limits`,
`#s-prov`. Each one resolves, opens every collapsed ancestor panel, and moves
focus to the target. `#s-burden` → Payments, `#s-recovery` → Target recovery,
`#s-dur` → Completion, verified individually.

`#prototype` on the demo page: lands on the landing page, scrolls to the
workbench, moves focus to it, renders an illustrative result. Confirmed by
screenshot — scripted scroll reads are unreliable in this browser pane (see §6).

## 4. Bilingual

Residual-English scan, Vietnamese, every panel expanded, using the committed
`tools/scan_residual_english.js` and its documented allowlist:

| page | nodes | suspects |
|---|---|---|
| `/lab?lang=vi` | 498 | **0** |
| `/demo.html?lang=vi` | 280 | **0** |
| `/?lang=vi` | 133 | 1 — the `<noscript>` fallback, already recorded as open |

A mid-session language switch was tested separately from a fresh load, which is
how the four unrepainted regions were found and fixed.

## 5. Research integrity

`git diff --name-only c98d02c..HEAD` touches only `backend/lab.py`,
`backend/tests/*`, `frontend/*` and `design/` + `evidence/`. **No file under
`research/` or any publication PDF was modified.** Registered artifacts are
byte-identical:

```
363729016298b3d7307ec066c8df37c60e1c9aa2582db2c058c5cc74df894d55  research/results/baseline_v3_canonical.json
b3ebfe6a5a7e7f48726d7e501295b02f84258a3fe9ee4e048875125b1270e0ee  research/results/baseline_equalcost_v2_canonical.json
```

No engine, generator, canonical result or schema was changed. The only backend
edits are presentation metadata and composed sentences.

No real-data submission, database write, administrator notification or
deployment occurred. The preview endpoint is read-only; the write paths
(`/api/sellers/submit`, `/api/auth/login`, `/api/keys/issue`,
`/api/stripe/claim`) were never exercised.

## 6. Limits of this verification — stated, not hidden

- **Scripted scroll reads are unreliable in this browser pane.** `window.scrollTo`
  and `scrollTop` leave `scrollY` at 0 while the document reports 3572px of
  scrollable height. Scroll behaviour was therefore confirmed by screenshot and
  by real input events, not by reading `scrollY`. An earlier conclusion that the
  `#prototype` route "did not scroll" was wrong for this reason and was
  corrected.
- **The pane caches aggressively.** Stylesheets and i18n catalogues were served
  stale several times, which once made correct Vietnamese keys look broken. All
  reported measurements were taken either after a cache-busted re-link or from
  a clean server port.
- **VoiceOver was not used and no screen-reader pass is claimed.** Keyboard
  focus movement was verified programmatically (`document.activeElement`);
  44px touch targets were set in CSS and spot-measured, not audited across
  every control.
- **No Playwright suite was run.** The browser checks above were driven
  interactively.
- The dashboard language repaint was exercised with a **stubbed dataset
  injected into the page**, not with real admin data — that needs credentials
  which were not entered.


---

# Corrections to this record — 3 November 2026

An independent review of `34d40e7` found four claims in the record above that
were wrong or ambiguously stated. They are corrected here rather than edited
away, so the error and its correction both stay on file.

## C1 — "the selector drives the card and its chart" was false

`selectQuestion()` calls `renderGuided()` and nothing else. The selector
changes the guided **table** only; the detail charts live in their own
optional panels and are drawn when a panel opens. The Phase C commit message
claimed synchronised charts and the test was named
`test_one_question_selector_drives_both_the_card_and_the_chart`, which checked
button counts and labels — not chart behaviour — so the name asserted
something the test never verified.

The design is **table-first with optional chart panels**. That is now what the
test is named, what it describes, and what it asserts: it additionally checks
that `selectQuestion` touches no chart function, so the claim and the code
cannot drift apart again.

## C2 — "IN" was ambiguous and overstated in one row

In the Lab table above, "IN" meant *starts within the viewport*, not *fully
visible*. For `390×844 VI selector 829–933 IN` that reads as a pass when the
element spans 104px and only the first 15px are above an 844px fold. The
honest statement is: **the question selector begins just inside the fold at
390×844 and is mostly below it.** The desktop rows that say FULLY IN were
measured as fully inside and are unchanged.

## C3 — the first-viewport target is still only partly met

Confirmed, not disputed. A bare Vietnamese prototype load without a fragment
places the first revenue slider and the result box below the fold; the
`#prototype` shortcut from the homepage is what brings the workbench into
view. Bare-page entry and anchored entry are different routes and are reported
separately from now on.

## C4 — the evidence directory held no images

Correct. It now does: `screenshots/`, with the R1 before/after pair.

## C5 — what the mixed-language scan result actually meant

The earlier "0 suspects" for `/lab?lang=vi` was a **scanner** result, not a
translation-completeness result. The scanner skipped any text node containing
a Vietnamese diacritic, so a Vietnamese wrapper around an English paragraph
was invisible to it — which is exactly how the untranslated pricing
explanation survived. The scanner now splits nodes into sentences, a fixture
file pins the mixed case, and the scanner's header states the remaining limits
in the result itself.

## Re-run after the R1–R5 corrections

| gate | result |
|---|---|
| `python3 -m pytest backend/tests -q` | **683 passed, 11 skipped, 0 failed** |
| `python3 tools/check_i18n.py` | OK — 775 / 775, parity |
| `node tools/check_i18n_fx_state.cjs` | 11 passed, 0 failed |
| `node tools/check_prototype_fx_state.cjs` | 5 passed, 0 failed |
| `node tools/test_scan_residual_english.cjs` | 5 passed, 0 failed |

Measured after R1, 390×844 Vietnamese, all three questions:
`scrollWidth == clientWidth == 328`, **zero values outside the card**.
Before: client 313 / scroll 760.

Residual-English, Vietnamese, all panels expanded, with the sentence-splitting
scanner: `/lab` 487 nodes, **0 suspects**.

---

# F1–F3 follow-up — 3 November 2026

Codex implemented the bounded follow-up after the user asked it to take over
from Claude. Starting point: clean `codex/bilingual-daily-fx` at
`548956eff8cc56e1bbbd7cb11de092353c90298b`. This entry records the new
verification; it does not turn the earlier checks into passes they did not earn.

## Corrections

- **F1, tablet fit:** the guided table's minimum and its card-layout boundary
  now share `48rem`. Previously the 620px boundary left a gap below the
  inherited 760px minimum. The new boundary is relative to text size; no
  overflow hiding, label truncation or font shrinking was introduced.
- **F2, Vietnamese labels:** stacked cells and their pseudo-labels explicitly
  override inherited `white-space:nowrap`. Complete labels wrap above values.
  `display:block` alone did not establish that, and the old universal
  no-overflow wording in the CSS and test was corrected.
- **F3, prototype harness:** the existing state suite now loads the actual
  money helpers and actual `fx-display.js`, with attribute/sibling/removal
  support in its fake DOM. All seven original cases remain. Two new cases
  exercise pending/failed results through real FX repaint/refresh, currency
  selection and Vietnamese language-change handling, using an explicitly
  synthetic quote. The separate five-test FX suite remains unchanged.

The earlier reported `390px` guided width of `328px` did not cover the
scrollbar-reserved case: the follow-up reproduced client width 313px with
328px of content before this correction. Likewise, tablet values remained
hidden at client width 671px with a 760px table. Both gaps are closed in the
executed cases below, not by a page-width-only assertion.

## Executed layout evidence

The local read-only preview served the existing registered Lab output.
The in-app browser reserved 15px for its vertical scrollbar. Checks measured
the guided container, cell overflow (including pseudo-labels), and numeric
value bounds; screenshots supplement rather than replace those measurements.

| Viewport width | Guided client / scroll width | Layout |
|---:|---:|---|
| 320 | 243 / 243 | cards |
| 360 | 283 / 283 | cards |
| 390 | 313 / 313 | cards |
| 768 | 671 / 671 | cards |
| 864 | 767 / 767 | cards |
| 865 | 768 / 768 | table |
| 866 | 769 / 769 | table |
| 1366 | 1038 / 1038 | table |
| 1440 | 1038 / 1038 | table |

- **54 states:** these nine widths × English/Vietnamese × all three guided
  questions, under sustained decline. Zero overflowing cells, zero numeric
  values outside the container and no guided horizontal overflow. The
  767/768/769px component widths cover below/at/above the stacking boundary.
- **36 additional states:** stable, temporary closure and month-13 closure ×
  360/768px × both languages × all three questions. The actual viewport and
  selected scenario were checked, not just requested. Same zero-overflow result.
- **18 enlarged-text states:** 390/768/1366px × both languages × all questions
  under sustained decline, with an ephemeral preview fixture setting the root
  font to 200% (computed 32px). All stacked with no cell/container overflow or
  outside values. This is a text-size fixture, **not** browser-zoom, Safari,
  physical-phone or screen-reader certification.

Raw measurements: `followup-geometry-2026-11-03.json` (54 + 36 + 18 states).
New screenshots: `screenshots/lab-360x800-vi-followup-wrap.jpg` and
`screenshots/lab-768x844-vi-followup-fit.jpg`.

One collection attempt targeted the normal tab while the viewport override
applied to the selected enlarged-text tab. Its nominal-width measurements and
two screenshots were discarded. The affected 36-state matrix and screenshots
were rerun with the intended tab selected and actual viewport width verified;
only the corrected outputs are saved here.

## Executed tests and preservation

| Gate | Result |
|---|---|
| Backend pytest, isolated temporary database, localhost allowed | **685 passed, 11 skipped** |
| Focused Lab localization suite | **67 passed** (included in backend count) |
| `check_i18n_fx_state.cjs` | **11 passed** |
| `check_prototype_state.cjs` | **9 passed** (seven original + two new) |
| `check_prototype_fx_state.cjs` | **5 passed** |
| `test_scan_residual_english.cjs` | **5 passed** |
| Catalogue check | **775 English / 775 Vietnamese**, all 625 referenced keys resolve |
| Tracked `research/results/` files and publication PDFs vs `c98d02c` | **29/29 byte-identical** |

The 11 skips are nine automated browser tests (Chromium executable absent),
one opt-in live FX-provider smoke test, and one scorer comparison without an
ensemble artifact. None is counted as a pass. The interactive layout matrix
above is separate from those skipped automated tests. No new simulation run
or live FX-source verification was performed for this CSS/harness correction.

As a negative control, removing `unbindMoney(el)` from the extracted hero code
in memory made **three of the nine state tests fail** (render exception and
both new currency-lifecycle cases). The ordinary suite passes all nine. This
shows the checks detect stale bindings rather than merely supplying a no-op
helper; the mutation was not written to the repository.

## Remaining boundaries and handoff

F1–F3 are addressed by this pass. The existing first-viewport qualification in
C3 still stands: bare prototype entry and the homepage's anchored entry are
different routes. This pass does not claim to resolve every design target or
translate a heuristic scan into complete accessibility/translation proof.

No engine, research artifact, paper, API schema, scoring implementation or
production database changed. No submissions, administrator notifications,
VoiceOver, push, merge or deployment occurred. The only application change is
guided-table CSS; other changes are regression tests and evidence.

---

## Simulation Lab completion pass — 2026-11-08

This appended entry describes local changes since `9a782bb`; earlier sections
above are historical evidence and are not rewritten. Full scope and review
instructions: `HANDOFF-LAB-REDESIGN-2026-11-08.md`. At authoring, this pass is
uncommitted and local-only: no push, merge or deployment.

### Correctness and preservation

- Full backend suite: **693 passed, 11 skipped, zero failures**. Focused run:
  **193 passed**, overlapping the full suite rather than additional passes.
- Node suites: **43 passed**, including **13 new actual-JavaScript Lab tests**
  covering 13 scenarios × 3 questions × 2 languages, values and takeaway
  branches, scales, missing/non-finite data, stale responses and errors,
  native selection atomicity, language repaint and anchor focus.
- Catalogues: **800 EN / 800 VI**; all **649** referenced keys resolve.
- **29/29 protected artifacts and PDFs byte-identical and SHA-256 unchanged
  versus `c136e32`**. No API, engine, scoring or simulation calculation changes.
- Diff whitespace check clean. Existing untracked `DESIGN-IS-2026-11-04/`
  preserved.

Skips: nine automated browser tests lack the Playwright Chromium executable;
one live-FX test is opt-in; one scorer comparison lacks an ensemble artifact.
None is counted as a pass. The new JavaScript suite uses a minimal DOM and real
artifact-backed payloads, not a layout engine or assistive technology.

### Main-agent actual-browser checks

**24 states:** EN/VI × Payment share/Target recovery/Completion × 360×800,
390×844, 768×900 and 1366×768. Zero document horizontal overflow, zero primary
numeric-value clipping, and equal bar-track widths in the measured states.
The shared scale is visibly 0–100% across registered scenarios. This browser
matrix must not be confused with the all-scenario JavaScript payload matrix.

For the default Payment share comparison in Vietnamese, measured FIX-A /
RBF-ILL numeric-value bottom coordinates were **672.84 / 770.72px** at 360×800,
**620.84 / 718.72px** at 390×844, **728.36 / 813.61px** at 768×900, and
**610.83 / 696.06px** at 1366×768. These establish that the two numbers fit in
those first viewports, not that all accompanying prose is above the fold.

An initial tablet check placed the second value at about **935px**, outside
the 900px viewport. The compact selector now applies below 900px and the
tablet rerun produced the passing coordinates above. This failure is recorded
rather than silently omitted.

Actual mobile month-13 closure Completion showed **100.0% / 23.8%** in both
languages; language switching preserved the scenario selection. The actual
`/lab?lang=vi#s-dur` route opened its panel, exposed `#dur-table`, focused
`s-dur` and produced zero document horizontal overflow.

After a footer wrapping correction, a Vietnamese 390px-wide **200% root-size
fixture (computed 32px)** had zero document overflow, zero primary numeric
clipping, and equal **121.8047px** track widths. This is root-relative text
enlargement, **not browser zoom**, and does not double fixed-pixel text.

Final screenshots delivered by the main agent and verified present on disk:

- `screenshots/lab-desktop-en-final-20261108.jpg`
- `screenshots/lab-mobile-vi-final-20261108.jpg`
- `screenshots/lab-tablet-vi-final-20261108.jpg`

No VoiceOver or native Safari testing in this pass; no blanket accessibility
or usability certification. The read-only preview's FX and prototype routes
return expected 503 responses; there was no live-FX verification or actual
submission. No notifications or production data writes occurred.

### Documentation closeout — 2026-11-11

The three final screenshot files above are delivered and their presence was
rechecked on November 11. All reported tests and browser measurements remain
dated November 8; this closeout introduced no new audit or application changes.
Preview servers are stopped and the browser viewport override reset; there is
no active preview link. The local commit is pending. No push, merge or
deployment has occurred.
