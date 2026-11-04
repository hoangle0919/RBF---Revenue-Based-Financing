# Handoff — Simulation Lab reading experience

Branch `codex/bilingual-daily-fx`. New HEAD **`fd2db94`**, one focused commit on
top of `c136e32`. No amend, no push, no merge, no deploy.
`DESIGN-IS-2026-11-04/` is preserved untracked; all five files were read.

## What changed

| brief item | result |
|---|---|
| compact introduction | hero is a title + one line; the 102-word methodology paragraph moved into the detail disclosure |
| simple scenario choice | four starters, all 13 one disclosure away, unchanged |
| one compact fixed-vs-revenue-share comparison | FIX-A and RBF-ILL as two aligned marks, **208px together on a phone** |
| one question at a time | Payment share / Target recovery / Completion; Payments shows ONE named aggregate |
| one scenario-dependent takeaway beside the result | derived from the two displayed values for the current scenario |
| explicit secondary view | one "All four contracts, detailed statistics and methods" panel |

Desktop is a horizontal workspace: scenario column, comparison in the main
area. Phone is one column, scenario then comparison.

## Scientific meaning

- Every number is read from the existing API. **All 13 scenarios × 3 questions
  compared against the API: zero mismatches.**
- Each mark states its kind beside the value. FIX-A: "scheduled payments,
  modelled as paid in full and on time — a benchmark, not observed collections".
- Payment share: payment ÷ GMV, active months only, **average of each path's
  own worst month** — explicitly not a global peak.
- Recovery: month-12 checkpoint, own-target denominator. Completion: 24-month
  horizon, 500-path denominator, and a non-finishing path is censored, not a
  predicted default.
- Takeaway never prewrites a winner. Measured: recovery direction splits
  **7 scenarios to RBF-ILL, 6 to FIX-A**. Payments favours RBF-ILL in all 13 —
  that is what the artifacts say, and the non-affordability qualification is
  what guards it. Flagging it so you can judge the wording.
- The marks are length-encoded values with the number printed beside them. No
  time series, because none exists behind these aggregates.

## Two source defects from E5, fixed

- `apr()` read the raw English `apr_undefined_reason` despite an available
  translation key; it now uses `apiText`. **No registered scenario produces an
  undefined rate**, so this path is latent — pinned by a test, not claimed as
  browser-reproduced.
- The stale comment claiming chart synchronisation is gone.

## Verification — executed

| gate | result |
|---|---|
| `pytest backend/tests -q` | **693 passed, 11 skipped, 0 failed** |
| `check_i18n_fx_state.cjs` | 11 passed, 0 failed |
| `check_prototype_state.cjs` | 9 passed, 0 failed |
| `check_prototype_fx_state.cjs` | 5 passed, 0 failed |
| `test_scan_residual_english.cjs` | 5 passed, 0 failed |
| `check_i18n.py` | parity, 795 / 795, every referenced key resolves |
| protected artifacts + PDFs | **29 files, 0 changed** vs `c136e32` |
| residual-English, Vietnamese | 503 nodes, **0 suspects** |

Also executed: every scenario and question; rapid scenario switching (last
selection wins, one pressed pill, values match API); a forced 500 (error state
shown, content hidden so no stale answer is presented, retry recovers); twelve
deep links (each opens its panel and moves focus); language switching
mid-session (comparison, takeaway, qualifiers and scenario label all repaint,
values unchanged); enlarged text at 16/20/24px root (no clipping, no
horizontal overflow); full-page inspection on a fresh load.

Full-page: **6.0 phone viewports, down from 9.0**, with all 7 panels closed by
default. Clutter is organised, not pushed down.

## Known limitations — stated, not rounded away

1. **At 1366×768 in Vietnamese the second value's box crosses the fold by 4px.**
   The digits render and are legible in the capture, but it is not strictly
   inside. At 1440×900 Vietnamese, and at 1366×768 English, both values and the
   basis are fully inside. I stopped trimming rather than over-tune one width.
2. **Limitations are deliberately NOT collapsed.** I collapsed them, the
   repository's anti-pattern guard failed, and I reverted instead of weakening
   it. `s-limits` is 2050px of the remaining page height, by choice.
3. Inline JS 56,747 B; the file-local budget moves 52,000 → 58,000 with the
   measured number in the test. Not an extraction refactor, per your earlier note.
4. No VoiceOver, no contrast measurement, no screen-reader certification. Focus
   movement was verified programmatically; the `:focus-visible` rule exists and
   the controls match it.
5. Screenshots are JPEG captures; the placement numbers come from measured
   geometry, not from reading the images.

Screenshots: `evidence/redesign/screenshots/*-2026-11-04.jpg`, described in
`README-2026-11-04.md`. Layouts: `design/LAB-READING-LAYOUT.md`.

**This is an implementation for review, not a user-approved design.**
