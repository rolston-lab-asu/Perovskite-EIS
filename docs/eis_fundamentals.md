# EIS Fundamentals for Perovskite Solar Cells

Summary of key concepts from the literature reviewed for this project.

---

## 1. What is EIS?

Electrochemical Impedance Spectroscopy applies a small sinusoidal voltage
perturbation V(t) = V_DC + V_p sin(wt) to a device and measures the current
response. The complex impedance is:

    Z(w) = V_p / I_p * e^(j*phi) = Z' + jZ''

where Z' is resistance (real part) and Z'' is reactance (imaginary part).
For capacitive elements: Z'' < 0.

**Nyquist plot**: -Z'' vs Z' at each frequency (capacitive semicircles appear
above the x-axis).

**Bode plot**: |Z| and phase vs frequency (log scale).

---

## 2. Validity Conditions (Kramers-Kronig)

For EIS data to be physically valid, the system must satisfy:
- **Linearity**: perturbation amplitude << kT/q (~26 mV at 25C, ~31 mV at 85C)
- **Causality**: response only from applied perturbation
- **Stability**: system does not change during one sweep
- **Finiteness**: Z(w) is finite for all w

**KK validation** (Lin-KK method, Schonleber et al. 2014):
- Fits the spectrum with a Voigt RC chain (always KK-compliant by construction)
- If residuals < 1%: excellent; < 2%: acceptable; >= 2%: fail
- Failure indicates nonlinearity or non-stationarity

---

## 3. PSC Impedance Spectra — The Zoo (Clarke et al. 2024)

PSC Nyquist plots are classified into 6 types named after animals:

| Name     | Shape              | Conditions                                      |
|----------|--------------------|-------------------------------------------------|
| Ladybird | HF + positive LF   | Low carrier density, SRH-dominated              |
| Elephant | HF + negative LF   | Same, but recombination type switches           |
| Hippo    | HF + pos MF + pos LF | Large hole density, electron-limited SRH      |
| Manatee  | HF + neg MF + neg LF | Large hole density, hole-limited SRH          |
| Rabbit   | HF + pos MF + neg LF | Large electron density, electron-limited SRH  |
| Tortoise | HF + pos MF + neg LF | Large electron density, hole-limited SRH      |

All shapes are explained by the standard ionic-electronic drift-diffusion
model — no exotic physics required.

**HF arc**: related to geometric capacitance and recombination resistance.
**LF arc**: related to ionic migration modulating recombination current.
**MF arc**: appears when carrier density is large enough to displace ions
            from equilibrium, creating a second ionic timescale.

---

## 4. Ionic Migration and Time-Invariance (Klotz et al. 2019)

PSCs are NOT time-invariant at VOC under illumination:
- R_HF increases and C_HF decreases over hours, while tau = RC stays constant
- This indicates temporary loss of electronically active area due to ionic migration
- Ion/vacancy accumulation at ETL/HTL interfaces creates recombination centres
- Effect is ~100% reversible after 24h in the dark

**Consequence**: always measure 2+ consecutive sweeps to verify time-invariance.
If they differ, you are capturing ionic migration dynamics (scientifically useful).

**Thermal acceleration**: at 85C (358K), ionic diffusion is ~44x faster than
at 25C (298K), assuming activation energy Ea = 0.58 eV (Arrhenius).
So Klotz et al.'s 20-hour effects compress to ~30 minutes at 85C.

---

## 5. Rise vs Decay Time Constants (Ravishankar et al. 2024)

TPV/TPC (time-domain) naturally gives TWO time constants:
- tau_rise: charge extraction (related to transport layer mobility)
- tau_decay: recombination lifetime

IMVS/IMPS (frequency-domain, traditional analysis) gives only ONE (the decay).
The rise constant is hidden because tau_decay >> tau_rise.

**Solution**: define modified transfer function M_W = i*w*W (for IMVS).
Its negative imaginary part shows TWO peaks, giving both time constants.

**Figure of Merit** for charge collection efficiency:
    FOM = 1 / (1 + tau_rise / tau_decay)
Values 0.7-0.95 near 1-sun VOC indicate efficient extraction.

---

## 6. Key References

1. Lazanas & Prodromidis, *ACS Meas. Sci. Au* **2023**, 3, 162-193.
   DOI: 10.1021/acsmeasuresciau.2c00070 — EIS tutorial

2. Lazanas & Prodromidis, *ACS Meas. Sci. Au* **2025**, 5, 156.
   DOI: 10.1021/acsmeasuresciau.5c00007 — Correction to tutorial

3. Klotz et al., *RSC Adv.* **2019**, 9, 33436-33445.
   DOI: 10.1039/c9ra07048f — Reversible changes in PSCs by EIS

4. Clarke et al., *Adv. Energy Mater.* **2024**, 14, 2400955.
   DOI: 10.1002/aenm.202400955 — Full zoo of PSC impedance spectra

5. Ravishankar et al., *Energy Environ. Sci.* **2024**, 17, 1229-1243.
   DOI: 10.1039/d3ee02013d — Rise time constants for charge extraction

6. Roose et al., *ACS Energy Lett.* **2024**, 9, 442-453.
   DOI: 10.1021/acsenergylett.3c02018 — EIS of all-perovskite tandems
