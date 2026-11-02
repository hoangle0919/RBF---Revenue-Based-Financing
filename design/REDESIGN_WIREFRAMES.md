# RBF redesign — labelled layouts

Prepared 1 November 2026 against `codex/bilingual-daily-fx` @ `c98d02c`.
Scope: task hierarchy, prototype entry, Lab information architecture.
**Not** in scope: visual identity, research values, engines, publications.

Tokens used throughout are the existing ones — navy `#142c3a`, deep navy
`#10232f`, cream `#f7f6f2`, ochre `#d7b477`, Archivo + editorial serif, the `R`
mark. No new theme, no gradients, no animation library, no decorative
dashboards.

Legend: `[[ ]]` primary action · `[ ]` secondary action · `( )` control ·
`▸` collapsed disclosure · `▾` expanded · `···` content continues below the fold.

---

## 1. Homepage — current vs proposed

### 1.1 Current (desktop 1366×768, first viewport)

```
┌──────────────────────────────────────────────────────────────────┐
│ Independent research & software prototype   Not a lending service│  status-line
├──────────────────────────────────────────────────────────────────┤
│ R RBF    Approach  Simulation Lab  Research   EN/VI   Discuss ↗  │  header
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ── Revenue-based financing                                      │
│  A clearer view              ┌──────────────────────────────┐    │
│  of the contract.            │ THE CONTRACT IN MOTION 01/…  │    │
│                              │ One revenue path.            │    │
│  When revenue changes, the   │ Two payment structures.      │    │
│  contract matters…           │ (Steady)(Decline)(Interrupt) │    │
│                              │  [conceptual SVG chart]      │    │
│  RBF studies how financing…  │                              │    │
│                              │  fixed ── · share ──         │    │
│  [[Explore the Simulation    │  caption…                    │    │
│    Lab ↗]]  [Read research]  └──────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
  ···  scope band
  ···  01 / Approach            (3 rows of prose)
  ···  02 / Simulation Lab      (feature + 3 index links)
  ···  03 / Research library    ← English & Vietnamese papers live HERE
  ···  04 / Development status  ← the only IN-PAGE prototype link lives HERE
  ···  Scope & limitations
  ···  Contact
```

**Diagnosis, measured.** The prototype is reachable from three places, and
none of them is prominent:

| Where | Measured position |
|---|---|
| `.underlink` in band 04, "Open the interactive prototype" (`index.html:112`) | ~2.9k–3.3k px into a **4339px** page, i.e. roughly 3.7 viewports below the fold at 1366×768 |
| footer nav, "Prototype" (`index.html:132`) | below all of `<main>` |
| mobile menu, "Interactive prototype" (`index.html:33`) | in `<nav hidden>`; its only opener, `#menu-toggle`, is `display:none` above 820px, so on desktop it is in the DOM with **no reachable opener** |

So it is not literally the only link, but it is absent from the desktop nav
entirely and appears nowhere a first-time reviewer looks first. The paper links
measure at **2562px**. And the action row that exists today begins at **715px of
a 768px viewport**, so even it is clipped at the fold — see
[measured-baseline.md](../evidence/redesign/measured-baseline.md).

### 1.2 Proposed (desktop 1366×768, first viewport)

