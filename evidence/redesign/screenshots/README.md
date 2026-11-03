# Screenshot set

Captured from a local server against the branch head listed in
`../verification.md`. These are the committed images the earlier evidence
record referred to but did not contain.

| file | page | viewport | language |
|---|---|---|---|
| `home-1366x768-en.jpg` | homepage | 1366×768 | English |
| `home-390x844-vi.jpg` | homepage | 390×844 | Vietnamese |
| `prototype-1366x768-vi.jpg` | prototype, top of page | 1366×768 | Vietnamese |
| `lab-1366x768-en.jpg` | Simulation Lab, top of page | 1366×768 | English |
| `lab-390x844-vi-guided-card-after-R1.jpg` | Lab guided card | 390×844 | Vietnamese |
| `lab-390x844-vi-guided-card-before-stacking-fix.jpg` | same, **before** the long-label fix | 390×844 | Vietnamese |

The last pair is the R1 before/after. In the "before" image the statistic
label and its value shared one flex line, so the longer R5 labels pushed the
value outside the card (measured: value right edge 435px against a 359px card
edge). In the "after" image the label sits above the value, and every value is
inside the card at every label length.

The images are JPEG captures scaled for size; the numeric claims in
`../verification.md` come from measured geometry, not from reading these.

## Follow-up correction — 3 November 2026

The earlier assertion "inside the card at every label length" was too broad.
The prior pair showed an improvement in value placement, but inherited nowrap
still clipped Vietnamese labels and the tablet breakpoint still hid values.
The following captures are after the F1/F2 correction, based on `548956e` plus
the focused follow-up. Their actual viewports were checked at capture time.

| file | page | viewport | language |
|---|---|---|---|
| `lab-360x800-vi-followup-wrap.jpg` | guided Payments, sustained decline; full labels wrap | 360×800 | Vietnamese |
| `lab-768x844-vi-followup-fit.jpg` | same question/scenario; tablet cards expose all columns | 768×844 | Vietnamese |

Guided client/scroll widths are 283/283px and 671/671px respectively. The
measurements cover complete cells, not just the visible crop; see the 108-state
matrix and its limits in `../verification.md`. These are in-app-browser
captures, not physical iPhone/Safari or assistive-technology tests.
