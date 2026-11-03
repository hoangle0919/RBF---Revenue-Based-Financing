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