```
┌──────────────────────────────────────────────────────────────────┐
│ Independent research & software prototype   Not a lending service│  unchanged
├──────────────────────────────────────────────────────────────────┤
│ R RBF   Prototype  Papers  Simulation Lab    EN/VI   Discuss ↗   │  nav reordered
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ── Revenue-based financing        ┌───────────────────────────┐  │
│  A clearer view                    │ THE CONTRACT IN MOTION    │  │
│  of the contract.                  │ One revenue path.         │  │  figure STAYS
│                                    │ Two payment structures.   │  │  in the right
│  When revenue changes, the         │ (Steady)(Decline)(Interr) │  │  column — see
│  contract matters.                 │  [conceptual SVG chart]   │  │  §1.4
│                                    │  fixed ── · share ──      │  │
│  ┌──────────────────────────────┐  │  caption…                 │  │
│  │ [[ Try the prototype → ]]    │  └───────────────────────────┘  │  ← PRIMARY
│  │                              │                                 │
│  │ Read the paper:              │                                 │  ← one study,
│  │ [English ↗] [Tiếng Việt ↗]   │                                 │    two editions
│  │                              │                                 │
│  │ [ Simulation Lab ↗ ]         │                                 │
│  └──────────────────────────────┘                                 │
│                                                                   │
│  RBF studies how financing structures behave under volatile       │  ← context
│  sales, motivated by Vietnamese e-commerce. Research and          │    moves BELOW
│  software — not a credit recommendation.                          │    the actions
│                                                                   │
│  Synthetic examples only. Unvalidated score. Not a lender.       │  ← honesty,
└──────────────────────────────────────────────────────────────────┘    in-viewport
  ···  01 / Approach
  ···  02 / Simulation Lab
  ···  03 / Research library     (full paper + supplement + decision log + source)
  ···  04 / Development status   (prototype description + gated evaluator)
  ···  Scope & limitations
  ···  Contact
```

**What changed.** Four things, and nothing else:

1. The hero's action block carries the prototype as the primary action, with
   both paper editions beside it and the Lab secondary.
2. The action block moves **above** the long context paragraph, which follows it.
3. `.intro` changes from `align-items:center` to `align-items:start`, so the copy
   starts at the top of the band instead of being vertically centred against the
   taller figure cell.
4. `Prototype` and `Papers` enter the desktop nav.

The conceptual figure **stays in the right-hand column** — see §1.4. Every
existing band survives in the same order after the hero, and every existing
anchor still resolves.

Items 2 and 3 are the measured fix. At 1366×768 the action row currently begins
at **715px of a 768px viewport**, so it is clipped at the fold; the cause is
`align-items:center` centring the 638px-tall figure cell's shorter sibling. See
[measured-baseline.md](../evidence/redesign/measured-baseline.md).

### 1.4 The conceptual diagram — one decision

**It stays in the right-hand column of the hero on desktop, and renders below
the actions on mobile.** That is the whole decision; no DOM relocation.

Reasons, measured rather than reasoned from CSS:
- `.intro` is `grid-template-columns:1.1fr 1fr` with `.intro-copy` first and
  `.contract-figure` second (`institutional.css:32`), and at `max-width:820px`
  (`institutional.css:216`) the grid collapses to one column — so on mobile the
  figure already renders *after* the action block.
- On desktop it occupies the second column, so it costs the action block no
  vertical space once `align-items:start` stops it dictating the copy's offset.

It is **not** the reason the actions fall below the fold. The cause is the
vertical centring, which items 2 and 3 above remove. Moving the figure into its
own band would cost the visual identity the user likes while fixing nothing the
measurement attributes to it.

Subject to rendered EN/VI and mobile checks after implementation, as Codex asked.

### 1.3 Proposed (mobile 390×844, first viewport)

```
┌────────────────────────────────┐
│ Independent research…          │
├────────────────────────────────┤
│ R RBF        EN/VI      Menu + │
├────────────────────────────────┤
│ ── Revenue-based financing     │
│ A clearer view                 │
│ of the contract.               │
│                                │
│ When revenue changes, the      │
│ contract matters.              │
│                                │
│ ┌────────────────────────────┐ │
│ │ [[ Try the prototype → ]]  │ │  ← visible WITHOUT opening Menu
│ └────────────────────────────┘ │
│ [English ↗]  [Tiếng Việt ↗]    │
│                                │
│ Synthetic examples only…       │
└────────────────────────────────┘
  ···  Simulation Lab link
  ···  conceptual figure
  ···  (bands as desktop)
```

