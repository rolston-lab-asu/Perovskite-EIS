# Transferable Impedance-Grounded Learning for Interfacial Degradation Across Energy Systems

Analysis code and poster materials for the **AI4X Accelerate 2026** (Singapore) contribution
by **Hithesh Rai Purushothama, Marco Casareto, and Nicholas Rolston**
(Renewable Energy Materials and Devices Lab, Arizona State University).

> **One question:** can a Li-ion battery and a perovskite solar cell be read with the
> *same* impedance workflow — even though their impedances differ by ~10,000×?

---

## Summary

Batteries and solar cells fail at their internal **interfaces**, where charge is transferred,
stored, and lost. Electrochemical impedance spectroscopy (EIS) separates these processes by
their characteristic **timescale**, giving a physics-grounded, feature-engineering-free
fingerprint of interfacial aging. We apply one workflow to both device classes:

1. **Measure** EIS (PAIOS for the solar cell, BioLogic for the battery).
2. **Model** each spectrum with the *same* equivalent circuit (Rₛ + two R‖CPE arcs).
3. **Resolve** the dominant interfacial process model-free, via the **distribution of
   relaxation times (DRT)** — a Tikhonov-regularized inversion to γ(τ).
4. **Predict** degradation from a single arc-resistance descriptor *R*ₚ.

**Findings**
- Both devices degrade through the same signature: a **growing interfacial arc**.
- DRT places the dominant aging relaxation in the **same 50 ms – 2 s band** in both —
  charge transfer (τ ≈ 0.16 s) for the battery, ion migration (τ ≈ 1.3 s) for the
  perovskite — despite different chemistry and a 10⁴× impedance gap.
- The arc descriptor *R*ₚ predicts **measured** degradation in both domains:
  battery state of health **|r| = 0.88**, perovskite *P*max retention **|r| = 0.91**.

This is a **proof-of-concept**: the perovskite side is a small device set, so the work
evidences the *premise* for cross-device transfer learning rather than a validated transfer
model. The overlapping relaxations are physically distinct (ionic migration vs. charge
transfer) but occupy the same region of timescale-space and grow the same way with aging.

---

## Datasets

| Domain | Cell | Conditions | EIS sweep |
|--------|------|-----------|-----------|
| Li-ion battery | Molicel P42A NMC 21700, 4.0 Ah (CA1–CA8) | Room temperature; 2C charge to 4.2 V, **3.75C discharge**, to end-of-life | 10 kHz – 1 Hz |
| Perovskite | Cs₂₀FA₈₀PbI₃ solar cell | 1-sun light soak at 358 K (PAIOS); periodic JV at 0/50/100 % intensity | 10 MHz – 10 mHz |

Battery performance label = discharge capacity normalized to cycle 0 (SOH = Q/Q₀).
Perovskite label = max-power point from the periodic 1-sun JV, normalized to the first
measurement (*P*max retention = Pₘₚₚ/Pₘₚₚ,₀) — an independent measurement, **not** derived
from the impedance.

---

## Reproduce

Requires the parent `LIB-EIS-ML` repo (the battery DRT pipeline lives in
`battery_gpytorch_rtx4060/battery_gpytorch/`). From the repo root, with the venv active:

```bash
source battery_gpytorch_rtx4060/.venv/Scripts/activate

# parse the perovskite PAIOS exports -> data/perovskite/*.npz
python -X utf8 crossdomain/perovskite_parse_v2.py

# build the poster figure cards (300 dpi PNG + vector PDF -> output/poster/)
python -X utf8 crossdomain/battery_nyquist_single.py   # Nyquist hooks
python -X utf8 crossdomain/ecm_cards.py                # equivalent-circuit fits + circuit
python -X utf8 crossdomain/drt_cards.py                # DRT cards + combined overlap
python -X utf8 crossdomain/drt_extraction_card.py      # EIS -> DRT schematic
python -X utf8 crossdomain/poster_figs.py              # Nyquist, DRT overlap, descriptor
```

All cards share one style (`poster_style.py`); edit it once and re-run to restyle everything.

---

## Repository layout

| File | Purpose |
|------|---------|
| `poster_text.md` | All poster copy — Background, Steps 1–4, conclusion, Fig. 1–9 captions |
| `POSTER_LAYOUT.md` | PowerPoint assembly sheet + the font-consistency rule |
| `poster_style.py` | Shared palette + Matplotlib style for every card |
| `perovskite_parse_v2.py` | Parse PAIOS IS + JV exports → `data/perovskite/*.npz` |
| `battery_nyquist_single.py` | Nyquist degradation hooks (battery, perovskite) |
| `ecm_cards.py` / `ecm_perovskite.py` | Equivalent-circuit fits + drawn circuit |
| `drt_cards.py` / `drt_extraction_card.py` | DRT per domain, combined overlap, EIS→DRT schematic |
| `poster_figs.py` | Nyquist hook, DRT τ-overlap, descriptor→performance |
| `kk_check_crossdomain.py` | Kramers–Kronig (lin-KK) causality checks |
| `workflow_assembly.py` | Reference render of the assembled workflow poster |
| `data/perovskite/` | Parsed perovskite EIS + JV series (npz) |
| `output/` | Generated figures (git-ignored — regenerate with the scripts) |

---

## Key references

Zhang et al., *Nat. Commun.* 11, 1706 (2020) · Jones et al., *Nat. Commun.* 13, 4806 (2022) ·
von Hauff & Klotz, *J. Mater. Chem. C* 10, 742 (2022) · Clarke et al., *Adv. Energy Mater.*
(2024) · Maradesa et al., *Joule* 8 (2024) · Thiesbrummel et al., *Nat. Energy* 9, 664 (2024) ·
Diekmann et al., *ACS Energy Lett.* 11, 3395 (2026) · Stiaszny et al., *J. Power Sources* 258,
61 (2014).

Perovskite stability metrics follow the ISOS consensus (Khenkin et al., *Nat. Energy* 5, 35,
2020).

---

## Contact

Hithesh Rai Purushothama — `hraipuru@asu.edu` · Renewable Energy Materials and Devices Lab,
Arizona State University.

We thank the Experiential Grant program, members of the Rolston Lab, and the guidance of
Dr. Shoichi Matsuda and his team at NIMS.
