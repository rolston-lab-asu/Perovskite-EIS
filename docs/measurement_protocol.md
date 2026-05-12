# PAIOS EIS Measurement Protocol for PSC Degradation Studies

Instrument: Fluxim PAIOS 4.4 (Characterization Suite 4.4)
Application: Accelerated degradation study at 85C, simple perovskite solar cell

---

## Pre-Measurement Checklist

1. **Impedance Calibration** (Section 4.8.4 of PAIOS manual)
   - `Advanced` -> `System Calibration` -> `New Calibration` -> `Impedance and Trigger`
   - Run before every new measurement session
   - Critical at 85C: thermal expansion changes contact resistance

2. **Device equilibration**
   - Hold device at measurement bias (VOC) under illumination for 2-5 minutes
   - Wait until VOC stabilizes before starting EIS

3. **Verify contacting**
   - Use `Hardware Manager` -> `Live Control` to check V and I before long runs

---

## Recommended EIS Settings (Impedance Spectroscopy, Section 7.12)

| Parameter           | Recommended Value    | Reason                                           |
|---------------------|----------------------|--------------------------------------------------|
| Modulation Amplitude| **10 mV**            | < kT/q (30.8 mV at 85C) -> linear regime        |
| Frequency (high)    | **10 MHz**           | Captures HF geometric capacitance arc            |
| Frequency (low)     | **10 mHz**           | Captures full ionic/LF features                  |
| Frequency steps     | 50-60 (log spaced)   | Good resolution across 6 decades                 |
| Offset Voltage      | **"Measure at Voc"** | Auto-adjusts as VOC drifts during degradation    |
| Offset Light        | 1 sun equivalent     | Standard operating condition                     |
| Averaging           | 2-3                  | Improves SNR, aids KK compliance                 |
| Setup Type          | LED                  | For illuminated measurements                     |

**Why 10 mHz?** At 85C, ionic migration is ~44x faster than at 25C (Ea=0.58 eV,
Arrhenius). Ionic features that appear at ~1 Hz at 25C appear at ~44 Hz at 85C.
Measuring to 10 mHz ensures you capture the full LF arc and do not truncate it.

**Why 10 mV?** The 70 mV amplitude previously used is 2.3x kT/q at 85C.
This places the measurement in the nonlinear regime, causing KK validation to
fail with >6% residuals regardless of data quality.

---

## Time-Invariance Verification

For each operating condition, measure at least 2 consecutive sweeps:

```
Sweep 1 -> run KK -> PASS?
Sweep 2 -> run KK -> PASS?
Compare Sweep 1 vs Sweep 2:
    Mean deviation < 2% -> time-invariant -> data is valid
    Mean deviation > 2% -> device is evolving (ionic migration detected)
```

If the device is evolving, this is not necessarily bad — it is the degradation
signal you are trying to capture. Report it as such.

---

## KK Validation in PAIOS (Section 6.3.13)

PAIOS has Lin-KK built in under:
`Acquire and Manage Data` -> `Basic Postprocessing` -> `Impedance: Kramers-Kronig Test`

Interpretation:
- Upper graph: measurement + KK fit (should overlap closely)
- Lower graph: residuals vs frequency
- Residuals < 1%: excellent
- Residuals 1-2%: acceptable
- Residuals > 2%: fail — check amplitude, frequency range, and device stability

Alternatively, run the Python script in `analysis/analyze_eis.py` which uses
the Lin-KK implementation from impedance.py (Schonleber et al. 2014).

---

## Degradation Study Protocol (Series Measurement Module, Section 5.1)

Use `Modules` -> `Series Measurement` for automated stress-measure cycles:

```
Settings tab:
  Group: select or create a device group
  Setup Type: LED
  Auto-Save: enabled (saves .aio after each step)

List Generation tab:
  Type: Stress/Aging
  Electrical Stress: Constant Voltage at VOC (or 0 V for open-circuit)
  Optical Stress: 1 sun illumination
  Stress duration: 15-30 min per step
  Waiting time after stress: 2-5 min (stabilization)
  Number of steps: 50 (gives ~13 hours at 15 min/step)
  Generate Task Table -> Start Procedure
```

The Log tab shows live V, I, LED intensity vs. time — the degradation curve.

---

## Sign Convention (PAIOS Export Format)

PAIOS exports Im(Z) directly in standard EIS convention:
- Im(Z) < 0 for capacitive elements
- Im(Z) > 0 for inductive (cable artifact at very high frequencies, e.g. 10 MHz)

When parsing exported .txt files:
```python
Z_complex = Z_real + 1j * Z_imag_from_file   # CORRECT
# NOT: Z_real - 1j * Z_imag                   # WRONG
```

For Nyquist plots: y-axis = -Im(Z) = -Z_imag_from_file

---

## Common Pitfalls

| Issue                  | Symptom                        | Fix                                      |
|------------------------|--------------------------------|------------------------------------------|
| Amplitude too large    | KK residuals > 6%              | Reduce to 10 mV                          |
| Frequency cutoff high  | LF feature truncated           | Extend to 10 mHz                         |
| No equilibration       | Sweep 1 != Sweep 2             | Wait 2-5 min at VOC before measuring     |
| No calibration         | Artifacts at high/low f        | Run impedance calibration first          |
| Wrong sign in script   | KK residuals 88-98%            | Use Z = Z_real + 1j * Z_imag            |
| VOC drift during run   | Bias no longer at VOC          | Use "Measure at Voc" option              |