The mandate's requirement — *"on mobile, Try the prototype remains available
without opening the menu"* — is met by the hero action itself, not by adding a
sticky bar. No new fixed element, so no new overlap risk with the header.

---

## 2. Prototype page — current vs proposed

### 2.1 Current (desktop first viewport)

```
┌──────────────────────────────────────────────────────────────────┐
│ Research prototype · Not a lending service · synthetic only…     │  banner
├──────────────────────────────────────────────────────────────────┤
│ R RBF /Prototype  Overview  Lab  Prototype   EN/VI  Dashboard    │
│                                     [[Enter synthetic example]]  │
├──────────────────────────────────────────────────────────────────┤
│ INTERACTIVE PROTOTYPE / SYNTHETIC EXAMPLES ONLY                  │
│                                                                  │
│ Explore the mechanics.                                           │
│ Keep the limits in view.                                         │  ← large hero
│                                                                  │
│ Adjust an illustrative merchant profile to inspect the existing  │
│ scoring-and-financing pipeline. This prototype is separate from  │
│ the simulation study and the proposed retrospective evaluation…  │
│                                                                  │
│ [[Enter synthetic example]]   [Read the methodology →]           │
│ ──────────────────────────────────────────────────────────────── │  hero-rule
│ active scorer · integrity screen · financing engine · Vietnam    │  data-strip
└──────────────────────────────────────────────────────────────────┘
  ···  ┌ ILLUSTRATIVE DEMO · ADJUST THE PROFILE ─────────────┐
  ···  │ presets + six sliders        │  live result panel   │  ← THE WORKBENCH
  ···  └──────────────────────────────┴──────────────────────┘     is down here
```

**Diagnosis.** The workbench already exists and already works — presets, six
range inputs, a live result panel driven by `GET /api/assess/preview`. It is
simply below an essay. A reviewer who clicks through from the homepage reads a
second hero before touching anything. The nav's primary button points at
`go('apply')`, the *submission* flow, which can store a record and notify an
administrator — not the easiest preview.

### 2.2 Proposed (desktop 1366×768, first viewport)

```
┌──────────────────────────────────────────────────────────────────┐
│ Research prototype · Not a lending service · synthetic only…     │  unchanged
├──────────────────────────────────────────────────────────────────┤
│ R RBF /Prototype  Overview  Papers  Lab   EN/VI   [[Try it]]  ≡  │  CTA → #prototype
├──────────────────────────────────────────────────────────────────┤
│ Prototype — synthetic examples only                              │  compact title
│ Adjust a synthetic merchant profile and watch the illustrative    │  ONE sentence
│ terms change.                                                     │
│ ⚠ Unvalidated score. The scorer sets the tier, and the tier sets  │  limitation,
│   the terms. Not a credit recommendation.                         │  concise
│                                                                   │
│ ┌─ ADJUST THE PROFILE ──────────────┬─ ILLUSTRATIVE OUTPUT ─────┐ │
│ │ Thời Trang Linh Chi · Shopee      │ <verdict> (illustrative)  │ │
│ │ (High revenue, low returns)       │ unvalidated demo score    │ │  ← WORKBENCH
│ │ (Fast growth, young store)        │                           │ │    is the first
│ │ (Declining, high returns)         │ Illustrative advance      │ │    main content
│ │ (Small, new store)                │   <live> ₫                │ │
│ │                                   │   ≈ <live> USD · dated    │ │
│ │ Monthly revenue  ──●────  185M ₫  │ ─────────────────────────  │ │
│ │ Growth (MoM)     ────●──  +22%    │ Remittance        <live>  │ │
│ │ Return rate      ─●─────  2.8%    │ Repayment cap     <live>  │ │
│ │                                   │ Est. duration     <live>  │ │
│ │ ▸ More inputs (3)                 │ Cost (APR)        <live>  │ │
│ │   rating · late shipments · days  │                           │ │
│ │                                   │ [View full example →]     │ │
│ │ [chips: growth · returns · …]     │                           │ │
│ └───────────────────────────────────┴───────────────────────────┘ │
│ Synthetic data only. This preview stores nothing and notifies no  │
│ one. The separate submission flow below does both — it says so.    │
└──────────────────────────────────────────────────────────────────┘
  ···  Why this exists        (the essay, moved below)
  ···  How it works #how      (pipeline + flow diagram)
  ···  Enter synthetic example (optional, secondary submission flow)
  ···  Data handling #privacy
```

