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
