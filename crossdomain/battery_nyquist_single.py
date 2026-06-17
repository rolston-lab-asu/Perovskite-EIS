"""
Hero Nyquist cards (top tier of the AI4X poster) — separate battery and
perovskite plots, wide format to sit side by side as the top row.

Distinct domain colormaps, both dark = fresh -> bright = aged:
  battery_nyquist_card    : CA7 to EOL, warm ramp (dark maroon -> coral #FD8963)
  perovskite_nyquist_card : light dev @358 K fast series, violet ramp
                            (dark #170A2C -> lavender #BFA8FF, AI4X palette)

Battery sign convention: EIS_CA*.txt columns 34-66 already store -Im(Z) —
plot directly (negating mirrors the arc into the 4th quadrant).

Run (repo root, venv): python -X utf8 crossdomain/battery_nyquist_single.py
Output: crossdomain/output/poster/{battery,perovskite}_nyquist_card.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
sys.path.insert(0, r"crossdomain")
from run_drt_molicell import load_cell
from poster_style import RC

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update(RC)

# domain ramps, dark (fresh) -> bright (aged); endpoints from the AI4X palette
CM_BAT = LinearSegmentedColormap.from_list(
    "bat", ["#2B0A02", "#8C2E00", "#D55E00", "#FD8963"])
CM_PER = LinearSegmentedColormap.from_list(
    "per", ["#170A2C", "#4E32A0", "#7C4DCB", "#BFA8FF"])
C_BAT_TXT, C_PER_TXT = "#8C2E00", "#4E32A0"


def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save(fig, name):
    for ext in ("png", "pdf"):
        p = os.path.join(OUT, f"{name}.{ext}")
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print("saved", p)
    plt.close(fig)


# ── battery card ──────────────────────────────────────────────────────────────
eis, cap, cyc, soh = load_cell("CA7")
Re, nIm = eis[:, :33], eis[:, 33:]          # columns 34-66 ARE -Im(Z) already
n = Re.shape[0]

fig, ax = plt.subplots(figsize=(7.4, 3.8), constrained_layout=True)
for i in range(n):
    ax.plot(Re[i] * 1e3, nIm[i] * 1e3, color=CM_BAT(i / (n - 1)), lw=1.1, alpha=0.75)
ax.axhline(0, color="0.6", lw=0.9, ls="--")
ax.set_xlabel(r"Re$(Z)$  /  m$\Omega$")
ax.set_ylabel(r"$-$Im$(Z)$  /  m$\Omega$")
style(ax)

# frequency endpoints + aging direction
ax.annotate("10 kHz", xy=(6, -18.5), fontsize=15, color="0.35", ha="left")
ax.annotate("1 Hz", xy=(141, 26), fontsize=15, color="0.35", ha="left")
ax.annotate("", xy=(112, 22), xytext=(48, 7),
            arrowprops=dict(arrowstyle="-|>", lw=3, color=C_BAT_TXT))
ax.text(78, 11.5, "aging", fontsize=18, fontweight="bold",
        color=C_BAT_TXT, rotation=14)
ax.set_xlim(0, 158)
ax.set_ylim(-20.5, 35)

sm = plt.cm.ScalarMappable(cmap=CM_BAT.reversed(),
                           norm=plt.Normalize(soh.min(), soh.max()))
cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)  # top = SOH 1.0 = dark
cb.set_label("State of health", fontsize=18)
save(fig, "battery_nyquist_card")

# ── perovskite card ───────────────────────────────────────────────────────────
d = np.load(r"crossdomain\data\perovskite\pero_l358_fast.npz")
ReP, ImP, th = d["Re"], d["Im"], d["t_hours"]
ns = ReP.shape[1]

fig, ax = plt.subplots(figsize=(7.4, 3.8), constrained_layout=True)
for k in range(ns):
    ax.plot(ReP[:, k], -ImP[:, k], color=CM_PER(th[k] / th[-1]), lw=1.1, alpha=0.85)
ax.set_xlabel(r"Re$(Z)$  /  $\Omega$")
ax.set_ylabel(r"$-$Im$(Z)$  /  $\Omega$")
style(ax)

ax.annotate("10 MHz", xy=(2, -22), fontsize=15, color="0.35", ha="left")
ax.annotate("10 Hz", xy=(660, -28), fontsize=15, color="0.35", ha="left")
ax.annotate("", xy=(540, 165), xytext=(450, 110),
            arrowprops=dict(arrowstyle="-|>", lw=3, color=C_PER_TXT))
ax.text(525, 130, "aging", fontsize=18, fontweight="bold",
        color=C_PER_TXT, rotation=27)
ax.set_ylim(-38, 228)

sm = plt.cm.ScalarMappable(cmap=CM_PER, norm=plt.Normalize(0, th[-1]))
cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
cb.set_label("Aging time / h", fontsize=18)
save(fig, "perovskite_nyquist_card")
