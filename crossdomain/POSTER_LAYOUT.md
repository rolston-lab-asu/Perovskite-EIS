# AI4X Poster — PPTX assembly sheet

Clean, style-unified cards for a **3-box workflow** poster (A0 portrait).
Every card is 300 dpi PNG + vector PDF in `crossdomain/output/poster/`, all sharing
one style (`poster_style.py`). Re-run a card script after any edit; re-run
`poster_style.py` values to restyle everything at once.

Reference render of the whole flow: `output/poster/workflow_A0.png`.

---

## The one rule that keeps fonts consistent

All cards use **identical font point sizes**. So text only matches if you import
them and apply the **same scale % to every card** in PowerPoint.

> **Import all cards, then set every one to the same zoom (start at ~210%).**
> Arrange into the boxes below. Never resize a single card to "make it fit" — that
> changes its font relative to the others. Resize a *whole box* of cards together,
> or change the zoom for all of them at once.

At 210% on an A0 portrait (84 cm wide), the native widths land at:

| Card width (in) | Imports at (cm) | On poster @210% (cm) | Use |
|---|---|---|---|
| 7.4 | 18.8 | **39.5** | half-column |
| 7.6 | 19.3 | **40.5** | half-column |
| 12.6 | 32.0 | **67** | wide strip |
| 13.5 | 34.3 | **72** | full-width |

Lock aspect ratio when resizing so heights follow automatically.

---

## Card inventory → which box

| File (`output/poster/`) | Role | Box | Width (in) |
|---|---|---|---|
| `perovskite_nyquist_card` | PSC Nyquist, arc grows | ① | 7.4 |
| `battery_nyquist_card` | Battery Nyquist, arc grows | ① | 7.4 |
| `ecm_perovskite_card` | Equivalent-circuit fit (recombination) | ② left | 7.6 |
| `ecm_battery_card` | Equivalent-circuit fit (charge transfer) | ② left | 7.6 |
| `drt_extraction_card` | **How** EIS → DRT (Nick's ask) | ② right | 12.6 |
| `drt_combined_card` | DRT τ overlap, shared 50 ms–2 s band | ② right | 7.4 |
| `poster_3_descriptor` | Descriptor → SOH (r=0.88) & Pmax (r=0.91) | ③ | 13.5 |

Optional / not on the workflow: `drt_battery_card`, `drt_perovskite_card`
(single-domain DRTs), `ecm_circuit` (shared circuit only),
`poster_3a/3b_*_descriptor` (single-domain descriptor panels).

---

## Section header text (use verbatim)

- **① MEASURE EIS** — *the interfacial arc grows as each device ages*
- **② READ THE SPECTRUM** — *two routes find the same interfacial process*
  - left column label: **Equivalent-circuit model (textbook)**
  - right column label: **Distribution of relaxation times (model-free)**
- **③ THE DESCRIPTOR PREDICTS MEASURED DEGRADATION** — *in both domains*

**Takeaway strip (bottom):** *Same workflow, same interfacial mechanism, same
descriptor → the premise for a model that learns degradation across both device
classes.*

**Color key:** battery = `#D55E00` (orange), perovskite = `#7C4DCB` (purple),
shared band / accents = `#C79100` (gold).

---

## Recommended arrangement (A0 portrait)

```
┌──────────────────────── TITLE + authors + QR ────────────────────────┐
├───────────────────────────────────────────────────────────────────────┤
│ ① MEASURE EIS                                                          │
│   [perovskite_nyquist_card]   →arc grows←   [battery_nyquist_card]     │
├──────────────────────────────── ↓ ────────────────────────────────────┤
│ ② READ THE SPECTRUM — two routes, same process                        │
│   Equivalent circuit (textbook) │ Distribution of relaxation times     │
│   [ecm_perovskite_card]         │ [drt_extraction_card] (wide)         │
│   [ecm_battery_card]            │ [drt_combined_card]                  │
├──────────────────────────────── ↓ ────────────────────────────────────┤
│ ③ DESCRIPTOR PREDICTS DEGRADATION — both domains                      │
│   [poster_3_descriptor]  (full width, 2 panels)                        │
├───────────────────────────────────────────────────────────────────────┤
│ takeaway strip  ·  methods  ·  refs  ·  repos                          │
└───────────────────────────────────────────────────────────────────────┘
```

`drt_extraction_card` is wide (2.4:1). If you'd rather it sit inside the right
column at matching scale, ask and I'll regenerate a stacked (tall) version.

---

## Cut from v17 (per Nick + your call)
- Arrhenius / E_a = 0.47 eV panel (battery-only, no perovskite equivalent)
- SDL / NIMO card + logo (not useful without the mechanism)
- "perovskite with 10 Hz cutoff: only the 7 µs electronic peak" annotation
