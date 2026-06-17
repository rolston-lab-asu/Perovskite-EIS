"""
Cross-domain figures v2 — rebuilt on DataForHitesh.zip (see README update 2026-06-11).

What changed vs crossdomain_figs.py (v1):
  * Perovskite sweeps now reach 10 mHz (85C campaign) -> the LF ionic feature is
    in-band and its DRT peak lands INSIDE the battery charge-transfer band.
    FIG B flips from "tau scale-separation" to "tau overlap" (honest framing: the
    overlapping processes differ physically -- ionic migration vs charge transfer).
  * Real light-JV labels (Pmax at 100% intensity) per aging step -> FIG C correlates
    the impedance descriptor against measured performance, not an aging index.
  * Dark-aged control device available -> FIG A shows the clean full-range series.

FIG A v2 : Nyquist degradation, battery (CA7) | perovskite light device @358 K
           (clean monotonic arc growth, JV-labeled) | perovskite dark device @358 K
           full 10 mHz sweep (the LF ionic window; noisy at MOhm scale, f>=30 mHz shown).
FIG B v2 : DRT gamma(tau) overlay -- both domains' dominant relaxation in the same
           ms-s band; inset shows the v1 truncated sweep that missed it.
           + normalized arc-growth trajectories.
FIG C v2 : descriptor -> measured label in both domains: battery Rp -> SOH,
           perovskite Rp -> Pmax retention (light device, real JV labels).
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
import run_drt_molicell as drt
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell, BANDS

OUT = r"crossdomain\output"
os.makedirs(OUT, exist_ok=True)
BCELLS = ["CA1", "CA2", "CA4", "CA7", "CA8"]
NYQ_CELL = "CA7"
B_FREQS = NATIVE_FREQS
CT_LO, CT_HI = BANDS[1][1], BANDS[1][2]        # battery charge-transfer band, 50 ms - 2 s

C_BAT, C_PER, C_PER2 = "#C0392B", "#2471A3", "#117A65"


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


# ════════════════════════════════════════════════════════════════════════════
def fig_A(bat, dark, fast):
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.2))
    fig.suptitle("FIG A  |  Same EIS measurement, two energy systems: interfacial impedance evolves with aging",
                 fontsize=12, y=1.00)

    b = bat[NYQ_CELL]; n = b["Re"].shape[0]
    cm = plt.cm.viridis(np.linspace(0, 1, n))
    for i in range(n):
        ax[0].plot(b["Re"][i] * 1e3, -b["Im"][i] * 1e3, color=cm[i], lw=0.7, alpha=0.7)
    ax[0].set_xlabel("Re(Z)  /  mOhm"); ax[0].set_ylabel("-Im(Z)  /  mOhm")
    ax[0].set_title(f"Li-ion battery ({NYQ_CELL})\n10 kHz - 1 Hz, milli-ohm scale", fontsize=10)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(b["soh"].max(), b["soh"].min()))
    cb = fig.colorbar(sm, ax=ax[0], fraction=0.045, pad=0.02); cb.set_label("SOH (1 -> 0)", fontsize=8)

    Re, Im, th = fast["Re"], fast["Im"], fast["t_hours"]; ns = Re.shape[1]
    cm = plt.cm.viridis(np.linspace(0, 1, ns))
    for k in range(ns):
        ax[1].plot(Re[:, k], -Im[:, k], color=cm[k], lw=0.7, alpha=0.7)
    ax[1].set_xlabel("Re(Z)  /  Ohm"); ax[1].set_ylabel("-Im(Z)  /  Ohm")
    ax[1].set_title("Perovskite, light-aged device @358 K\n10 MHz - 10 Hz, ohm scale "
                    "(arc +55%, Pmax -33%)", fontsize=10)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(0, th[-1]))
    cb = fig.colorbar(sm, ax=ax[1], fraction=0.045, pad=0.02)
    cb.set_label(f"aging time / h (0 -> {th[-1]:.0f})", fontsize=8)

    # dark device, full LF window: f >= 30 mHz shown (10-30 mHz points are pA-level
    # noise at tens of MOhm); last spectrum has NaNs -> dropped; spectra whose Nyquist
    # path is rough (total variation > 1.2x the monotonic minimum) dropped for display
    Re, Im, th = dark["Re"], dark["Im"], dark["t_hours"]; ns = Re.shape[1] - 1
    mask = dark["freqs"] >= 0.03
    cm = plt.cm.viridis(np.linspace(0, 1, ns))
    n_drop = 0
    for k in range(ns):
        r, i = Re[mask, k], Im[mask, k]
        # Re is monotonic along a clean arc (-Im is not), so roughness = TV(Re)/range
        tv = np.abs(np.diff(r)).sum() / np.ptp(r)
        if tv > 1.15:
            n_drop += 1
            continue
        ax[2].plot(r * 1e-6, -i * 1e-6, color=cm[k], lw=0.7, alpha=0.7)
    print(f"  fig A: dropped {n_drop}/{ns} noisy dark-device spectra from display")
    ax[2].set_xlim(0, 75); ax[2].set_ylim(-3, 38)
    ax[2].set_xlabel("Re(Z)  /  MOhm"); ax[2].set_ylabel("-Im(Z)  /  MOhm")
    ax[2].set_title("Perovskite, dark-aged device @358 K\n10 MHz - 10 mHz: LF ionic arc in-band",
                    fontsize=10)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(0, th[-1]))
    cb = fig.colorbar(sm, ax=ax[2], fraction=0.045, pad=0.02)
    cb.set_label(f"aging time / h (0 -> {th[-1]:.0f})", fontsize=8)

    fig.text(0.5, -0.02,
             "Impedance magnitudes span ~10 decades across panels, yet the same interfacial-arc structure appears in all.\n"
             "Light device: clean monotonic arc growth with measured Pmax loss. Dark device: the extended 10 mHz sweep "
             "captures the low-frequency ionic feature (dominant MOhm arc) that the truncated v1 sweep missed\n"
             "(f >= 30 mHz shown; noisiest spectra omitted from display, all retained for DRT in FIG B).",
             ha="center", fontsize=8.5, style="italic")
    plt.tight_layout()
    p = os.path.join(OUT, "fig_A_v2_nyquist_degradation.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)


# ════════════════════════════════════════════════════════════════════════════
def fig_B(bat, dark, fast):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.suptitle("FIG B  |  One DRT formalism, two domains: dominant relaxations OVERLAP in the same ms-s band",
                 fontsize=11.5, y=1.00)

    # --- panel 1: DRT gamma(tau), same Tikhonov-NNLS + regularisation for both ---
    drt.LAMBDA_REG = 0.5
    b = bat[NYQ_CELL]; mid = b["Re"].shape[0] // 2
    tb, gb, _ = compute_drt(B_FREQS, b["Re"][mid], b["Im"][mid])
    tpk_b = tb[np.argmax(gb)]

    drt.FREQ_MIN = 0.005                       # keep 10 mHz points (default floor 0.1 Hz)
    midp = dark["Re"].shape[1] // 2
    tp, gp, _ = compute_drt(dark["freqs"], dark["Re"][:, midp], -dark["Im"][:, midp])
    tpk_p = tp[np.argmax(gp)]
    # v1 truncated sweep (10 Hz cutoff) for the inset comparison
    drt.FREQ_MIN = 0.1
    midf = fast["Re"].shape[1] // 2
    tf, gf, _ = compute_drt(fast["freqs"], fast["Re"][:, midf], -fast["Im"][:, midf])
    tpk_f = tf[np.argmax(gf)]
    drt.LAMBDA_REG = 0.01; drt.FREQ_MIN = 0.1  # restore defaults

    ax[0].axvspan(CT_LO, CT_HI, color="#d0f0d8", zorder=0)
    ax[0].text(np.sqrt(CT_LO * CT_HI), 1.13, "battery CT band\n50 ms - 2 s",
               ha="center", fontsize=8, color="#1E8449")
    ax[0].plot(tb, gb / gb.max(), color=C_BAT, lw=2,
               label=f"Battery ({NYQ_CELL}) charge-transfer arc\n  tau_peak={tpk_b:.1e} s  (solid-state R_ct)")
    ax[0].plot(tp, gp / gp.max(), color=C_PER, lw=2,
               label=f"Perovskite (dark dev, 10 mHz sweep)\n  tau_peak={tpk_p:.1e} s  (ionic migration)")
    ax[0].plot(tf, gf / gf.max(), color=C_PER, lw=1.2, ls=":", alpha=0.8,
               label=f"Perovskite v1 (10 Hz cutoff)\n  tau_peak={tpk_f:.1e} s  (electronic only)")
    ax[0].set_xscale("log"); ax[0].set_ylim(0, 1.25)
    ax[0].set_xlabel("relaxation time  tau  /  s   (log)")
    ax[0].set_ylabel("DRT  gamma(tau)  (normalized)")
    ax[0].set_title("Extending the sweep to 10 mHz reveals the perovskite ionic feature\n"
                    "inside the battery charge-transfer band (v1 cutoff missed it)", fontsize=9.5)
    ax[0].legend(fontsize=7.5, loc="upper left")

    # --- panel 2: normalized arc-growth trajectories (clean labeled light device) ---
    Rp_f, th_f = fast["rp"], fast["t_hours"]
    ax[1].plot(th_f / th_f[-1], 100 * (Rp_f / Rp_f[0] - 1), "o-", ms=3,
               color=C_PER, label="Perovskite light dev @358 K (13 h)")
    ax[1].set_xlabel("normalized aging  (t / t_end)")
    ax[1].set_ylabel("perovskite  Delta Rp / Rp0  /  %", color=C_PER)
    ax[1].tick_params(axis="y", labelcolor=C_PER)
    ax[1].set_title("Both: monotonic interfacial-resistance growth\n"
                    "(extent differs -- battery aged to end-of-life)", fontsize=9.5)

    ax2 = ax[1].twinx()
    for c in BCELLS:
        b = bat[c]
        ax2.plot(b["cyc"] / b["cyc"].max(), 100 * (b["Rp"] / b["Rp"][0] - 1),
                 lw=1.1, alpha=0.7, color=C_BAT if c == NYQ_CELL else "#E59866")
    ax2.set_ylabel("battery  Delta Rp / Rp0  /  %  (CA cells)", color=C_BAT)
    ax2.tick_params(axis="y", labelcolor=C_BAT)
    ax[1].legend(handles=[Line2D([0], [0], color=C_PER, marker="o", label="Perovskite light dev (13 h)"),
                          Line2D([0], [0], color=C_BAT, label="Battery CA cells (to EOL+)")],
                 fontsize=8, loc="upper left")

    plt.tight_layout()
    p = os.path.join(OUT, "fig_B_v2_tau_overlap.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)
    print(f"  tau_peak battery={tpk_b:.2e}s | pero full={tpk_p:.2e}s | pero v1-cutoff={tpk_f:.2e}s")


# ════════════════════════════════════════════════════════════════════════════
def fig_C(bat, fast):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.suptitle("FIG C  |  The impedance descriptor tracks MEASURED performance in both domains",
                 fontsize=12, y=1.00)

    # --- battery: arc descriptor Rp -> SOH (pooled) ---
    Rp_all = np.concatenate([bat[c]["Rp"] for c in BCELLS])
    soh_all = np.concatenate([bat[c]["soh"] for c in BCELLS])
    r_b, _ = pearsonr(Rp_all, soh_all)
    cm = plt.cm.tab10(np.linspace(0, 1, len(BCELLS)))
    for i, c in enumerate(BCELLS):
        ax[0].scatter(bat[c]["Rp"] * 1e3, bat[c]["soh"], s=8, color=cm[i], alpha=0.6, label=c)
    ax[0].set_xlabel("arc descriptor  Rp = Re(1Hz)-Re(10kHz)  /  mOhm")
    ax[0].set_ylabel("SOH  (capacity / initial)")
    ax[0].set_title(f"Battery: arc descriptor tracks SOH\nPearson r = {r_b:.3f}  (CA cells pooled)",
                    fontsize=9.5)
    ax[0].legend(fontsize=7, ncol=2, markerscale=1.5)

    # --- perovskite: arc descriptor Rp -> Pmax retention (REAL light-JV label) ---
    Rp_p, pm, th = fast["rp"], fast["pmax"], fast["t_hours"]
    ret = pm / pm[0]
    r_p, _ = pearsonr(Rp_p, ret)
    sc = ax[1].scatter(Rp_p, ret, s=14, c=th, cmap="viridis")
    cb = fig.colorbar(sc, ax=ax[1], fraction=0.045, pad=0.02)
    cb.set_label("aging time / h", fontsize=8)
    ax[1].set_xlabel("arc descriptor  Rp = Re(10Hz)-Re(10MHz)  /  Ohm")
    ax[1].set_ylabel("Pmax / Pmax0  (JV @ 100% intensity)")
    # full-spectrum PC1 -> Pmax retention (reported in title)
    feats = np.hstack([fast["Re"].T, fast["Im"].T])
    pc1 = PCA(n_components=1).fit_transform(StandardScaler().fit_transform(feats))[:, 0]
    r_pc, _ = pearsonr(pc1, ret)
    ax[1].set_title(f"Perovskite (light dev @358 K): arc descriptor tracks measured Pmax\n"
                    f"Pearson r = {r_p:.3f}  (spectral PC1: r = {abs(r_pc):.3f})", fontsize=9.5)

    fig.text(0.5, -0.02,
             "v1 had no usable performance label (dark JV); the new per-step light-JV gives a real "
             "SOH-analog (Pmax retention) -- the same descriptor->performance relation holds in both domains.",
             ha="center", fontsize=8.5, style="italic")
    plt.tight_layout()
    p = os.path.join(OUT, "fig_C_v2_descriptor_performance.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)
    print(f"  battery Rp~SOH r={r_b:.3f} | pero Rp~Pmax-retention r={r_p:.3f} | PC1~Pmax r={abs(r_pc):.3f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    bat = load_battery()
    dark = load_pero("d358_full")
    fast = load_pero("l358_fast")
    fig_A(bat, dark, fast)
    fig_B(bat, dark, fast)
    fig_C(bat, fast)
    print("Done. Figures in", OUT)