**What changed.** The hero essay, the `hero-rule` and the `data-strip` move
below the workbench. The title compacts to one line plus one sentence plus one
limitation. Three of six controls are foregrounded; the other three sit behind a
`▸ More inputs` disclosure that **keeps them in the DOM** so no hidden value is
ever reset. The nav's primary button retargets from `go('apply')` to the
workbench anchor `#prototype`. `Read the methodology` is renamed to match where
it actually goes — the prototype's own *How it works* section.

### 2.3 Proposed (mobile 390×844)

```
┌────────────────────────────────┐
│ Research prototype · not a …   │
├────────────────────────────────┤
│ R RBF /Prototype   EN/VI    ≡  │
├────────────────────────────────┤
│ Prototype — synthetic only     │
│ Adjust a synthetic profile and │
│ watch the terms change.        │
│ ⚠ Unvalidated score.           │
│                                │
│ ┌─ ADJUST THE PROFILE ───────┐ │
│ │ (High rev, low returns)    │ │  ← presets visible
│ │ (Fast growth, young)       │ │
│ │ (Declining, high returns)  │ │
│ │ (Small, new store)         │ │
│ │                            │ │
│ │ Monthly revenue            │ │  ← one meaningful
│ │ ──────●────────  185M ₫    │ │    input visible
│ └────────────────────────────┘ │
└────────────────────────────────┘
   ↓ within one viewport of scroll
┌────────────────────────────────┐
│ │ Growth (MoM)   ───●─  +22%   │
│ │ Return rate    ─●───  2.8%   │
│ │ ▸ More inputs (3)            │
│ ├─ ILLUSTRATIVE OUTPUT ──────┐ │
│ │ <verdict> (illustrative)   │ │  ← result reachable
│ │ Advance <live> ₫           │ │    in one scroll
│ │        ≈ <live> USD        │ │
│ └────────────────────────────┘ │
└────────────────────────────────┘
```

Stacked intentionally: controls, then output. Type size is **not** reduced to
hit the target; the budget comes from removing the essay, not from shrinking
text.

---

## 3. Simulation Lab — current vs proposed

### 3.1 Current

```
nav · banner (simulation-only) · hero (eyebrow, h1, lede, research question box)
summary bar + JUMP: Scenario|Contracts|Burden|Recovery|Settlement|
                    Under-reporting|Findings|Limitations          ← 8 technical labels
  s-scn       Scenario                    (selector, 13 scenarios in 4 families)
  s-arms      Contracts compared          (4 arm cards)
  s-burden    Seller payment burden       (chart + caveat)
  s-hpb       Months above a threshold    ▸ details
  s-recovery  Provider recovery           (chart + caveat)
  s-dur       Repayment duration…         (table + caveat)
  s-under     Under-reporting sensitivity ▸ details
  s-find      What this shows…            (classified findings)
  s-limits    Assumptions / Limitations
  s-prov      Provenance                  (artifacts + checksums)
```

**Diagnosis.** Ten stacked analytical sections read top-to-bottom, with a jump
bar whose labels assume the vocabulary the page is trying to teach. The scenario
selector is section one, but nothing tells a visitor what question the page
answers until they have read the hero's research-question box.

### 3.2 Proposed (desktop)

