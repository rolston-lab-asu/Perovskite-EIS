"""
Separate poster-style ECM cards with a drawn equivalent-circuit schematic:
battery (CA7 mid-life) and perovskite (light dev @358 K mid-life).

Circuit (same topology both devices):
    R_s  --  (R1 || CPE1)  --  (R2 || CPE2)
The degradation-tracking arc (R2 = charge transfer / recombination) is
highlighted in the domain color. Legend sits between schematic and plot,
not on the data. No literal "Battery:/Perovskite:" titles — the schematic
and legend carry the content.

Run (repo root, venv): python -X utf8 crossdomain/ecm_cards.py
Output: crossdomain/output/poster/ecm_{battery,perovskite}_card.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.optimize import least_squares

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
sys.path.insert(0, r"crossdomain")
from run_drt_molicell import NATIVE_FREQS, load_cell
from poster_style import RC, PAL

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)
C_BAT, C_PER = PAL["bat"], PAL["per"]
C_WIRE = PAL["wire"]

plt.rcParams.update(RC)


def z_model(p, w):
    Rs, R1, t1, a1, R2, t2, a2 = p
    return (Rs + R1 / (1 + (1j * w * t1) ** a1)
               + R2 / (1 + (1j * w * t2) ** a2))


def fit_ecm(freq, Z, p0):
    ok = np.isfinite(freq) & np.isfinite(Z)
    freq, Z = freq[ok], Z[ok]
    w = 2 * np.pi * freq

    def resid(p):
        Zf = z_model(p, w)
        return np.concatenate([(Zf.real - Z.real) / np.abs(Z),
                               (Zf.imag - Z.imag) / np.abs(Z)])

    lb = [0] + [1e-12, 1e-9, 0.5] * 2
    ub = [np.inf] + [np.inf, 1e3, 1.0] * 2
    sol = least_squares(resid, np.clip(p0, lb, ub), bounds=(lb, ub), max_nfev=40000)
    rms = 100 * np.sqrt(np.mean(sol.fun ** 2))
    return sol.x, rms, freq, Z


# ── circuit schematic ─────────────────────────────────────────────────────────
def draw_circuit(ax, hi_color, hi_block):
    """R_s -- (R1||CPE1) -- (R2||CPE2); block `hi_block` (1 or 2) highlighted
    in the domain color = the degradation-tracking element."""
    ax.set_xlim(0, 100); ax.set_ylim(0, 36); ax.axis("off")
    y, dy = 18, 8
    lw = 2.0

    def wire(x0, x1, yy=y):
        ax.plot([x0, x1], [yy, yy], color=C_WIRE, lw=lw, solid_capstyle="round")

    def resistor(xc, yy, label, color=C_WIRE, above=True):
        wbox, hbox = 10, 6
        ax.add_patch(Rectangle((xc - wbox / 2, yy - hbox / 2), wbox, hbox,
                               fc="white", ec=color, lw=2.2, zorder=3))
        ax.text(xc, yy + (hbox / 2 + 4.5) * (1 if above else -1), label,
                ha="center", va="center", fontsize=13.5, color=color,
                fontweight="bold" if color != C_WIRE else "normal")

    def cpe(xc, yy, label, color=C_WIRE):
        for off in (-1.8, 1.8):
            ax.plot([xc + off - 2, xc + off + 2], [yy - 3, yy + 3],
                    color=color, lw=2.2, zorder=3)
        wire(xc - 6, xc - 3.8, yy); wire(xc + 3.8, xc + 6, yy)
        ax.text(xc, yy - 8.2, label, ha="center", va="center",
                fontsize=13.5, color=color,
                fontweight="bold" if color != C_WIRE else "normal")

    def parallel_block(x0, x1, rlab, clab, color):
        xc = (x0 + x1) / 2
        ax.plot([x0, x0], [y - dy, y + dy], color=C_WIRE, lw=lw)
        ax.plot([x1, x1], [y - dy, y + dy], color=C_WIRE, lw=lw)
        wire(x0, xc - 5, y + dy); wire(xc + 5, x1, y + dy)
        resistor(xc, y + dy, rlab, color)
        wire(x0, xc - 6, y - dy); wire(xc + 6, x1, y - dy)
        cpe(xc, y - dy, clab, color)

    wire(2, 12)
    resistor(17, y, r"$R_s$"); wire(12, 12)
    wire(22, 30)
    parallel_block(30, 56, r"$R_1$", r"$CPE_1$",
                   hi_color if hi_block == 1 else C_WIRE)
    wire(56, 64)
    parallel_block(64, 90, r"$R_2$", r"$CPE_2$",
                   hi_color if hi_block == 2 else C_WIRE)
    wire(90, 98)


def make_card(freq, Z, p, scale, unit, color, dark, meas_label, fit_label, name,
              hi_block):
    fig = plt.figure(figsize=(7.6, 6.8), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 3.4])
    axc = fig.add_subplot(gs[0]); ax = fig.add_subplot(gs[1])

    draw_circuit(axc, color, hi_block)

    wf = 2 * np.pi * np.logspace(np.log10(freq.min()), np.log10(freq.max()), 400)
    Zfit = z_model(p, wf)
    ax.plot(Z.real * scale, -Z.imag * scale, "o", ms=6, color=color, label=meas_label)
    ax.plot(Zfit.real * scale, -Zfit.imag * scale, "-", lw=2.5, color=dark,
            alpha=0.85, label=fit_label)
    ax.axhline(0, color="0.6", lw=0.8, ls="--")
    ax.set_xlabel(fr"Re$(Z)$  /  {unit}")
    ax.set_ylabel(fr"$-$Im$(Z)$  /  {unit}")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False,
              borderaxespad=0.1)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {OUT}\\{name}.png/.pdf")


# ── battery ───────────────────────────────────────────────────────────────────
eis, cap, cyc, soh = load_cell("CA7")
mid = eis.shape[0] // 2
Zb = eis[mid, :33] - 1j * eis[mid, 33:]            # stored col 33+ is -Im(Z)
p0 = np.array([0.027, 0.009, 1e-3, 0.95, 0.065, 0.15, 0.75])
pb, rms_b, fb, Zb = fit_ecm(NATIVE_FREQS, Zb, p0)
print(f"BATTERY CA7 mid: rms={rms_b:.1f}%  Rs={pb[0]*1e3:.1f} mOhm | "
      f"R1={pb[1]*1e3:.1f} mOhm t1={pb[2]*1e3:.2f} ms | "
      f"R2={pb[4]*1e3:.1f} mOhm t2={pb[5]:.3f} s (a={pb[6]:.2f})")
make_card(fb, Zb, pb, 1e3, r"m$\Omega$", C_BAT, "#2B0A02",
          "Measured (Li-ion cell, mid-life)",
          fr"Fit:  $R_2$ = {pb[4]*1e3:.0f} m$\Omega$ (charge transfer),  "
          fr"$\tau_2$ = {pb[5]:.2f} s",
          "ecm_battery_card", hi_block=2)

# ── perovskite ────────────────────────────────────────────────────────────────
d = np.load(r"crossdomain\data\perovskite\pero_l358_fast.npz")
k = d["Re"].shape[1] // 2
Zp = d["Re"][:, k] + 1j * d["Im"][:, k]
p0 = np.array([25.0, 400.0, 7e-6, 0.9, 180.0, 1e-3, 0.8])
pp, rms_p, fp, Zp = fit_ecm(d["freqs"], Zp, p0)
print(f"PEROVSKITE light mid: rms={rms_p:.1f}%  Rs={pp[0]:.0f} Ohm | "
      f"R1={pp[1]:.0f} Ohm t1={pp[2]:.1e} s (a={pp[3]:.2f}) | "
      f"R2={pp[4]:.0f} Ohm t2={pp[5]:.1e} s")
# NB: for the perovskite the HF arc (R1) is the recombination feature
make_card(fp, Zp, pp, 1.0, r"$\Omega$", C_PER, "#170A2C",
          "Measured (perovskite cell @358 K, mid-life)",
          fr"Fit:  $R_1$ = {pp[1]:.0f} $\Omega$ (recombination),  "
          fr"$\tau_1$ = {pp[2]*1e6:.0f} µs",
          "ecm_perovskite_card", hi_block=1)

# ── standalone circuit-only figure (domain-neutral, one image for both) ───────
fig, axc = plt.subplots(figsize=(9.0, 2.8), constrained_layout=True)
draw_circuit(axc, C_WIRE, hi_block=0)        # no highlight — shared circuit
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"ecm_circuit.{ext}"), dpi=300,
                bbox_inches="tight")
plt.close(fig)
print(f"saved {OUT}\\ecm_circuit.png/.pdf")
