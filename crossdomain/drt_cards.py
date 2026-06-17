"""
Separate poster-style DRT cards: battery (CA7 mid-life) and perovskite
(dark dev @358 K, full 10 mHz sweep, mid series) — to sit side by side with
the Nyquist and ECM cards; the combined overlap figure (poster_2) follows.

Both cards share the SAME tau axis (3e-9 .. 3e2 s, matching poster_2) so the
peak alignment is visible even before the combined plot. Same Tikhonov-NNLS
DRT and regularisation as poster_2 (LAMBDA_REG = 0.5).

Run (repo root, venv): python -X utf8 crossdomain/drt_cards.py
Output: crossdomain/output/poster/drt_{battery,perovskite}_card.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
sys.path.insert(0, r"crossdomain")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell
from poster_style import RC, PAL

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)
C_BAT, C_PER = PAL["bat"], PAL["per"]
XLIM = (3e-9, 3e2)

plt.rcParams.update(RC)


def card(tau, gamma, color, peak_labels, name, tau_min_data=None, notes=()):
    g = gamma / gamma.max()
    if tau_min_data is not None:        # drop the grid decade below the data
        m = tau >= tau_min_data
        tau, g = tau[m], g[m]
    fig, ax = plt.subplots(figsize=(7.4, 5.0), constrained_layout=True)
    ax.plot(tau, g, color=color, lw=2.5)
    ax.fill_between(tau, g, color=color, alpha=0.18)
    for x, y, txt in notes:
        ax.text(x, y, txt, fontsize=12.5, color="0.45", ha="center")
    for t_pk, txt, dx, dy in peak_labels:
        i = np.argmin(np.abs(tau - t_pk))
        ax.annotate(txt, xy=(tau[i], g[i]), xytext=(tau[i] * dx, g[i] + dy),
                    fontsize=14.5, fontweight="bold", color=color, ha="center",
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.8))
    ax.set_xscale("log")
    ax.set_xlim(*XLIM)
    ax.set_ylim(0, 1.32)
    ax.set_xlabel(r"Relaxation time  $\tau$  /  s")
    ax.set_ylabel(r"DRT  $\gamma(\tau)$  (normalized)")
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {OUT}\\{name}.png/.pdf")


# ── battery: CA7 mid-life ─────────────────────────────────────────────────────
drt.LAMBDA_REG = 0.5
eis, cap, cyc, soh = load_cell("CA7")
mid = eis.shape[0] // 2
tb, gb, _ = compute_drt(NATIVE_FREQS, eis[mid, :33], eis[mid, 33:])
tpk_b = tb[np.argmax(gb)]
print(f"battery tau_peak = {tpk_b:.3f} s")
card(tb, gb, C_BAT,
     [(tpk_b, f"charge transfer\nτ = {tpk_b:.2f} s", 1.0, 0.13),
      (8e-4, "SEI region\n(ms)", 0.6, 0.30)],
     "drt_battery_card",
     tau_min_data=1 / (2 * np.pi * NATIVE_FREQS.max()))

# ── perovskite: dark dev @358 K, full 10 mHz sweep, mid series ────────────────
drt.FREQ_MIN = 0.005                  # keep the 10 mHz points (default 0.1 Hz)
d = np.load(r"crossdomain\data\perovskite\pero_d358_full.npz")
midp = d["Re"].shape[1] // 2
tp, gp, _ = compute_drt(d["freqs"], d["Re"][:, midp], -d["Im"][:, midp])
drt.FREQ_MIN = 0.1; drt.LAMBDA_REG = 0.01      # restore defaults
tpk_p = tp[np.argmax(gp)]
# electronic peak = max gamma below 1 ms
m_hf = tp < 1e-3
tpk_e = tp[m_hf][np.argmax(gp[m_hf])]
print(f"perovskite tau_peak (ionic) = {tpk_p:.2f} s | electronic = {tpk_e:.1e} s")
card(tp, gp, C_PER,
     [(tpk_p, f"ion migration\nτ = {tpk_p:.1f} s", 1.0, 0.13)],
     "drt_perovskite_card",
     tau_min_data=1 / (2 * np.pi * np.nanmax(d["freqs"])),
     notes=[(3e-6, 0.10, "electronic response (µs)\n~10³× smaller — off scale")])

# ── combined card, same visual language as the singles ────────────────────────
C_BAND = "#C79100"
CT_LO, CT_HI = 0.05, 2.0

mb = tb >= 1 / (2 * np.pi * NATIVE_FREQS.max())
mp = tp >= 1 / (2 * np.pi * np.nanmax(d["freqs"]))

fig, ax = plt.subplots(figsize=(7.4, 5.0), constrained_layout=True)
ax.axvspan(CT_LO, CT_HI, color=C_BAND, alpha=0.18, zorder=0)
ax.text(np.sqrt(CT_LO * CT_HI), 1.21, "shared band\n50 ms – 2 s",
        ha="center", fontsize=14.5, color=C_BAND, fontweight="bold")

ax.plot(tb[mb], gb[mb] / gb.max(), color=C_BAT, lw=2.5)
ax.fill_between(tb[mb], gb[mb] / gb.max(), color=C_BAT, alpha=0.18)
ax.plot(tp[mp], gp[mp] / gp.max(), color=C_PER, lw=2.5)
ax.fill_between(tp[mp], gp[mp] / gp.max(), color=C_PER, alpha=0.18)

ax.annotate(f"battery\nτ = {tpk_b:.2f} s", xy=(tpk_b, 1.0),
            xytext=(tpk_b / 60, 0.97), fontsize=14.5, fontweight="bold",
            color=C_BAT, ha="center",
            arrowprops=dict(arrowstyle="->", color=C_BAT, lw=1.8))
ax.annotate(f"perovskite\nτ = {tpk_p:.1f} s", xy=(tpk_p, 1.0),
            xytext=(tpk_p * 50, 0.97), fontsize=14.5, fontweight="bold",
            color=C_PER, ha="center",
            arrowprops=dict(arrowstyle="->", color=C_PER, lw=1.8))

ax.set_xscale("log")
ax.set_xlim(*XLIM)
ax.set_ylim(0, 1.32)
ax.set_xlabel(r"Relaxation time  $\tau$  /  s")
ax.set_ylabel(r"DRT  $\gamma(\tau)$  (normalized)")
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"drt_combined_card.{ext}"), dpi=300,
                bbox_inches="tight")
plt.close(fig)
print(f"saved {OUT}\\drt_combined_card.png/.pdf")