```
┌──────────────────────────────────────────────────────────────────────┐
│ R RBF    Overview  Prototype  Papers              EN/VI              │
├──────────────────────────────────────────────────────────────────────┤
│ ▲ All figures are simulation output. No observed seller revenue,     │  banner kept
│   repayment or default outcome exists in this project.               │  verbatim
├──────────────────────────────────────────────────────────────────────┤
│ Simulation Lab                                                        │
│ Compare repayment when sales change.                                  │
│ Choose a simulated sales scenario and compare how four contracts      │
│ respond. Simulation only — no observed seller outcomes.                │
│                                                                       │
│ SCENARIO   four starter choices, of 13 available                      │
│  (Stable sales)(Sustained decline)(Temporary interruption)             │
│  (Permanent closure)                        ▾ All 13 scenarios        │
│  Stable sales: flat seasonality and no trend or shock, with ordinary   │
│  month-to-month variation around that level. A specified input, not a  │
│  measured Vietnamese outcome.                                         │
│                                                                       │
│ SHOW ME          ← ONE selector. Nothing else selects a question.     │
│  ((Payments))  ( Target recovery )  ( Completion )                    │
│                                                                       │
│ ┌─ Payments ─────────────────────────────────────────────────────┐   │
│ │ What share of sales goes to payments?                           │   │
│ │ Payment ÷ GMV in a month. Summary statistics over 24 months —    │   │
│ │ there is no monthly series behind these figures.                 │   │
│ │                                                                 │   │
│ │                              mean    90th pct   peak month      │   │
│ │ Fixed payment · cost-matched  9.6%     11.8%      12.03%        │   │
│ │   (FIX-A)                                                       │   │
│ │ Amortizing loan · 18% nom.    9.5%     11.6%      11.87%        │   │
│ │   no cap  (FIX-B)                                               │   │
│ │ Revenue-based · cap 1.0945×   9.7%      9.7%       9.70%        │   │
│ │   (RBF-EQ)                                                      │   │
│ │ Revenue-based · cap 1.20×     9.7%      9.7%       9.70%        │   │
│ │   (RBF-ILL)                                                     │   │
│ │                                                                 │   │
│ │ [grouped horizontal bars — the existing groupedBars renderer]    │   │
│ │                                                                 │   │
│ │ ⚠ Burden is measured on REVENUE, not on what the seller keeps.   │   │
│ │   Margins, operating costs, reserves and other debts are not     │   │
│ │   modelled, so a lower burden does not establish affordability.  │   │
│ │   The denominator is GMV while remittance is charged on net      │   │
│ │   sales, so this equals r·(1 − return rate), not r. Undefined in │   │
│ │   months with zero revenue.                                      │   │
│ └─────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│ ▸ What each of the four contracts is            → opens #s-arms       │
│ ▸ Months above a burden threshold               → opens #s-hpb        │
│ ▸ Repayment duration and settlement             → opens #s-dur        │
│ ▸ Under-reporting sensitivity                   → opens #s-under      │
│ ▸ Findings, by claim type                       → opens #s-find       │
│ ▸ Assumptions & limitations                     → opens #s-limits     │
│ ▸ Provenance — artifacts, checksums, reproduction → opens #s-prov     │
└───────────────────────────────────────────────────────────────────────┘
```

Selecting **Target recovery** replaces the card body with:

```
│ ┌─ Target recovery ──────────────────────────────────────────────┐   │
│ │ How much of each repayment target is recovered?                 │   │
│ │ Recorded checkpoints at months 12, 18 and 24 — not a monthly    │   │
│ │ series. Each arm is shown against its OWN target.               │   │
│ │                                 month 12  month 18  month 24    │   │
│ │ Fixed payment · cost-matched      92.3%    100.0%    100.0%     │   │
│ │   (FIX-A)      target: contractual cap                          │   │
│ │ Amortizing loan · 18% nom. (FIX-B) …                            │   │
│ │   target: scheduled total repayment (this loan has no cap)      │   │
│ │ Revenue-based · cap 1.0945× (RBF-EQ) …                          │   │
│ │ Revenue-based · cap 1.20×   (RBF-ILL) …                         │   │
│ │ ⚠ Denominators DIFFER by contract, so read each arm against its │   │
│ │   own target. A higher share does not necessarily mean more VND  │   │
│ │   recovered, more profit, or less principal at risk.             │   │
│ └─────────────────────────────────────────────────────────────────┘   │
```

