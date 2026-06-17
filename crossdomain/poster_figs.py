"""
Poster-grade figures for AI4X Accelerate 2026 (Singapore).

Three standalone panels (300 dpi PNG + vector PDF each), sized for poster columns,
built from the v2 dataset (DataForHitesh):

  poster_1_nyquist  : Nyquist degradation hook — battery vs perovskite (light dev),
                      same growing interfacial arc, ~4 decades apart in |Z|.
  poster_2_drt      : the headline — DRT tau overlap. Battery CT arc and perovskite
                      LF ionic feature in the same ms-s band; v1 truncated sweep shown
                      to mark what a 10 Hz cutoff misses.
  poster_3_descriptor: descriptor -> MEASURED performance, both domains (r ~ -0.9).

Run (repo root, venv): python -X utf8 crossdomain/poster_figs.py
"""
import sys, os
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
sys.path.insert(0, r"crossdomain")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell, BANDS
from poster_style import RC

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)
BCELLS = ["CA1", "CA2", "CA4", "CA7", "CA8"]
NYQ_CELL = "CA7"
CT_LO, CT_HI = BANDS[1][1], BANDS[1][2]

# two-domain palette matched to the hero Nyquist cards / AI4X theme
# (battery = warm coral family, perovskite = violet family, band = gold)
C_BAT = "#D55E00"   # battery — mid of the dark-maroon -> coral #FD8963 ramp
C_PER = "#7C4DCB"   # perovskite — AI4X primary purple (ramp #170A2C -> #BFA8FF)
C_BAND = "#C79100"  # shared tau band — dark gold (fill of AI4X yellow #FDCE39)

from matplotlib.colors import LinearSegmentedColormap
CM_PER = LinearSegmentedColormap.from_list(
    "per", ["#170A2C", "#4E32A0", "#7C4DCB", "#BFA8FF"])

plt.rcParams.update(RC)


def save(fig, name):
    saved = []
    for ext in ("png", "pdf"):
        p = os.path.join(OUT, f"{name}.{ext}")
        try:
            fig.savefig(p, dpi=300, bbox_inches="tight")
        except PermissionError:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            p = os.path.join(OUT, f"{name}_{stamp}.{ext}")
            fig.savefig(p, dpi=300, bbox_inches="tight")
            print(f"warning: output was locked; saved {p} instead")
        saved.append(p)
    plt.close(fig)
    print("saved", ", ".join(saved))


def panel_letter(ax, letter):
    ax.text(-0.13, 1.06, letter, transform=ax.transAxes,
            fontsize=24, fontweight="bold", va="top")


def load_battery():
    out = {}
    for c in BCELLS:
        eis, cap, cyc, soh = load_cell(c)
        Re, Im = eis[:, :33], eis[:, 33:]
        out[c] = dict(Re=Re, Im=Im, cyc=cyc, soh=soh, Rp=Re[:, -1] - Re[:, 0])
    return out


def load_pero(key):
    d = np.load(rf"crossdomain\data\perovskite\pero_{key}.npz")
    return {k: d[k] for k in d.files}


bat = load_battery()
fast = load_pero("l358_fast")
dark = load_pero("d358_full")

# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 1 — Nyquist hook
fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.6), constrained_layout=True)

b = bat[NYQ_CELL]; n = b["Re"].shape[0]
cm = plt.cm.viridis(np.linspace(0, 1, n))
for i in range(n):
    ax[0].plot(b["Re"][i] * 1e3, -b["Im"][i] * 1e3, color=cm[i], lw=1.3, alpha=0.8)
ax[0].set_xlabel(r"Re$(Z)$  /  m$\Omega$")
ax[0].set_ylabel(r"$-$Im$(Z)$  /  m$\Omega$")
ax[0].set_title("Li-ion battery (NMC, to EOL)\n10 kHz – 1 Hz", pad=10)
# viridis_r + ascending norm so the colorbar reads top = SOH 1.0 = dark,
# matching the curves (reversed Normalize renders the colorbar wrong)
sm = plt.cm.ScalarMappable(cmap="viridis_r", norm=plt.Normalize(b["soh"].min(), 1.0))
cb = fig.colorbar(sm, ax=ax[0], fraction=0.05, pad=0.02)
cb.set_label("State of Health", fontsize=14)
panel_letter(ax[0], "a")

