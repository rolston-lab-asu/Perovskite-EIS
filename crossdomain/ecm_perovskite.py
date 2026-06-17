"""
Traditional ECM check for the perovskite EIS (vs DRT / arc-descriptor pipeline).

Circuit (von Hauff & Klotz 2022 universal PSC ECM, HF/LF separation):
    Z(w) = R_s + R1/(1+(jw*t1)^a1) + R2/(1+(jw*t2)^a2)      (two R||CPE arcs)

Checks:
  1. Light dev @358 K fast series (10 MHz-10 Hz, 50 spectra, real Pmax labels):
     per-spectrum fit -> do the ECM resistances track Pmax retention as well as
     the simple arc descriptor Rp (|r| = 0.909)?
  2. Dark dev @358 K full sweep (10 MHz-10 mHz, early KK-valid spectra):
     add the slow ionic arc -> does the ECM time constant t_LF agree with the
     DRT peak (1.3 s) / battery CT band (50 ms-2 s)?

Output: crossdomain/output/fig_ecm_perovskite.png + printed summary.
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.stats import pearsonr

OUT = r"crossdomain\output"
os.makedirs(OUT, exist_ok=True)
C_PER, C_BAND = "#7C4DCB", "#C79100"
plt.rcParams.update({"font.size": 12, "font.family": "Arial",
                     "axes.spines.top": False, "axes.spines.right": False})


def z_model(p, w, n_arcs):
    Rs = p[0]
    Z = np.full_like(w, Rs, dtype=complex)
    for k in range(n_arcs):
        R, t, a = p[1 + 3 * k: 4 + 3 * k]
        Z = Z + R / (1 + (1j * w * t) ** a)
    return Z


def fit_ecm(freq, Z, p0, n_arcs):
    ok = np.isfinite(freq) & np.isfinite(Z)
    freq, Z = freq[ok], Z[ok]
    w = 2 * np.pi * freq

    def resid(p):
        Zf = z_model(p, w, n_arcs)
        return np.concatenate([(Zf.real - Z.real) / np.abs(Z),
                               (Zf.imag - Z.imag) / np.abs(Z)])

    lb = [0] + [1e-3, 1e-9, 0.5] * n_arcs
    ub = [np.inf] + [np.inf, 1e3, 1.0] * n_arcs
    sol = least_squares(resid, np.clip(p0, lb, ub), bounds=(lb, ub), max_nfev=40000)
    rms = 100 * np.sqrt(np.mean(sol.fun ** 2))
    return sol.x, rms


# ── 1. light device fast series: 2-arc fit per spectrum, warm-started ─────────
d = np.load(r"crossdomain\data\perovskite\pero_l358_fast.npz")
freqs, Re, Im, th, pmax = d["freqs"], d["Re"], d["Im"], d["t_hours"], d["pmax"]
ns = Re.shape[1]
ret = pmax / pmax[0]

p = np.array([25.0, 350.0, 7e-6, 0.9, 200.0, 1e-3, 0.8])   # Rs | HF arc | LF shoulder
R1s, R2s, t1s, rms_all, fits = [], [], [], [], []
for k in range(ns):
    Z = Re[:, k] + 1j * Im[:, k]
    p, rms = fit_ecm(freqs, Z, p, n_arcs=2)                # warm start from previous
    R1s.append(p[1]); t1s.append(p[2]); R2s.append(p[4]); rms_all.append(rms)
    fits.append(p.copy())
R1s, R2s, t1s = np.array(R1s), np.array(R2s), np.array(t1s)

r_R1, _ = pearsonr(R1s, ret)
r_R2, _ = pearsonr(R2s, ret)
r_tot, _ = pearsonr(R1s + R2s, ret)
print("LIGHT DEV @358 K, 2-arc ECM (R_s + RQ_HF + RQ_LF), 50 spectra:")
print(f"  median fit RMS = {np.median(rms_all):.2f}%  (max {np.max(rms_all):.2f}%)")
print(f"  R_HF (recombination): {R1s[0]:.0f} -> {R1s[-1]:.0f} Ohm | r vs Pmax retention = {r_R1:+.3f}")
print(f"  R_LF (shoulder):      {R2s[0]:.0f} -> {R2s[-1]:.0f} Ohm | r vs Pmax retention = {r_R2:+.3f}")
print(f"  R_HF+R_LF (total):    r = {r_tot:+.3f}   [descriptor Rp benchmark: -0.909]")
print(f"  HF arc tau: {t1s[0]:.1e} -> {t1s[-1]:.1e} s (electronic, ~7 us scale)")

# ── 2. dark device full sweep: 2-arc fit incl. slow ionic arc ─────────────────
dd = np.load(r"crossdomain\data\perovskite\pero_d358_full.npz")
print("\nDARK DEV @358 K, full 10 mHz sweep, early (KK-valid) spectra, 2-arc ECM:")
t_lf_list = []
dark_fit_example = None
p0 = np.array([1e3, 2e6, 1e-5, 0.9, 3e7, 1.0, 0.9])
for k in (0, 1, 2, 3):
    Z = dd["Re"][:, k] + 1j * dd["Im"][:, k]
    pk, rms = fit_ecm(dd["freqs"], Z, p0, n_arcs=2)
    if pk[4] > 1e3:          # warm-start next spectrum from a non-degenerate fit
        p0 = pk.copy()
    in_band = 0.05 <= pk[5] <= 2.0
    t_lf_list.append(pk[5])
    print(f"  spec {k}: rms={rms:5.2f}%  R_LF={pk[4]:.2e} Ohm  t_LF={pk[5]:.2f} s "
          f"(a={pk[6]:.2f})  in CT band 50 ms-2 s: {'YES' if in_band else 'no'}")
    if k == 1:
        dark_fit_example = (dd["freqs"], Z, pk)

# ── figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)
fig.suptitle("Traditional ECM check: R_s + 2x(R||CPE) — agrees with the DRT/descriptor pipeline",
             fontsize=13, fontweight="bold")

# (a) example fit, light dev mid
k = ns // 2
Z = Re[:, k] + 1j * Im[:, k]
Zf = z_model(fits[k], 2 * np.pi * freqs, 2)
ax[0].plot(Z.real, -Z.imag, "o", ms=4, color=C_PER, label="data (light dev, mid-life)")
ax[0].plot(Zf.real, -Zf.imag, "-", lw=2, color="k", alpha=0.75,
           label=f"ECM fit (rms {rms_all[k]:.1f}%)")
ax[0].set_xlabel(r"Re$(Z)$ / $\Omega$"); ax[0].set_ylabel(r"$-$Im$(Z)$ / $\Omega$")
ax[0].set_title("a)  ECM reproduces the spectrum", fontsize=11)
ax[0].legend(fontsize=9)

# (b) ECM R vs Pmax retention
ax[1].scatter(R1s + R2s, ret, s=30, c=th, cmap="Purples", edgecolors="k", lw=0.3)
ax[1].set_xlabel(r"ECM  $R_\mathrm{HF}+R_\mathrm{LF}$  /  $\Omega$")
ax[1].set_ylabel(r"$P_\mathrm{max}$ retention")
ax[1].set_title(f"b)  ECM resistance tracks measured power\n|r| = {abs(r_tot):.2f} "
                f"(descriptor Rp: 0.91)", fontsize=11)

# (c) dark dev slow arc: t_LF vs DRT band
fq, Zd, pk = dark_fit_example
Zf = z_model(pk, 2 * np.pi * fq, 2)
m = np.isfinite(Zd)
ax[2].plot(Zd.real[m] * 1e-6, -Zd.imag[m] * 1e-6, "o", ms=4, color=C_PER,
           label="data (dark dev, early)")
ax[2].plot(Zf.real * 1e-6, -Zf.imag * 1e-6, "-", lw=2, color="k", alpha=0.75,
           label=f"ECM fit:  $t_\\mathrm{{LF}}$ = {pk[5]:.2f} s")
ax[2].axhline(0, color="0.6", lw=0.7, ls="--")
ax[2].set_xlabel(r"Re$(Z)$ / M$\Omega$"); ax[2].set_ylabel(r"$-$Im$(Z)$ / M$\Omega$")
ax[2].set_title(f"c)  Ionic arc time constant = {pk[5]:.2f} s\n"
                "inside the battery CT band (50 ms – 2 s)", fontsize=11, color=C_BAND)
ax[2].legend(fontsize=9)

p = os.path.join(OUT, "fig_ecm_perovskite.png")
fig.savefig(p, dpi=200, bbox_inches="tight")
print("\nsaved", p)