Selecting **Completion**:

```
│ ┌─ Completion ───────────────────────────────────────────────────┐   │
│ │ How many paths complete repayment within 24 months?             │   │
│ │ Share of the 500 simulated revenue paths for this scenario,     │   │
│ │ over a fixed 24-month observation window.                       │   │
│ │ Fixed payment · cost-matched (FIX-A)             100.0%         │   │
│ │ Amortizing loan · 18% nominal (FIX-B)            100.0%         │   │
│ │ Revenue-based · cap 1.0945× (RBF-EQ)             100.0%         │   │
│ │ Revenue-based · cap 1.20×   (RBF-ILL)            100.0%         │   │
│ │ ⚠ This is COMPLETION, not default. No borrower behaviour and no │   │
│ │   default is simulated on any arm; a path that does not complete │   │
│ │   is censored by the 24-month window. The fixed arms are         │   │
│ │   modelled as paid in full and on time, so these are simulated   │   │
│ │   obligations, not observed collections.                         │   │
│ └─────────────────────────────────────────────────────────────────┘   │
```

**What changed.** Ten stacked analytical sections become: a purpose statement
with the simulation qualifier; a starter scenario set with access to all 13; one
`SHOW ME` selector; one result card that answers the selected question for all
four contracts with its own caveat attached; and seven optional panels that keep
the existing section ids.

### 3.3 Proposed (mobile 390×844)

```
┌────────────────────────────────┐
│ R RBF           EN/VI      ≡   │
├────────────────────────────────┤
│ ▲ All figures are simulation…  │
├────────────────────────────────┤
│ Compare repayment when         │
│ sales change.                  │
│ Choose a scenario and compare  │
│ how four contracts respond.    │
│                                │
│ SCENARIO  4 of 13              │
│ (Stable)(Sustained decline)    │
│ (Temporary)(Permanent closure) │
│ ▾ All 13 scenarios             │
│                                │
│ SHOW ME                        │
│ ((Payments))( Target recovery )│  ← the SAME selector, wrapped
│ ( Completion )                 │
└────────────────────────────────┘
   ↓ promptly
┌────────────────────────────────┐
│ ┌─ Payments ─────────────────┐ │
│ │ What share of sales goes   │ │
│ │ to payments?               │ │
│ │ Summary statistics over 24 │ │
│ │ months; no monthly series. │ │
│ │ Fixed · cost-matched       │ │
│ │   (FIX-A)   peak 12.03%    │ │
│ │ Amortizing · 18% (FIX-B)   │ │
│ │             peak 11.87%    │ │
│ │ Revenue 1.0945× (RBF-EQ)   │ │
│ │             peak  9.70%    │ │
│ │ Revenue 1.20×  (RBF-ILL)   │ │
│ │             peak  9.70%    │ │
│ │ ⚠ Measured on revenue, not │ │
│ │   on what the seller keeps.│ │
│ └────────────────────────────┘ │
└────────────────────────────────┘
```

**One selector, not three controls.** The desktop `SHOW ME` group and the mobile
group are the same element and the same state — it wraps on narrow widths rather
than becoming a separate tab strip. There is no second chart selector: the card
body and its chart both follow the one selection. Labels are **Payments**,
**Target recovery** and **Completion**; no unexplained Q numbers anywhere.

### 3.4 No invented chart

The current API exposes, per arm:
- burden as **`mean`, `p90`, `p95`, `max`** — summary statistics, **no monthly
  series**. `p95` is emitted today and never rendered; the redesign can show it
  or leave it, but it must not be presented as a time series.
