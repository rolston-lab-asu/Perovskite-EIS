"""Quick check: do battery and perovskite DRT relaxation times overlap?
Uses the SAME compute_drt (NIMS Tikhonov-NNLS) on both domains."""
import sys, os
import numpy as np
sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell, BANDS, band_features

# ---- perovskite ----
d = np.load(r"crossdomain\data\perovskite\perovskite_aging.npz")
freqs, Re, Im = d["freqs"], d["Re"], d["Im"]
n_spec = Re.shape[1]
tau_peak_p = []
for k in range(n_spec):
    tau, gamma, r_inf = compute_drt(freqs, Re[:, k], -Im[:, k])  # pass -Im so capacitive>0
    if tau is None:
        tau_peak_p.append(np.nan); continue
    tau_peak_p.append(tau[np.argmax(gamma)])
tau_peak_p = np.array(tau_peak_p)
print(f"PEROVSKITE DRT peak tau: {np.nanmin(tau_peak_p):.2e} -> {np.nanmax(tau_peak_p):.2e} s")
print(f"  early(0): {tau_peak_p[0]:.2e} s   late(-1): {tau_peak_p[-1]:.2e} s")

# ---- battery (CA cells) tau_c_CT ----
print("\nBATTERY tau_c_CT (charge-transfer centroid), per cell early->late:")
all_ct = []
for cell in ["CA1","CA4","CA7","CA8"]:
    eis, cap, cyc, soh = load_cell(cell)
    tcs = []
    for i in range(eis.shape[0]):
        tau, gamma, r_inf = compute_drt(NATIVE_FREQS, eis[i,:33], eis[i,33:])
        if tau is None: continue
        _, tc_CT = band_features(tau, gamma, *BANDS[1][1:])
        if np.isfinite(tc_CT): tcs.append(tc_CT)
    tcs = np.array(tcs); all_ct.extend(tcs)
    print(f"  {cell}: {tcs[0]:.2e} -> {tcs[-1]:.2e} s   (range {tcs.min():.2e}-{tcs.max():.2e})")
all_ct = np.array(all_ct)
print(f"\nBATTERY tau_c_CT overall: {all_ct.min():.2e} -> {all_ct.max():.2e} s")
print(f"PEROVSKITE peak tau overall: {np.nanmin(tau_peak_p):.2e} -> {np.nanmax(tau_peak_p):.2e} s")
