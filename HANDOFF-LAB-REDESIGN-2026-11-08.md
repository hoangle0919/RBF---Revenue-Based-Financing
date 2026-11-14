# Handoff — Simulation Lab completion pass, 2026-11-08

Repository: `/Users/hoanglh/RBF-Revenue-Based-Financing/worktrees/bilingual-daily-fx`.
Branch: `codex/bilingual-daily-fx`. Review base: `9a782bb`; original redesign
baseline: `c136e32`. This record describes local working-tree changes after
`9a782bb`. At authoring, this pass has not been committed, pushed, merged or
deployed. Preserve the existing untracked `DESIGN-IS-2026-11-04/` audit folder.

## Outcome and scope

The existing two-contract comparison is retained and finished, not replaced by
another prototype. The primary result is FIX-A versus RBF-ILL, one question
at a time, with all four contracts and full methods still available in detail.

- `frontend/lab.html`: compact Lab-local hero; a native all-13-scenario selector
  below the desktop workspace breakpoint; compact phone navigation; visibly
  labelled shared bar scale; equal-width tracks; active-month exclusions;
  missing/non-finite value handling; pending-request busy state on the primary
  comparison and selector; optional research panels closed by default without
  collapsing assumptions or limitations; enlarged-text footer wrapping.
- `frontend/i18n/en.json` and `vi.json`: matching bilingual labels and concise
  disclosure text. Pair selection now explains the actual match: principal,
  total repayment and term on the reference path, isolating payment timing.
  This is not an equal-APR claim or the separate RBF-EQ pricing exercise.
- `backend/tests/test_lab_localization.py`: checks the explicit matching basis.
- `tools/check_lab_reading_state.cjs`: 13 regression tests execute the actual
  page JavaScript against real backend artifact payloads in a minimal DOM.
- `design/LAB-READING-LAYOUT.md`: completion plan added to the earlier layouts.

The bars use the same labelled 0–100% scale for every registered scenario.
Future values above 100% expand both tracks together to a disclosed bound,
rather than silently clipping. The mobile selector keeps the old label with
the old figures until the latest successful response commits both together.

Scientific boundaries remain visible: simulation only; fixed scheduled-payment
benchmark assumed paid fully and on time; payment divided by GMV; mean of each
path's peak, not a global peak; zero-revenue and post-completion months excluded;
month-12 own-target recovery; 500 paths and a 24-month completion horizon;
non-completion is not a default prediction; lower payment share does not prove
affordability. No invented series, universal winner or observed-outcome claim
was introduced. No API, engine, scoring or financing calculation changed.

## Executed checks

| Gate | Result |
|---|---|
| Full backend suite | 693 passed, 11 skipped, no failures |
| Focused suite | 193 passed; not additional to the full-suite count |
| Node suites | 43 passed, including 13 new actual-JavaScript Lab tests |
| Catalogue validation | 800 EN / 800 VI entries; all 649 referenced keys resolve |
| Protected research artifacts and PDFs vs `c136e32` | 29/29 byte-for-byte and SHA-256 unchanged |
| Diff whitespace check | Clean |

The 11 skips are nine automated browser tests because the Playwright Chromium
executable is absent, one opt-in live-FX test, and one comparison requiring an
absent ensemble artifact. Skips are not passes. The 13 new tests cover all
13 scenarios × 3 questions × 2 languages, value parity, correct takeaway
direction/equality, shared scales, missing/non-finite data, stale responses,
safe failures, mobile selector atomicity, language repaint and anchor focus.
The minimal-DOM suite is not a browser-layout or assistive-technology test.

## Actual-browser evidence

The main agent measured 24 states: both languages × three questions × four
viewports (360×800, 390×844, 768×900 and 1366×768). All measured states had
zero document horizontal overflow, zero primary numeric-value clipping and
equal track widths. This matrix concerns the primary comparison, not a claim
that every possible page state or all 13 scenarios received browser QA.

Default Payment share, Vietnamese, first-viewport numeric-value bottoms:

| Viewport | FIX-A bottom | RBF-ILL bottom |
|---|---:|---:|
| 360×800 | 672.84 px | 770.72 px |
| 390×844 | 620.84 px | 718.72 px |
| 768×900 | 728.36 px | 813.61 px |
| 1366×768 | 610.83 px | 696.06 px |

The initial tablet Vietnamese result put the second value at about 935px,
below a 900px viewport. Extending the compact selector to widths below 900px
corrected that failure; the table above records the rerun, not the failed
layout. Both values fitting does not imply every qualification and takeaway
fits above the fold.

Additional browser checks:

- Month-13 closure Completion displayed 100.0% / 23.8% correctly on mobile in
  EN and VI. Switching language preserved the selected scenario.