Re, Im, th = fast["Re"], fast["Im"], fast["t_hours"]; ns = Re.shape[1]
cm = plt.cm.viridis(np.linspace(0, 1, ns))
for k in range(ns):
    ax[1].plot(Re[:, k], -Im[:, k], color=cm[k], lw=1.3, alpha=0.8)
ax[1].set_xlabel(r"Re$(Z)$  /  $\Omega$")
ax[1].set_ylabel(r"$-$Im$(Z)$  /  $\Omega$")
ax[1].set_title("Perovskite solar cell (1 sun, 358 K)\n10 MHz – 10 Hz", pad=10)
sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(0, th[-1]))
cb = fig.colorbar(sm, ax=ax[1], fraction=0.05, pad=0.02)
cb.set_label("Aging time / h", fontsize=14)
panel_letter(ax[1], "b")

fig.suptitle(r"Same measurement, same degradation signature — $10^4\times$ apart in impedance",
             fontsize=18, fontweight="bold")
save(fig, "poster_1_nyquist")

# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 2 — DRT tau overlap (headline)
drt.LAMBDA_REG = 0.5
b = bat[NYQ_CELL]; mid = b["Re"].shape[0] // 2
tb, gb, _ = compute_drt(NATIVE_FREQS, b["Re"][mid], b["Im"][mid])
tpk_b = tb[np.argmax(gb)]

drt.FREQ_MIN = 0.005
midp = dark["Re"].shape[1] // 2
tp, gp, _ = compute_drt(dark["freqs"], dark["Re"][:, midp], -dark["Im"][:, midp])
tpk_p = tp[np.argmax(gp)]
drt.FREQ_MIN = 0.1
midf = fast["Re"].shape[1] // 2
tf, gf, _ = compute_drt(fast["freqs"], fast["Re"][:, midf], -fast["Im"][:, midf])
tpk_f = tf[np.argmax(gf)]
drt.LAMBDA_REG = 0.01; drt.FREQ_MIN = 0.1

fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
ax.axvspan(CT_LO, CT_HI, color=C_BAND, alpha=0.18, zorder=0)
ax.text(np.sqrt(CT_LO * CT_HI), 1.30, "shared band\n50 ms – 2 s",
        ha="center", fontsize=15, color=C_BAND, fontweight="bold")

ax.plot(tb, gb / gb.max(), color=C_BAT,
        label=fr"Battery charge transfer   $\tau_\mathrm{{peak}}$ = {tpk_b:.2f} s")
ax.fill_between(tb, gb / gb.max(), color=C_BAT, alpha=0.15)
ax.plot(tp, gp / gp.max(), color=C_PER,
        label=fr"Perovskite ionic (10 mHz sweep)   $\tau_\mathrm{{peak}}$ = {tpk_p:.2f} s")
ax.fill_between(tp, gp / gp.max(), color=C_PER, alpha=0.15)
ax.plot(tf, gf / gf.max(), color=C_PER, ls=":", lw=2.0, alpha=0.85,
        label=fr"Perovskite, 10 Hz cutoff   $\tau_\mathrm{{peak}}$ = 7 µs (electronic only)")

ax.annotate("missed below\nsweep cutoff", xy=(tpk_f * 1.6, 0.92), xytext=(2.5e-7, 0.72),
            fontsize=13, color="gray", ha="center",
            arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))
ax.set_xscale("log")
ax.set_xlim(3e-9, 3e2)
ax.set_ylim(0, 1.45)
ax.set_xlabel(r"Relaxation time  $\tau$  /  s")
ax.set_ylabel(r"DRT  $\gamma(\tau)$  (normalized)")
ax.set_title("One DRT formalism — dominant relaxations overlap in the same ms–s band",
             fontsize=17, fontweight="bold", pad=12)
