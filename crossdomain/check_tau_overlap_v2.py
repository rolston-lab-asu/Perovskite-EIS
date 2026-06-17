"""tau-overlap check v2 — full-range perovskite sweeps (10 MHz -> 10 mHz).

v1 (check_tau_overlap.py) used the 10 Hz-truncated sweep and found NO overlap:
perovskite peak tau ~7e-6 s (electronic) vs battery CT tau ~0.16 s, 4.4 decades apart.
The new 85C campaign reaches 10 mHz, so the slow ionic feature (ms-s) is now in-band.
Question: does a perovskite DRT feature now land in the battery CT band (5e-2 - 2 s)?

Same NIMS Tikhonov-NNLS compute_drt on both domains; FREQ_MIN lowered to keep
the sub-Hz perovskite points (default 0.1 Hz floor was set for the CA battery data).
"""
import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell, BANDS, band_features

CT_LO, CT_HI = BANDS[1][1], BANDS[1][2]          # battery charge-transfer band, 50 ms - 2 s


def drt_peaks(tau, gamma, frac=0.05):
    """tau of local maxima of gamma above frac*max."""
    thr = frac * gamma.max()
    pk = []
    for i in range(1, len(gamma) - 1):
        if gamma[i] >= gamma[i - 1] and gamma[i] >= gamma[i + 1] and gamma[i] > thr:
            pk.append(tau[i])
    return np.array(pk)


# ---- battery CT centroid (same as v1) -----------------------------------------
print("BATTERY tau_c_CT (charge-transfer centroid):")
all_ct = []
for cell in ["CA1", "CA4", "CA7", "CA8"]:
    eis, cap, cyc, soh = load_cell(cell)
    tcs = []
    for i in range(eis.shape[0]):
        tau, gamma, _ = compute_drt(NATIVE_FREQS, eis[i, :33], eis[i, 33:])
        if tau is None:
            continue
        _, tc = band_features(tau, gamma, CT_LO, CT_HI)
        if np.isfinite(tc):
            tcs.append(tc)
    all_ct.extend(tcs)
    print(f"  {cell}: {tcs[0]:.2e} -> {tcs[-1]:.2e} s")
all_ct = np.array(all_ct)
print(f"  overall: {all_ct.min():.2e} - {all_ct.max():.2e} s\n")

# ---- perovskite full-range series ----------------------------------------------
drt.FREQ_MIN = 0.005          # keep the 10 mHz points (module default 0.1 clips them)

fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharex=True)
results = {}
for ax, key, label in zip(axes,
                          ["d358_full", "l358_full"],
                          ["dark device @358 K (clean)", "light device @358 K (drifting)"]):
    d = np.load(rf"crossdomain\data\perovskite\pero_{key}.npz")
    freqs, Re, Im = d["freqs"], d["Re"], d["Im"]
    n_t = Re.shape[1]
    cmap = plt.cm.viridis(np.linspace(0, 1, n_t))
    print(f"PEROVSKITE {key} ({label}), {n_t} spectra:")
    ct_mass_frac, peaks_all = [], []
    for k in range(n_t):
        tau, gamma, _ = compute_drt(freqs, Re[:, k], -Im[:, k])
        if tau is None or not np.isfinite(gamma).all():
            ct_mass_frac.append(np.nan)
            continue
        pk = drt_peaks(tau, gamma)
        peaks_all.append(pk)
        g_ct, tc_ct = band_features(tau, gamma, CT_LO, CT_HI)
        dln = np.log(tau[1] / tau[0])
        g_tot = gamma.sum() * dln
        ct_mass_frac.append(g_ct / g_tot if g_tot > 0 else np.nan)
        ax.plot(tau, gamma / gamma.max(), color=cmap[k], lw=0.8, alpha=0.7)
        if k in (0, n_t - 1):
            in_ct = pk[(pk >= CT_LO) & (pk <= CT_HI)]
            print(f"  spectrum {k:2d}: peaks at " +
                  ", ".join(f"{t:.1e}" for t in pk) +
                  f" s | in CT band: {['no', 'YES'][len(in_ct) > 0]}"
                  f" | tc_CT={tc_ct:.2e} s | CT mass frac={ct_mass_frac[-1]:.2f}")
    pk_cat = np.concatenate(peaks_all)
    in_band = pk_cat[(pk_cat >= CT_LO) & (pk_cat <= CT_HI)]
    print(f"  -> {len(in_band)}/{len(pk_cat)} DRT peaks fall inside battery CT band "
          f"({CT_LO:.0e}-{CT_HI:.0e} s); median CT mass frac = "
          f"{np.nanmedian(ct_mass_frac):.2f}\n")
    results[key] = (pk_cat, ct_mass_frac)

    ax.axvspan(CT_LO, CT_HI, color="#d0f0d8", zorder=0,
               label=f"battery CT band\n(tau_c {all_ct.min():.2f}-{all_ct.max():.2f} s)")
    ax.axvspan(7e-6 / 3, 7e-6 * 3, color="#f0d0d0", zorder=0,
               label="v1 peak (10 Hz cutoff)\ntau~7e-6 s, electronic")
    ax.set_xscale("log")
    ax.set_xlabel("tau / s")
    ax.set_ylabel("gamma / max(gamma)")
    ax.set_title(f"perovskite DRT, {label}\n(viridis: early->late, 10 MHz-10 mHz)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")

plt.tight_layout()
p = r"crossdomain\output\fig_tau_overlap_v2.png"
fig.savefig(p, dpi=140, bbox_inches="tight")
print(f"Saved {p}")