- recovery as **recorded checkpoints at months 12, 18 and 24** — labelled as
  checkpoints, never implied to be a complete monthly curve.
- completion as a single **share of 500 paths** over the fixed 24-month window.

An earlier draft of this wireframe showed a "Burden over time" control. That was
inventing a series the data does not contain, and it is removed. The existing
`groupedBars()` renderer (`lab.html:844-905`, horizontal grouped bars with a
narrow-width branch below 560px) is the right primitive and is reused unchanged.
No calculation, artifact or registered value changes.

### 3.5 Deep-link targets

Every current anchor keeps resolving, and each one opens exactly one panel:

| Anchor | Opens | Linked from |
|---|---|---|
| `#s-scn` | scrolls to the scenario selector (stays top-level, not a panel) | `lab.html` jump nav |
| `#s-arms` | **What each of the four contracts is** | `index.html:87`, jump nav |
| `#s-burden` | selects **Payments** and scrolls to the result card | `index.html:88`, jump nav |
| `#s-recovery` | selects **Target recovery** and scrolls to the result card | `index.html:89`, jump nav |
| `#s-dur` | **Repayment duration and settlement** | jump nav |
| `#s-hpb` | **Months above a burden threshold** | not linked today |
| `#s-under` | **Under-reporting sensitivity** | jump nav |
| `#s-find` | **Findings, by claim type** | jump nav |
| `#s-limits` | **Assumptions & limitations** | jump nav, and `test_lab.py:509` slices the HTML on `id="s-limits"` |
| `#s-prov` | **Provenance** | not linked today |

`#s-burden` and `#s-recovery` drive the selector rather than a panel, because
that is where their content now lives. `backend/tests/test_institutional_redesign.py:128-135`
asserts every `/lab#…` href on the homepage resolves to a real id in `lab.html`,
so none of these can be renamed without updating `index.html:87-89`.

## 4. Flow comparison

| | Current | Proposed |
|---|---|---|
| **Prototype** | homepage → scroll ~3.7 viewports to band 04 `underlink` (or the footer, or the mobile menu) → second hero → `[[Enter synthetic example]]`, which is the *submission* flow | homepage hero `[[Try the prototype]]` → `/demo.html#prototype` → workbench, showing its loading state until a successful preview response arrives |
| **Papers** | homepage → scroll to band 03 | homepage hero, beside the prototype action |
| **Lab** | homepage hero primary action → 10 stacked sections read top-down | homepage secondary action → purpose line → scenario → 3 questions → optional panels |

The prototype CTA goes to the **preview workbench**, never to `go('apply')`.
The submission flow stays available and secondary, with its storage and
notification disclosure intact ahead of it.

---

## 5. What is deliberately NOT changed

- Navy / cream / ochre palette, rules, Archivo + serif, the `R` mark.
- The four presets, the six controls, `GET /api/assess/preview`, the full-result
  behaviour, the stale-response and error safeguards.
- All four Lab arms, all 13 scenarios, every metric, every registered value.
- Research artifacts, engines, canonical results, schemas, publication PDFs.
- EN/VI support, the dated approximate USD display, VND as the input and
  calculation currency.
- Every existing URL and hash route, loading / error / unavailable states,
  reduced-motion handling, visible keyboard focus.

---

## 6. Numbers shown in these layouts

The Lab question-card figures above are **real values read from the registered
artifacts** for the `stable` scenario — peak payment burden FIX-A 12.03%,
FIX-B 11.87%, RBF-EQ 9.70%, RBF-ILL 9.70%; month-24 target recovery and
completion share 100.0% for all four arms. They are shown so the layout can be
checked against what the page will actually render.

The prototype panel's figures are written `<live>` rather than filled in: they
come from `GET /api/assess/preview` at render time and depend on which scorer
path is active. A wireframe showing a specific advance would be a placeholder
presented as a fetched result, which this mandate forbids.
