# Measured baseline — before the redesign

Measured in the browser against a local server, **not estimated from CSS**.
An earlier draft of the plan estimated the homepage intro band at ~480px and
concluded the action row was already in the first viewport. That estimate was
wrong, and the correction is recorded here.

## Homepage, 1366×768, English

| Element | top (px) | bottom (px) | in first viewport |
|---|---|---|---|
| status line | 0 | 38 | yes |
| site header | 38 | 127 | yes |
| `.intro` band | 127 | 931 | overruns the fold by 163px |
| `#intro-title` (h1) | 330 | 497 | yes |
| `.intro-lead` | 527 | 587 | yes |
| `.intro-context` | 605 | 681 | yes |
| **`.intro-actions`** | **715** | **768** | **starts 715px down — clipped at the fold** |
| `.contract-figure` | 209 | 847 | overruns the fold |
| `.scope-band` | 931 | 1034 | no |
| research band (papers) | 2170 | 2817 | no |
| `.paper-links` | 2562 | 2650 | no |
| development status band | 2817 | 3341 | no |

Page height 4339px.

## Why the copy starts 330px down

`institutional.css:32` sets `.intro{display:grid;grid-template-columns:1.1fr 1fr;
align-items:center}`. The figure cell is 638px tall; `align-items:center`
vertically centres the **shorter** copy cell against it, pushing the h1 down to
330px and the action row to 715px.

This is exactly the mechanism Codex warned about — a grid's second column
affecting row height — and it is why a CSS reading alone got it wrong.

So the homepage needs **both** priority and compaction, not priority alone:
- `align-items:start` so the copy begins at the band's top rather than centred
  against the figure, and
- the action block placed directly after the lead, with the longer context
  paragraph below it.

Together these are projected to lift the action row from 715px to roughly
470px. The projection is stated as a projection; it is re-measured after
implementation and the measured number is what gets reported.