- A 390px-wide Vietnamese fixture with root font size 32px (200%) had zero
  document overflow, zero primary numeric-value clipping and equal track widths
  of 121.8047px after the footer wrapping correction. This is root-relative
  enlargement, not actual browser zoom or proof that fixed-pixel text doubled.
- `/lab?lang=vi#s-dur` opened the settlement panel, exposed `#dur-table`, moved
  focus to `s-dur`, and had no document horizontal overflow.

Final screenshots delivered by the main agent and verified present on disk:

- `evidence/redesign/screenshots/lab-desktop-en-final-20261108.jpg`
- `evidence/redesign/screenshots/lab-mobile-vi-final-20261108.jpg`
- `evidence/redesign/screenshots/lab-tablet-vi-final-20261108.jpg`

## Limits and local-only status

No VoiceOver or native Safari testing was performed in this pass. Geometry,
automated tests and screenshots do not establish user comprehension or complete
accessibility. The read-only local preview intentionally returns 503 for FX
and prototype execution routes; those responses are not production failures
or evidence of live-provider verification. No actual submission, notification,
production database mutation, push, merge or deployment occurred.

Earlier handoffs and verification sections remain historical records; their
counts and layouts must not be presented as this pass's current measurements.

## Closeout note — 2026-11-11

All three final screenshot files listed above are delivered and their presence
was rechecked on November 11. The test and browser measurements remain the
November 8 results; no new audit or application changes were made for this
documentation closeout. The preview servers are stopped and the browser
viewport override reset, so no active preview link is part of the handoff.
The local commit is pending; nothing has been pushed, merged or deployed.

## Review prompt for Claude

## Codex takeover review — 2026-11-13

Reviewed committed implementation `9d4e754` against `9a782bb`, including the
primary comparison, translation changes, regression harness, and the three
saved final screenshots. No new actionable blocking defect was found in this
bounded review. This is a follow-up review by the implementing assistant, not
independent external approval or user acceptance of the design.

Fresh verification:

- All five Node suites: **43 passed**. Catalogue check: **800 EN / 800 VI**,
  all **649 referenced keys** resolve.
- Full backend run: **693 passed, 2 skipped, 9 setup errors** because sandbox
  restrictions prevented the browser fixture binding its local server.
  An approved rerun of those nine browser tests reached browser startup and
  **skipped all nine** because the Chromium executable is absent. No browser
  test pass is claimed for this review.
- Direct byte comparison against `c136e32`: **29 protected result/PDF files,
  zero differences**. The comparison was rerun successfully after increasing
  the inspection command's output buffer for the larger PDF files.
- The November 8 screenshots were visually inspected; they were not recaptured.
  The earlier layout measurements remain dated evidence, not newly executed
  measurements. No VoiceOver, native Safari, contrast certification, or new
  live-service verification was performed.

No application correction was necessary. Only this review record was appended;
the existing untracked design-audit folder is preserved. No commit, push,
merge, deployment, submission, or notification was performed. The next release
step is authorization to publish the branch and proceed through the release
review; the missing automated-browser execution remains an explicit limit.

### Original review prompt

```text
Review the completed Simulation Lab changes read-only in
/Users/hoanglh/RBF-Revenue-Based-Financing/worktrees/bilingual-daily-fx.
Start with HANDOFF-LAB-REDESIGN-2026-11-08.md and the appended 2026-11-08
section of evidence/redesign/verification.md. Inspect current git status and
diff since 9a782bb; use c136e32 only for original-baseline comparison and
protected-file preservation. If the work has since been committed, review
that commit as well as any remaining working-tree diff. Do not assume the
handoff's at-authoring uncommitted status remains current.

Review frontend/lab.html, both i18n catalogues, the changed localization tests
and tools/check_lab_reading_state.cjs. Verify FIX-A/RBF-ILL identity and the
reference-path principal/total/term explanation against backend/lab.py.
Check shared scale truthfulness, equal bar tracks, visible simulation and
scheduled-benchmark qualifications, payment aggregation/exclusions, recovery
denominator/checkpoint, completion censoring, missing data, latest-request
atomicity, EN/VI switching, native scenario selection and deep links.

Inspect the three delivered final screenshots. Distinguish actual-browser evidence
from minimal-DOM tests, the 200% root-size fixture from browser zoom, and
skipped tests from passing tests. Preserve all 13 scenarios, the all-four
detail, methods, assumptions and limitations. Confirm protected research
artifacts/PDFs are unchanged versus c136e32. Do not weaken tests to obtain a
pass, reopen settled design choices without concrete evidence, or redo the
implementation merely because this is a review handoff.

Return only actionable findings with severity, exact file/line, reproduction
or evidence, user/scientific impact and the smallest relevant correction;
otherwise report no findings and residual verification limits. No edits,
VoiceOver, actual submissions, notifications, commit, push, merge or deploy.
```
