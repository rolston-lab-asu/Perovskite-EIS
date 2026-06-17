"""
Workflow box 2 — "How DRT is extracted from EIS" schematic card.

Nick's review of poster v17: the poster jumps straight to DRT peaks without
showing where they come from. This card makes the inversion step explicit for a
non-ECS audience: one measured spectrum (Nyquist)  --DRT-->  its gamma(tau)
distribution, with a single plain-language caption.

Uses one battery spectrum (CA7 mid-life) as the representative example; the
method is identical for the perovskite spectra. Same Tikhonov-NNLS DRT as the
other cards.

Run (repo root, venv): python -X utf8 crossdomain/drt_extraction_card.py
Output: crossdomain/output/poster/drt_extraction_card.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
sys.path.insert(0, r"crossdomain")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell
from poster_style import RC, PAL

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)
C_BAT, C_BAND, C_INK = PAL["bat"], PAL["band"], PAL["ink"]

plt.rcParams.update(RC)

# one representative measured spectrum: CA7 mid-life
drt.LAMBDA_REG = 0.5
eis, cap, cyc, soh = load_cell("CA7")
mid = eis.shape[0] // 2
Re, Im = eis[mid, :33], eis[mid, 33:]
tau, gamma, _ = compute_drt(NATIVE_FREQS, Re, Im)
tau_min = 1 / (2 * np.pi * NATIVE_FREQS.max())
m = tau >= tau_min
tau, gamma = tau[m], gamma[m] / gamma[m].max()
tpk = tau[np.argmax(gamma)]

fig = plt.figure(figsize=(12.6, 5.2))
# left: measured Nyquist
axL = fig.add_axes([0.065, 0.20, 0.34, 0.66])
axL.plot(Re * 1e3, -Im * 1e3, "o-", ms=5, lw=2.0, color=C_BAT)
axL.set_xlabel(r"Re$(Z)$  /  m$\Omega$")
axL.set_ylabel(r"$-$Im$(Z)$  /  m$\Omega$")
axL.set_title("1.  MEASURED SPECTRUM\nimpedance at each frequency",
              fontsize=15, fontweight="bold", color=C_INK, pad=8)

# right: extracted DRT
axR = fig.add_axes([0.635, 0.20, 0.34, 0.66])
axR.plot(tau, gamma, color=C_BAT, lw=2.5)
axR.fill_between(tau, gamma, color=C_BAT, alpha=0.18)
axR.set_xscale("log")
axR.set_xlim(tau_min, 3e2)
axR.set_ylim(0, 1.25)
axR.annotate(f"one interfacial\nprocess\n$\\tau$ = {tpk:.2f} s",
             xy=(tpk, 1.0), xytext=(tpk / 120, 0.92),
             fontsize=13.5, fontweight="bold", color=C_BAT, ha="center",
             arrowprops=dict(arrowstyle="->", color=C_BAT, lw=1.8))
axR.set_xlabel(r"Relaxation time  $\tau$  /  s")
axR.set_ylabel(r"DRT  $\gamma(\tau)$  (norm.)")
axR.set_title("2.  DISTRIBUTION OF\nRELAXATION TIMES",
              fontsize=15, fontweight="bold", color=C_INK, pad=8)

# arrow + method label between the two panels
arr = FancyArrowPatch((0.435, 0.52), (0.60, 0.52), transform=fig.transFigure,
                      arrowstyle="-|>", mutation_scale=34, lw=3.0, color=C_BAND)
fig.add_artist(arr)
fig.text(0.5175, 0.60, "DRT", ha="center", fontsize=20, fontweight="bold",
         color=C_BAND)
fig.text(0.5175, 0.40, "regularized\ninversion", ha="center", fontsize=12,
         color="0.35")

# one-line plain-language caption
fig.text(0.5, 0.045,
         "A Tikhonov-regularized inversion turns the frequency spectrum into a "
         "distribution of relaxation times $\\tau$ — each peak = one physical "
         "process, model-free.",
         ha="center", fontsize=13.5, color=C_INK, style="italic")

for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"drt_extraction_card.{ext}"), dpi=300,
                bbox_inches="tight")
plt.close(fig)
print(f"saved {OUT}\\drt_extraction_card.png/.pdf  (tau_peak = {tpk:.3f} s)")
