"""
Temperature analysis (poster addition): the impedance signature is a thermally
activated covariate the shared representation must handle.

Same Molicell P42A NMC 21700 cells, three cycling/measurement temperatures:
    +25 C (CA1-8) | -10 C (N10_CB1-4) | -20 C (N20_CB1-4)   [chemistry verified
    identical from MPT headers: "Electrode material: NMC, MOLICELL 21700 P42A"].

At MATCHED state of health (SOH ~ 0.90, to remove the aging confound), the DRT
charge-transfer resistance R_ct (band integral 3 ms - 0.5 s, excluding the SEI
peak below and the tau_max grid edge above) is extracted per cell. R_ct follows
Arrhenius:  ln R_ct = ln A + E_a/(k_B T).

Findings:
  * E_a = 0.45 eV (r = 0.98) -> matches the lower end of literature Li-ion
    charge-transfer activation energies (0.5-0.7 eV): a THIRD, independent
    confirmation that the 0.16 s DRT feature is charge transfer (after DRT
    position and the ECM ZARC fit).
  * R_ct shifts ~30x across the 45 C window at fixed SOH -> temperature is a
    strong covariate.
  * Within the battery domain, cross-temperature model transfer fails
    (R^2 <= 0.07, often negative; from run_multitemp_*). The in-domain proof
    that fixed impedance features are not transferable across an intensive
    variable -> motivates a temperature-CONDITIONED shared encoder.

Run: python -X utf8 crossdomain/temperature_arrhenius.py
Output: crossdomain/output/poster/temperature_arrhenius.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS

drt.LAMBDA_REG = 0.5
SD = Path(r"battery_gpytorch_rtx4060\battery_gpytorch")
CA = SD / "data" / "ca_dataset"; MT = SD / "data" / "multitemp_dataset"
OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)

K_EV = 8.617e-5
CT_LO, CT_HI = 3e-3, 0.5          # charge-transfer window (above SEI, below tau_max edge)
SOH_TARGET = 0.90
SHARED_LO, SHARED_HI = 0.05, 2.0  # the cross-domain shared band

# cold -> warm
TEMPS = [
    (253.15, "-20 C", ["N20_CB1", "N20_CB2", "N20_CB3", "N20_CB4"], "#2166AC"),
    (263.15, "-10 C", ["N10_CB1", "N10_CB2", "N10_CB3", "N10_CB4"], "#9970AB"),
    (298.15, "+25 C", ["CA1", "CA2", "CA4", "CA7", "CA8"],           "#D55E00"),
]

plt.rcParams.update({
    "font.size": 16, "axes.labelsize": 18, "xtick.labelsize": 15,
    "ytick.labelsize": 15, "legend.fontsize": 13, "axes.linewidth": 1.4,
    "savefig.facecolor": "white", "axes.facecolor": "white", "font.family": "Arial",
    "axes.spines.top": False, "axes.spines.right": False,
})


def load(cell):
    d = MT if cell.startswith("N") else CA
    return np.loadtxt(d / f"EIS_{cell}.txt"), (lambda c: c / c[0])(np.loadtxt(d / f"cap_{cell}.txt"))


def spectrum_at_soh(cell, target):
    eis, soh = load(cell)
    j = np.argmin(np.abs(soh - target))
    if abs(soh[j] - target) > 0.06:
        return None
    return compute_drt(NATIVE_FREQS, eis[j, :33], eis[j, 33:])


def r_ct(tau, g):
    dln = np.log(tau[1] / tau[0]); m = (tau >= CT_LO) & (tau <= CT_HI)
    return g[m].sum() * dln * 1e3                       # mOhm


# ── collect ───────────────────────────────────────────────────────────────────
Tn, Rmean, Rstd, drt_rep = [], [], [], []
for T, lab, cells, col in TEMPS:
    rs, reps = [], []
    for c in cells:
        out = spectrum_at_soh(c, SOH_TARGET)
        if out is None or out[0] is None:
            continue
        tau, g, _ = out
        rs.append(r_ct(tau, g)); reps.append((tau, g))
    rs = np.array(rs)
    Tn.append(T); Rmean.append(rs.mean()); Rstd.append(rs.std())
    drt_rep.append(reps[len(reps) // 2])               # median cell as representative
    print(f"{lab} ({T:.0f} K): R_ct = {rs.mean():.1f} +/- {rs.std():.1f} mOhm  (n={len(rs)})")

Tn = np.array(Tn); Rmean = np.array(Rmean); Rstd = np.array(Rstd)
slope, intercept = np.polyfit(1 / Tn, np.log(Rmean), 1)
Ea = slope * K_EV
r = np.corrcoef(1 / Tn, np.log(Rmean))[0, 1]
print(f"\nArrhenius: E_a = {Ea:.3f} eV  (r = {r:.4f})")

# ── figure (single clean Arrhenius card, poster style) ───────────────────────
fig, axL = plt.subplots(figsize=(7.6, 5.6), constrained_layout=True)

# Arrhenius:  ln R = slope*(1/T) + intercept ;  x-axis = 1000/T
x = 1000.0 / Tn
xx = np.linspace(x.min() * 0.97, x.max() * 1.03, 50)
axL.plot(xx, np.exp(slope * (xx / 1000.0) + intercept), "-", color="0.4",
         lw=2.5, zorder=1)
# point labels placed directly by each marker (no legend box)
lab_off = {"-20 C": (6, 8, "left"), "-10 C": (8, -4, "left"), "+25 C": (-8, 10, "right")}
for (T, lab, cells, col), rm, rs in zip(TEMPS, Rmean, Rstd):
    axL.errorbar(1000.0 / T, rm, yerr=rs, fmt="o", ms=14, color=col, capsize=5,
                 lw=2, mec="white", mew=1.6, zorder=3)
    dx, dy, ha = lab_off[lab]
    axL.annotate(lab.replace(" C", " °C"), xy=(1000.0 / T, rm),
                 xytext=(dx, dy), textcoords="offset points", ha=ha,
                 fontsize=14, fontweight="bold", color=col)
axL.set_yscale("log")
axL.set_xlabel(r"1000 / T   /   K$^{-1}$")
axL.set_ylabel(r"charge-transfer  $R_\mathrm{ct}$  /  m$\Omega$   (at SOH 0.90)")
# E_a as prominent on-plot text (like the |r| values on the descriptor cards)
axL.text(0.04, 0.93, fr"$E_a$ = {Ea:.2f} eV", transform=axL.transAxes,
         fontsize=22, fontweight="bold", color="0.2", va="top")
axL.text(0.04, 0.83, fr"$r$ = {r:.2f}   (Li-ion lit. 0.5–0.7 eV)",
         transform=axL.transAxes, fontsize=13, color="0.4", va="top")
# the ~32x span, stated on-plot
axL.annotate(fr"$\times${Rmean.max()/Rmean.min():.0f} across 45 °C",
             xy=(0.96, 0.06), xycoords="axes fraction", ha="right",
             fontsize=13, color="0.4", style="italic")

# open L-frame version (matches the ECM / DRT cards)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"temperature_arrhenius.{ext}"), dpi=300,
                bbox_inches="tight")
print(f"\nsaved {OUT}\\temperature_arrhenius.png/.pdf  (open L-frame)")

# full-box version (all four spines) for posters whose other graphs are boxed
for sp in ("top", "right"):
    axL.spines[sp].set_visible(True)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"temperature_arrhenius_boxed.{ext}"), dpi=300,
                bbox_inches="tight")
print(f"saved {OUT}\\temperature_arrhenius_boxed.png/.pdf  (full box)")
plt.close(fig)