ax.legend(loc="upper left", framealpha=0.95)
save(fig, "poster_2_drt_overlap")

# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 3 — descriptor -> measured performance
fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.6), constrained_layout=True)

Rp_all = np.concatenate([bat[c]["Rp"] for c in BCELLS])
soh_all = np.concatenate([bat[c]["soh"] for c in BCELLS])
r_b, _ = pearsonr(Rp_all, soh_all)
for c in BCELLS:
    ax[0].scatter(bat[c]["Rp"] * 1e3, bat[c]["soh"], s=22, alpha=0.65,
                  color=C_BAT, edgecolors="none")
ax[0].set_xlabel(r"Arc descriptor  $R_p$  /  m$\Omega$")
ax[0].set_ylabel("State of Health")
ax[0].set_title("Battery: resistance rises as capacity falls\n(5 cells pooled)", pad=10)
ax[0].text(0.95, 0.92, fr"$|r| = {abs(r_b):.2f}$", transform=ax[0].transAxes,
           fontsize=20, fontweight="bold", ha="right", color=C_BAT)
panel_letter(ax[0], "a")

Rp_p, pm, th = fast["rp"], fast["pmax"], fast["t_hours"]
ret = pm / pm[0]
r_p, _ = pearsonr(Rp_p, ret)
sc = ax[1].scatter(Rp_p, ret, s=42, c=th, cmap=CM_PER, edgecolors="none")
cb = fig.colorbar(sc, ax=ax[1], fraction=0.05, pad=0.02)
cb.set_label("Aging time / h", fontsize=14)
ax[1].set_xlabel(r"Arc descriptor  $R_p$  /  $\Omega$")
ax[1].set_ylabel(r"$P_\mathrm{max}$ retention")
ax[1].set_title("Perovskite: resistance rises as power falls\n(light JV @ 100% intensity)", pad=10)
ax[1].text(0.95, 0.92, fr"$|r| = {abs(r_p):.2f}$", transform=ax[1].transAxes,
           fontsize=20, fontweight="bold", ha="right", color=C_PER)
panel_letter(ax[1], "b")

fig.suptitle("The same impedance descriptor predicts measured degradation in both domains",
             fontsize=18, fontweight="bold")
save(fig, "poster_3_descriptor")

# ── standalone single-panel versions (for free placement in the PPT poster) ──
fig, ax = plt.subplots(figsize=(7.0, 5.6), constrained_layout=True)
for c in BCELLS:
    ax.scatter(bat[c]["Rp"] * 1e3, bat[c]["soh"], s=22, alpha=0.65,
               color=C_BAT, edgecolors="none")
ax.set_xlabel(r"Arc descriptor  $R_p$  /  m$\Omega$")
ax.set_ylabel("State of Health")
ax.set_title("Battery: resistance rises as capacity falls\n(5 cells pooled)", pad=10)
ax.text(0.95, 0.92, fr"$|r| = {abs(r_b):.2f}$", transform=ax.transAxes,
        fontsize=20, fontweight="bold", ha="right", color=C_BAT)
save(fig, "poster_3a_battery_descriptor")

fig, ax = plt.subplots(figsize=(7.8, 5.6), constrained_layout=True)
sc = ax.scatter(Rp_p, ret, s=42, c=th, cmap=CM_PER, edgecolors="none")
cb = fig.colorbar(sc, ax=ax, fraction=0.05, pad=0.02)
cb.set_label("Aging time / h", fontsize=14)
ax.set_xlabel(r"Arc descriptor  $R_p$  /  $\Omega$")
ax.set_ylabel(r"$P_\mathrm{max}$ retention")
ax.set_title("Perovskite: resistance rises as power falls\n(light JV @ 100% intensity)", pad=10)
ax.text(0.95, 0.92, fr"$|r| = {abs(r_p):.2f}$", transform=ax.transAxes,
        fontsize=20, fontweight="bold", ha="right", color=C_PER)
save(fig, "poster_3b_perovskite_descriptor")

print(f"\nbattery r = {r_b:.3f} | perovskite r = {r_p:.3f}")
print("Done. Poster figures in", OUT)
