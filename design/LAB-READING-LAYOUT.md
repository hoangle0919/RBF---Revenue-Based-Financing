# Simulation Lab — primary reading experience

Against `c136e32`. Addresses `DESIGN-IS-2026-11-04/03-verdict.md`.
Priority: useful → understandable → minimal. Honesty is a hard constraint.

## Desktop (1366×768) — one horizontal workspace

```
┌────────────────────────────────────────────────────────────────────────┐
│ R RBF   Overview  Prototype  Papers                     EN / Tiếng Việt│
├────────────────────────────────────────────────────────────────────────┤
│ ▲ Every figure is simulation output. No observed seller outcome exists.│
├────────────────────────────────────────────────────────────────────────┤
│ Compare repayment when sales change                                     │
│ Pick a sales scenario. See what a fixed payment and a revenue share do. │  ← 2 lines
├──────────────────┬─────────────────────────────────────────────────────┤
│ SALES SCENARIO   │  SHOW ME                                            │
│ ((Steady))       │  ((Payment share)) ( Target recovery ) ( Completion)│
│ ( Falling )      │                                                     │
│ ( Interrupted )  │  Share of a month's sales taken as payment          │  ← ONE line
│ ( Closure )      │  average of each path's worst month · payment ÷ GMV │  ← basis
│ ▾ All 13         │                                                     │
│                  │  Fixed payment · cost-matched          FIX-A        │
│ Falling sales:   │  ████████████████████░░░░░░░░░░  18.77%             │  ← aligned
│ an immediate,    │                                                     │    marks
│ permanent drop   │  Revenue share · cap 1.20×            RBF-ILL       │
│ to 60% of prior  │  ██████████░░░░░░░░░░░░░░░░░░░░   9.70%             │
│ revenue.         │                                                     │
│                  │  ┌─ In this scenario ──────────────────────────┐    │
│                  │  │ The revenue share takes a smaller share of  │    │  ← takeaway,
│                  │  │ sales here, 9.70% against 18.77%. A lower   │    │    scenario-
│                  │  │ share is not proof of affordability.        │    │    dependent
│                  │  └─────────────────────────────────────────────┘    │
│                  │                                                     │
│                  │  Showing 2 of 4 contracts — the cost-matched fixed  │  ← explicit
│                  │  payment and the illustrative revenue share.        │    selection
│                  │  ▸ All four contracts, detailed statistics & methods│  ← ONE
└──────────────────┴─────────────────────────────────────────────────────┘    secondary
   ▸ Contracts compared   ▸ Burden  ▸ Recovery  ▸ Settlement  ▸ …            area
```

## Phone (390×844) — both contracts visible together

```
┌────────────────────────────────┐
│ R RBF            EN / Tiếng Việt│
├────────────────────────────────┤
│ ▲ Every figure is simulation…  │
├────────────────────────────────┤
│ Compare repayment when         │
│ sales change                   │
│ Pick a sales scenario. See     │
│ what a fixed payment and a     │
│ revenue share do.              │
│                                │
│ SALES SCENARIO                 │
│ ((Steady))( Falling )          │
│ ( Interrupted )( Closure )     │
│ ▾ All 13                       │
│                                │
│ SHOW ME                        │
│ ((Payment share))( Recovery )  │
│ ( Completion )                 │
└────────────────────────────────┘
   ↓ the comparison starts here
┌────────────────────────────────┐
│ Share of a month's sales taken │
│ as payment                     │
│ avg of each path's worst month │
│ · payment ÷ GMV                │
│                                │
│ Fixed payment · cost-matched   │
│ FIX-A                          │
│ ███████████████░░░░░  18.77%   │  ← BOTH contracts
│                                │    in one block,
│ Revenue share · cap 1.20×      │    no separate
│ RBF-ILL                        │    tall cards
│ ████████░░░░░░░░░░░░   9.70%   │
│                                │
│ ┌ In this scenario ──────────┐ │
│ │ The revenue share takes a  │ │
│ │ smaller share here, 9.70%  │ │
│ │ against 18.77%. A lower    │ │
│ │ share is not proof of      │ │
│ │ affordability.             │ │
│ └────────────────────────────┘ │
│                                │
│ Showing 2 of 4 contracts …     │
│ ▸ All four contracts, detailed │
│   statistics and methods       │
└────────────────────────────────┘
```

## What changes

| | before | after |
|---|---|---|
| first thing read | 102-word methodology paragraph | the question, then two values |
| primary comparison | 4 stacked cards × 3 statistics = 12 numbers | 2 rows × 1 headline value |
| Payments default | mean + p90 + peak at once | **one** named aggregate; the rest in detail |
| which pair, and why | not stated | stated in words, above the detail link |
| takeaway | after the table | beside the result, scenario-dependent |
| methodology | before the answer | inside the one secondary area |
| detail | spread over panels | one "All four contracts, detailed statistics and methods" |

## Honesty rules carried into the markup

- The mark is a **length-encoded value with the number printed beside it**, on a
  stated common scale. Not a time series, not a trend, not decoration.
- FIX-A is labelled a **scheduled-payment benchmark**, never observed collection.
- Payment share states **payment ÷ GMV** and **average of path peaks**, never
  "worst month" unqualified.
- Recovery states its **checkpoint month** and **own-target denominator**.
- Completion states the **24-month horizon** and **simulated-path denominator**.
- The takeaway is generated per scenario from API values and never asserts a
  universal winner; recovery explicitly says the ordering depends on scenario.
- "Showing 2 of 4" is always visible, so the pair is never read as the whole set.

## Completion pass — 2026-11-06 (before application edits)

1. Restore the intended compact hero with Lab-local selectors that win over
   `institutional.css`; replace the phone starter grid with a labelled native
   selector containing all 13 API scenarios. Reuse `renderScenarios`,
   `apiText`, `markSelected`, and the atomic `select` request guard. Keep desktop
   starters, keyboard operation, language repaint, deep links and error recovery.
2. Keep the simulation/no-observed-outcomes/non-lending warning visible in a
   concise bilingual banner, retaining its full explanation in About this study.
   Shorten only repeated introduction, never metric or contract qualifications.
3. Keep both marks adjacent and readable, add explicit common-scale endpoints
   and active-month exclusions beside payment figures. Derive every value from
   the existing `QUESTIONS` fields, never create a series or alter API/engine data.
4. Clarify pair selection from `backend/lab.py:ARMS`: FIX-A and RBF-ILL share
   principal, total repayment and reference-path term; RBF-EQ is the separate
   reference-rate grid-priced contract. Do not imply equality of realised rates.
5. Check localization parity/static guards and all Lab tests; parent verifies
   actual EN/VI browser geometry at 1366×768, 390×844 and 360×800, all scenarios
   and questions, language switches, enlarged text, error and race handling.
   Both marks must fit together without shrinking essential type or clipping.
   Research results, engine, API and papers remain untouched. No deployment.
