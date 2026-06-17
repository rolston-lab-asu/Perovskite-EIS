# Perovskite Solar Cell EIS Analysis

Tools and documentation for electrochemical impedance spectroscopy (EIS)
characterization of perovskite solar cells (PSCs), with a focus on
accelerated degradation studies at elevated temperature using the
Fluxim PAIOS platform.

---

## Repository Structure

```
Perovskite-EIS/
├── analysis/
│   └── analyze_eis.py        # Main PAIOS data parser + KK validation script
├── data/
│   └── .gitkeep              # Place PAIOS .txt exports here (not committed)
├── docs/
│   ├── eis_fundamentals.md   # EIS theory, PSC spectral zoo, ionic migration
│   ├── measurement_protocol.md  # PAIOS settings, sign convention, calibration
│   └── doe_recommendations.md   # DOE design for 85C degradation study
├── crossdomain/              # AI4X 2026 cross-domain study (see below)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Cross-Domain Study — AI4X Accelerate 2026

The [`crossdomain/`](crossdomain/) folder holds the analysis behind the AI4X
Accelerate 2026 poster *"Transferable Impedance-Grounded Learning for Interfacial
Degradation Across Energy Systems"* (Purushothama, Casareto, Rolston). One EIS
workflow — equivalent-circuit fitting **and** distribution of relaxation times (DRT) —
is applied to both a **perovskite solar cell** and a **Li-ion battery**. Both dominant
aging relaxations fall in the same 50 ms–2 s timescale band, and a single arc-resistance
descriptor predicts measured degradation in each (perovskite *P*max retention |r| = 0.91,
battery state of health |r| = 0.88). See [`crossdomain/README.md`](crossdomain/README.md)
for details; the battery DRT pipeline lives in the companion `LIB-EIS-ML` repository.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Place data files

Copy your PAIOS EIS `.txt` export files into the `data/` folder.
The `.gitignore` ensures they will never be committed.

### 3. Update filenames and run

Edit the filenames in `analysis/analyze_eis.py` `main()` function, then:

```bash
python analysis/analyze_eis.py
```

Figures are saved to `data/figures/`.

---

## What the Script Does

For each PAIOS EIS dataset:

| Output | Description |
|--------|-------------|
| `*_nyquist_all.png` | All sweeps on one Nyquist plot, coloured by time |
| `*_bode.png` | Bode magnitude + phase for selected sweeps |
| `*_time_evolution.png` | Z' and -Z'' at 6 frequencies tracked across sweeps |
| `*_consecutive_check.png` | Sweep 1 vs 2 and sweep N-1 vs N overlap check |
| `*_kk_validation.png` | Lin-KK fit + residuals for 6 selected sweeps |

KK residuals are printed to console with PASS / FAIL per sweep.

---

## Key Learnings

### EIS Fundamentals

- EIS measures complex impedance Z(w) = Z' + jZ'' across frequencies
- Nyquist plot: -Z'' vs Z'. Capacitive arcs appear above the x-axis
- KK validity requires: linearity (amplitude << kT/q), stability, causality
- Lin-KK (Schonleber 2014): fits Voigt RC chain; residuals < 2% = valid data

### PSC Spectral Zoo (Clarke et al. 2024)

Six Nyquist shapes occur in PSCs, all explained by standard drift-diffusion:

| Shape | Name | Key signature |
|-------|------|---------------|
| HF + positive LF | Ladybird | Small carrier density |
| HF + negative LF | Elephant | SRH type switches |
| HF + pos MF + pos LF | Hippo | Large hole density |
| HF + neg MF + neg LF | Manatee | Hole-limited SRH |
| HF + pos MF + neg LF | Rabbit | Large electron density |
| HF + pos MF + neg LF | Tortoise | Hole-limited SRH variant |

A third (mid-frequency) feature appears when carrier density is large enough
to partially screen the electric field, displacing ions from bulk equilibrium.

### Ionic Migration and Time-Invariance (Klotz et al. 2019)

- PSC impedance drifts significantly over time at VOC under illumination
- R_HF increases, C_HF decreases, tau_HF = R*C stays constant
- Physical cause: temporary loss of active area due to ionic migration
  (ion/vacancy accumulation at ETL/HTL interfaces creates recombination centres)
- Effect is ~100% reversible after 24h in dark
- At 85C, this process is ~44x faster (Arrhenius, Ea = 0.58 eV)
- Always measure 2+ consecutive sweeps to verify time-invariance

### Rise Time Constants (Ravishankar et al. 2024)

- Traditional IMVS/IMPS analysis captures only the decay time constant (recombination)
- The rise time constant (charge extraction) is hidden when tau_decay >> tau_rise
- Modified transfer function M_W = i*w*W reveals both peaks
- Figure of Merit FOM = 1/(1 + tau_rise/tau_decay) quantifies collection efficiency

### PAIOS-Specific Notes

- **Sign convention**: PAIOS exports Im(Z) directly (Im(Z) < 0 = capacitive)
  - Parse as: `Z = Z_real + 1j * Z_imag` (NOT `-1j`)
- **Amplitude**: use 10 mV (not 70 mV); 70 mV = 2.3x kT/q at 85C -> nonlinear
- **Frequency**: extend to 10 mHz; stopping at 10 Hz misses ionic LF features
- **KK test**: built into PAIOS Basic Postprocessing (Section 6.3.13)
- **Series Measurement Module**: automates stress -> EIS -> JV cycles for degradation studies
- **Calibration**: run impedance calibration before every session

---

## Recommended PAIOS Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| Modulation Amplitude | **10 mV** | < kT/q at any temperature |
| Frequency range | **10 mHz -- 10 MHz** | Captures HF + LF + ionic features |
| Bias | **Measure at Voc** | Tracks VOC drift during degradation |
| Averaging | 2-3 | Improves SNR and KK compliance |
| Setup Type | LED | For illuminated measurements |

---

## References

1. Lazanas & Prodromidis, *ACS Meas. Sci. Au* **2023**, 3, 162.
   DOI: [10.1021/acsmeasuresciau.2c00070](https://doi.org/10.1021/acsmeasuresciau.2c00070)

2. Klotz et al., *RSC Adv.* **2019**, 9, 33436.
   DOI: [10.1039/c9ra07048f](https://doi.org/10.1039/c9ra07048f)

3. Clarke et al., *Adv. Energy Mater.* **2024**, 14, 2400955.
   DOI: [10.1002/aenm.202400955](https://doi.org/10.1002/aenm.202400955)

4. Ravishankar et al., *Energy Environ. Sci.* **2024**, 17, 1229.
   DOI: [10.1039/d3ee02013d](https://doi.org/10.1039/d3ee02013d)

5. Roose et al., *ACS Energy Lett.* **2024**, 9, 442.
   DOI: [10.1021/acsenergylett.3c02018](https://doi.org/10.1021/acsenergylett.3c02018)

6. Schonleber et al., *Electrochim. Acta* **2014**, 131, 20.
   DOI: [10.1016/j.electacta.2014.01.034](https://doi.org/10.1016/j.electacta.2014.01.034)

---

## License

MIT
