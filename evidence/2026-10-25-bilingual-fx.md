# Bilingual site + USD reference equivalents — verification record

Branch `codex/bilingual-daily-fx`, based on `origin/main` `b3683e5`.
Implementation only. Not pushed, not merged, not deployed.

## What was verified, and how

| Check | Result |
|---|---|
| Backend suite (`--ignore=test_lab_browser.py`) | **599 passed, 2 skipped** |
| Simulation suite (`research/rbf_sim/tests`) | **651 passed** |
| Node prototype-state tests (`tools/check_prototype_state.cjs`) | **7 passed** |
| Catalogue parity (`tools/check_i18n.py`) | **en=583 vi=583**, every referenced key resolves |
| 20 registered research artifacts vs `origin/main` | **unchanged** (SHA-256) |
| 3 publication PDFs vs `origin/main` | **unchanged** (SHA-256) |

Baseline before this work was 556 passed / 1 skipped. The increase is 42 new FX
tests plus one new i18n-isolation guard.

## Not executed

- The nine Playwright Lab browser tests. Not run.
- VoiceOver and any screen-reader behaviour. Not run, by instruction.
- No live merchant submission, no dashboard login against production, no
  payment, no notification.
- Browser checks were performed against a local preview at 360px and desktop
  width only. 390/768/1440 were not separately exercised.

## FX adapter

Provider reconfirmed before implementation: no API key, free for commercial use
of blended rates, daily updates, caching encouraged, **no SLA stated**. One
successful fetch demonstrates connectivity and nothing more; the observed rate
is not hardcoded anywhere.

A failing fetch was diagnosed rather than guessed at: the cause was the **CA
bundle, not the User-Agent** — three different agents failed identically with
`CERTIFICATE_VERIFY_FAILED`, and an explicit `certifi` context fixed it. The
same root cause had previously broken the operator-alert path. `certifi` was
already pinned, so no dependency changed.

42 tests, all mocked, covering orientation, cents rounding, wrong pair, inverted
orientation, malformed and future dates, the three freshness bands and their
boundaries, timeouts, 429/5xx, oversized responses, cache expiry, failed refresh
preserving `fetched_at`, concurrency dedupe and recovery. One live smoke test is
gated behind `RBF_FX_LIVE=1` and is never used as a correctness oracle.

A guard asserts no calculation module imports `fx`, checked by source inspection
rather than `sys.modules`, because an import inside a function would not appear
in a fresh-import check.

## Defects found and fixed during the work

1. **85 catalogue keys were referenced but undefined**, via lookup tables and
   arrays (`VERDICT`, `CHIP_DEFS`, `TIER_LABEL`, `DECISION_STEPS`). `t()` returns
   `''` for an unknown key, so verdict labels, tier names, severity levels and
   chip states rendered **blank in every language, English included**. The parity
   checker reported OK because its regex only saw direct `t('key')` call sites.
   The checker now treats any namespaced string literal as a reference.
2. **An A-9 qualifier was lost.** `origin/main` read "…observed window, not a
   lifetime return)". After the string moved into the catalogue it read only
   "Observed return to closure", which is the exact misreading A-9 forbids.
   Restored in both languages.
3. **Approved hero copy was replaced with paraphrases** while inferring English
   for keys whose source text existed on `origin/main` ("Preview unavailable"
   became "Unavailable", and six similar). All restored verbatim.

## Guards updated rather than relaxed

Six guards asserted English literals that now live in the catalogue. Each was
rebound to assert the copy where it actually is, **and to require a non-empty
Vietnamese value** — a disclaimer that exists only in English is not a
disclaimer for a Vietnamese reader. That is stricter than the assertion it
replaced. No guard was deleted or weakened.

## Known gap

`backend/lab.py` generates user-visible English prose (scenario labels, arm
names, findings, metric definitions). **102 of 436 visible text nodes on the Lab
page remain English in Vietnamese mode** as a result. Keying it means changing
the shape of an API response that renders registered research output, which is a
broader change than this task authorises. Reported, not attempted.

---

# Appendix — 31 October 2026 review corrections

