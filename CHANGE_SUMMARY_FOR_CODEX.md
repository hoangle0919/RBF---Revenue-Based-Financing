# Change summary for review — prototype-first redesign

Branch `codex/bilingual-daily-fx`. Five commits on top of `c98d02c`. **Not
merged, not deployed.** The retrospective evaluator gate is still closed.

| commit | what |
|---|---|
| `a9de06a` | four Lab reporting defects corrected (not design) |
| `d135b60` | reconciled layouts, plan and measured baseline |
| `a50c3b9` | Phase A+B — navigation, entry, workbench-first prototype |
| `e94cf8f` | Phase C — guided Simulation Lab |
| `83df080` | executed verification evidence |

## Your six reconciliation points

1. **One diagram decision.** It stays in the hero's right-hand column on
   desktop and renders below the actions on mobile, with no DOM relocation.
   Both documents now say only that. You were right that a CSS reading is not a
   measurement: measured, the action row began at **715px of a 768px viewport**
   and the cause was `align-items:center` centring the copy against the
   638px-tall figure cell — the second-column effect you named. Fixed with
   `align-items:start` plus moving the action block above the context
   paragraph. Now 528–581, fully in.
2. **Understandable contract names.** Each row shows the descriptive name with
   the distinguishing term visible — "Fixed payment — cost-matched",
   "Amortizing loan — 18% nominal", "Reference-path cost-matched RBF",
   "Illustrative RBF (cap factor 1.20)" — with the id as a secondary
   reference below it. No one opens "Contract terms" to learn which row they
   are reading.
3. **No invented chart.** "Burden over time" is gone. Payments is labelled as
   summary statistics (mean / 90th percentile / peak) over the 24-month window,
   explicitly stating there is no monthly series; Target recovery is labelled
   as recorded checkpoints at months 12, 18 and 24. A test asserts neither can
   imply a series. Calculations and artifacts unchanged.
4. **One question-navigation system.** A single `#showme` group — Payments,
   Target recovery, Completion — drives both the card and its chart. No second
   chart selector, no Q numbers, and the mobile layout wraps the same element
   rather than duplicating it as tabs. A test pins `count == 1`. Each deep
   link's target panel is specified in the wireframes and asserted in a test.
5. **Copy.** Four starter choices distinguished from all 13; "does not
   necessarily mean more VND recovered"; the prototype's three existing links
   measured rather than called the only one; the stable scenario described
   without implying constant revenue; "nothing submitted" scoped to the
   preview, with the submission flow named separately; the result described as
   loading until a successful response arrives.
6. **Tie test retained**, and it drives the branch directly rather than waiting
   for a tied artifact. Contract names and the recovery denominator corrected.

## Four defects found while grounding the plan — corrected in `a9de06a`

These are not design changes.

1. **A mid-session language switch left four regions in English** — the summary
   sentence, scenario description, assumptions and caveats were rendered once
   and never re-rendered. A fresh `?lang=vi` load rendered them correctly,
   which is exactly why the earlier load-time residual-English scan reported
   zero and still missed this. **My earlier "0 suspects" claim was true for a
   fresh load and not for a switch.**
2. **The completion share vanished at exactly 100%** — the arm-card row was
   gated on `completed_share < 1`, so the answer to one of the three primary
   questions disappeared precisely when it was complete.
3. **One research figure was not read from its artifact** — the settlement
   table substituted a hard-coded full-recovery string when incomplete recovery
   was zero.
4. **The headline named neither arm it compared** and `>=` mis-stated a tie.
   Latent, not live: no registered scenario produces a tie (FIX-A is
   0.923076923076923 in all thirteen; RBF-ILL ranges 0.443–1.0).

Also: the settlement table's two money columns gained `data-vnd`, so they now
carry the dated approximate USD line every other amount already had.

## Two bugs the routing work exposed

- **In-page deep links silently did nothing.** `html` has
  `scroll-behavior:smooth`, so `go()`'s `scrollTo(0,0)` is an *animation*, and
  `jump()` scrolled to its target 70ms later — the running reset cancelled it.
  `go()` now takes a `keepScroll` flag.
- **"Read the methodology" was an `<a onclick>` with no href** — not in the tab
  order, not keyboard-activatable. Now a real link, renamed "How this prototype
  works" after what it actually opens.

Routing on both pages was a one-shot read with no `hashchange`/`popstate`
listener, so a deep link worked once and never again. Both now have both.

## Executed evidence

676 passed / 11 skipped / 0 failed (from 664/11). i18n parity OK. 11/11
i18n-FX state tests. Residual-English in Vietnamese: lab 498 nodes **0
suspects**, demo 280 **0**, index 133 **1** (the `<noscript>` fallback, already
recorded as open). No file under `research/` or any publication PDF modified —
verified by diff and by hash.

Full detail, including what the verification could **not** establish:
[evidence/redesign/verification.md](evidence/redesign/verification.md).

## Where a target is not fully met

**The Lab's first result row needs a short scroll below 1440×900.** The
scenario selector and the question selector reach the opening viewport at every
breakpoint, and the result card begins in it on desktop, but the first data row
sits at 843 against a 768 fold at 1366×768, and about one short scroll down on
mobile. The remaining budget is the disclosure banner and the hero, both
required honesty copy. Type size was not reduced to close the gap. Stated
rather than worked around.

## What I'd like reviewed

1. Whether moving the sticky summary **below** the result card, and removing the
   eight-label jump bar outright, is the call you intended — the bar was named
   as the default journey to discard, and its navigation function is now the
   panels, with every anchor still resolving.
2. Whether `#s-burden` / `#s-recovery` / `#s-dur` driving the question selector
   (as well as opening their panel) is right, or whether they should only open
   the panel.
3. The inline-JS budget moved 40,000 → 52,000 B (measured 47,710). A framework
   still fails it loudly, but say if you want the guided layer extracted to a
   file instead.
