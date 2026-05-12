# Design of Experiments (DOE) Recommendations

PSC Degradation Study at 85C using PAIOS EIS

---

## Context

Device: Simple (single-junction) perovskite solar cell
Goal: Understand degradation mechanisms through EIS time-series at 85C
Instrument: PAIOS 4.4.1 (Fluxim)
Current datasets: 50 sweeps (light only) + 96 sweeps (light + dark) over ~13h

---

## Issues Found in Existing Data

| Issue | Impact | Priority |
|-------|--------|----------|
| Amplitude 70 mV (2.3x kT/q at 85C) | KK residuals 6-7% (fail); parameters distorted | Critical |
| Frequency low cutoff at 10 Hz | Ionic LF features at ~44 Hz at 85C may be truncated | High |
| Fixed offset 0.75 V instead of Voc | Bias drifts from VOC during degradation | Medium |
| No impedance calibration confirmed | Possible systematic artifacts at high/low f | Medium |

---

## Corrected DOE for Remeasurement

### Experiment A: Baseline at Room Temperature

Purpose: Establish reference spectrum before degradation, compare to literature.

| Parameter | Value |
|-----------|-------|
| Temperature | 25C |
| Amplitude | 10 mV |
| Frequency | 10 mHz to 10 MHz |
| Bias | Measure at Voc |
| Illumination | 1 sun |
| Sweeps | 3 consecutive (verify time-invariance) |
| Also measure | JV (forward + reverse), dark JV |

### Experiment B: Degradation Time-Series at 85C (Primary DOE)

Purpose: Track impedance evolution during accelerated degradation.

| Parameter | Value |
|-----------|-------|
| Temperature | 85C |
| Amplitude | 10 mV |
| Frequency | 10 mHz to 10 MHz |
| Bias | Measure at Voc |
| Illumination | 1 sun |
| Stress interval | 15 min illumination stress |
| Wait before EIS | 2 min equilibration |
| Total steps | 50 (gives ~13 hours) |
| JV after each EIS | Yes (forward + reverse) |

Use PAIOS Series Measurement Module to automate this.

### Experiment C: Dark EIS Comparison

Purpose: Separate electronic from ionic contributions.

| Parameter | Value |
|-----------|-------|
| Temperature | 85C |
| Amplitude | 10 mV |
| Frequency | 10 mHz to 10 MHz |
| Bias | Forward bias at same V as Voc in light |
| Illumination | None (dark) |
| Sweeps | 3 consecutive |
| Timing | Before and after light degradation |

### Experiment D: Arrhenius Analysis (Optional Extension)

Purpose: Extract ionic migration activation energy.

- Repeat Experiment B at: 25C, 45C, 65C, 85C
- Extract LF and MF feature frequencies at each temperature
- Plot ln(f) vs 1/T -> slope gives activation energy Ea
- Expected Ea ~ 0.58 eV for iodide vacancies in MAPbI3

---

## What to Extract from Each Spectrum

From equivalent circuit fitting (R + R1C1 + R2C2 model):

| Parameter | Symbol | Physical meaning |
|-----------|--------|------------------|
| Series resistance | R_s | Contact + transport resistance |
| HF resistance | R_HF | Recombination resistance |
| HF capacitance | C_HF | Geometric capacitance (C = e*e0*A/d) |
| HF time constant | tau_HF = R_HF * C_HF | Should stay constant if only area changes |
| LF resistance | R_LF | Ionic-modulated recombination |
| LF capacitance | C_LF | Apparent ionic capacitance |
| LF time constant | tau_LF | Ion migration timescale |

**Key diagnostic (Klotz et al.):**
If R_HF increases AND C_HF decreases with tau_HF constant -> active area loss
due to ionic migration. Reversible if device kept in dark for 24h.

**Spectral type classification (Clarke et al.):**
Identify which animal shape the Nyquist plot resembles (ladybird, elephant,
hippo, manatee, rabbit, tortoise) to determine carrier density regime and
dominant recombination mechanism.

---

## Expected Results at 85C

Based on Klotz et al. (25C) scaled to 85C (Arrhenius, Ea = 0.58 eV):

| Timescale (25C) | Timescale (85C) | Process |
|-----------------|-----------------|---------|
| ~10-20 hours to double R | ~15-30 min | R_HF increase from active area loss |
| ~24 hours to recover | ~30-60 min in dark | Recovery of ionic equilibrium |
| tau_HF < 2 ms | tau_HF < 2 ms | Should stay constant (geometry) |

This means your 50-sweep / 13-hour dataset at 85C is likely capturing the
FULL cycle of ionic migration-driven active area loss, not just the onset.
Repeated measurements may show faster initial drift in later cycles (as
Klotz et al. observed — each cycle's drift accelerates after the first).

---

## Analysis Workflow

```
1. Check impedance calibration was run
2. Parse PAIOS .txt with analysis/analyze_eis.py
3. Plot nyquist_all.png -> identify spectral type (animal shape)
4. Plot consecutive_check.png -> confirm time-invariance or detect drift
5. Plot time_evolution.png -> track R and C vs sweep number
6. Run KK validation -> confirm data quality (target: max residual < 2%)
7. Fit equivalent circuit (PAIOS built-in or impedance.py)
8. Extract R_HF, C_HF, tau_HF for each sweep
9. Plot R_HF, C_HF, tau_HF vs time -> check Klotz et al. pattern
10. Correlate with JV parameters (Voc, FF, PCE) measured after each EIS
```