The record above is retained as written. It described the branch at `ae8d778`
and is now inaccurate in three particulars, corrected here rather than edited
in place: the branch **has** been pushed (backup only, authorised; no merge or
deploy), the backend suite is no longer 599 tests, and the FX suite is no
longer 42.

## Findings reproduced before any edit

All eight findings in the 31 Oct review were reproduced first, using the
review's own two scripts plus direct inspection for F1 and F7. Reproducing a
defect is not the same as satisfying an acceptance gate, and is not claimed as
such.

## Corrected

| Finding | State |
|---|---|
| F1 — USD not connected to any page | **Fixed.** Adapter loaded on all three pages; amounts bind their authoritative integer in `data-vnd`; display control and dated attribution added |
| F2 — no refresh or ageing on a long-lived page | **Fixed in logic, partially verified.** Client recomputes age from the reference date against the current UTC day; hourly refresh, visibility/focus revalidation, single in-flight refresh, stale-response guard |
| F3 — refresh completion not atomic | **Fixed.** Release and publish are one lock transition |
| F4 — ValueError text escaped the taxonomy | **Fixed.** Fixed allowlist; anything else becomes `fx_unreachable` |
| F5 — browser used binary float, not decimal | **Fixed.** BigInt integer arithmetic; five fixtures pinned on both sides |
| F6 — language race and lost URL preference | **Fixed.** Desired-language token; explicit language carried into same-origin links; `lang=en` retained |
| F7 — Vietnamese Lab coverage and dynamic state | **OPEN.** Not attempted |
| F8 — evidence inaccurate | This appendix |

## Verification actually executed

| | |
|---|---|
| Backend (`--ignore=test_lab_browser.py`) | **618 passed, 2 skipped** |
| Simulation | **651 passed** |
| Node prototype-state | **7 passed** |
| Node i18n/FX state (new) | **11 passed** |
| Catalogue parity | **583 / 583**, every reference resolves |
| Protected files vs `b3683e5` | **30 checked, 0 changed** |

The skipped backend tests are the missing-ensemble artifact and the live FX
smoke test (run separately and passing). One Node test was removed rather than
left hanging: the harness holds a single unresolved catalogue request, so a
second delayed fetch overwrote its release closure. The single-pending case
covers the same defect; a multi-pending version needs a per-request resolver.

## Browser checks executed

Against a local preview on this machine, with the live `/api/fx` quote
(reference date 2026-10-30).

- **demo, Vietnamese, 360 / 390 / 768 / 1440px** — no horizontal overflow at
  any width; 3 bound amounts each carrying a USD line; language switch usable.
- **lab, Vietnamese, 390 / 1440px** — no horizontal overflow; 8 bound amounts;
  Vietnamese attribution line.
- Browser and backend agree exactly: 185,000,000 → 7180.28, 333,000,000 →
  12924.51, 382,950,000 → 14863.19, 222,000,000 → 8616.34.
- VND-only removes the USD lines and the note while VND stays primary.
- Vietnamese renders its own number format (`7.180,28`).

**A regression was found and fixed during these checks.** At 390px the
Vietnamese prototype header overflowed its viewport by 13px, caused by the
language switch this work added to a header that has no mobile menu to fall
back to. Hiding the control would have stranded a Vietnamese reader on a phone,
so it now wraps and shrinks instead.

A stale browser stylesheet cache initially made the fix appear ineffective.
The rule was confirmed absent from the loaded sheet before any further change
was made, rather than the CSS being rewritten against a false negative.

## Not executed — no claim made

- The nine Playwright Lab browser tests. Still not run.
- VoiceOver and all screen-reader behaviour. Not run, by instruction.
- English-language viewport matrix; Vietnamese was checked as the harder case.
- `index.html` at the full viewport matrix.
- No production request, submission, login, payment, deployment or merge.

## Remaining gap

**F7 is open and Vietnamese coverage is not complete.** `backend/lab.py` emits
user-visible English prose through four read-only endpoints — 86 prose-bearing
fields — leaving roughly 102 of 436 visible Lab text nodes English in
Vietnamese mode. The additive `*_key` approach is specified and authorised but
not implemented.
