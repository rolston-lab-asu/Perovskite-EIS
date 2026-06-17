"""
Cross-domain proof-of-concept figures for AI4X 2026 abstract:
"Transferable Impedance-Grounded Learning for Interfacial Degradation
 Across Energy Systems" (Li-ion battery <-> perovskite solar cell).

Honest claim (perovskite = 1 device, 50 spectra -> proof-of-concept):
  * The SAME physics-grounded EIS pipeline (DRT, arc descriptors) applies to
    both domains and resolves a single dominant interfacial relaxation in each.
  * Both degrade by the SAME signature: monotonic interfacial arc-resistance growth.
  * The descriptor is degradation-informative in both domains.
  * The two interfaces are separated by ~4-5 decades in BOTH impedance scale and
    characteristic tau -- shared structure across that gap is exactly what motivates
    a shared-encoder transfer model (the abstract's proposed future work).

Methods learned from NIMS (DRT Tikhonov-NNLS = compute_drt). Data: battery repo
(CA cells) + perovskite EIS only. NIMS data is NOT used.

FIG A : side-by-side Nyquist degradation series (arcs grow in both).
FIG B : tau / scale-separation (DRT peaks ~5 decades apart, same formalism)
        + normalized arc-growth trajectories (same monotonic law, different extent).
FIG C : descriptor is degradation-informative -- battery Rp->SOH, perovskite Rp & PC1->aging.
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
from run_drt_molicell import compute_drt, NATIVE_FREQS, load_cell

OUT = r"crossdomain\output"
os.makedirs(OUT, exist_ok=True)
BCELLS = ["CA1", "CA2", "CA4", "CA7", "CA8"]   # clean RT cells (exclude DNF CA6 / odd ones)
NYQ_CELL = "CA7"

# ── battery freqs (high->low) : 10 kHz .. 1 Hz ; Re=[:33], Im=[33:] ─────────────
B_FREQS = NATIVE_FREQS                       # 33 pts


def load_battery():
    """Per cell: raw EIS, SOH, Rp arc diameter, DRT gamma(tau) of a mid-life spectrum."""
    out = {}
    for c in BCELLS:
        eis, cap, cyc, soh = load_cell(c)
        Re = eis[:, :33]; Im = eis[:, 33:]
        Rp = Re[:, -1] - Re[:, 0]            # Re(1 Hz) - Re(10 kHz)  [arc diameter, Ohm]
        out[c] = dict(eis=eis, Re=Re, Im=Im, cyc=cyc, soh=soh, Rp=Rp)
    return out


def load_perovskite():
    d = np.load(r"crossdomain\data\perovskite\perovskite_aging.npz")
    return {k: d[k] for k in d.files}


def drt_peak(freq, re, neg_im):
    tau, gamma, r_inf = compute_drt(freq, re, neg_im)
    if tau is None:
        return None, None, np.nan
    return tau, gamma, tau[np.argmax(gamma)]


# ════════════════════════════════════════════════════════════════════════════
def fig_A(bat, per):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.suptitle("FIG A  |  Same EIS measurement, two energy systems: interfacial arc grows with aging",
                 fontsize=12, y=1.00)

    # battery
    b = bat[NYQ_CELL]; n = b["Re"].shape[0]
    cm = plt.cm.viridis(np.linspace(0, 1, n))
    for i in range(n):
        ax[0].plot(b["Re"][i] * 1e3, -b["Im"][i] * 1e3, color=cm[i], lw=0.7, alpha=0.7)
    ax[0].set_xlabel("Re(Z)  /  mOhm"); ax[0].set_ylabel("-Im(Z)  /  mOhm")
    ax[0].set_title(f"Li-ion battery ({NYQ_CELL})\n10 kHz - 1 Hz, milli-ohm scale", fontsize=10)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(b["soh"].max(), b["soh"].min()))
    cb = fig.colorbar(sm, ax=ax[0], fraction=0.045, pad=0.02); cb.set_label("SOH (1 -> 0)", fontsize=8)

    # perovskite
    Re, Im = per["Re"], per["Im"]; ns = Re.shape[1]
    cm = plt.cm.viridis(np.linspace(0, 1, ns))
    for k in range(ns):
        ax[1].plot(Re[:, k], -Im[:, k], color=cm[k], lw=0.7, alpha=0.7)
    ax[1].set_xlabel("Re(Z)  /  Ohm"); ax[1].set_ylabel("-Im(Z)  /  Ohm")
    ax[1].set_title("Perovskite solar cell (1 device)\n10 MHz - 10 Hz, ohm scale, light @ 358 K", fontsize=10)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(0, ns))
    cb = fig.colorbar(sm, ax=ax[1], fraction=0.045, pad=0.02); cb.set_label("aging step (0 -> ~13 h)", fontsize=8)

    fig.text(0.5, -0.02, "Impedance magnitudes differ ~10^4x, yet both show a growing semicircular interfacial arc "
             "(battery: charge-transfer R_ct; perovskite: HF recombination R_rec) -- a shared degradation signature.\n"
             "Perovskite sweep is 10 MHz-10 Hz, so the low-frequency ionic feature (<1 Hz) is outside this window.",
             ha="center", fontsize=8.5, style="italic")
    plt.tight_layout()
    p = os.path.join(OUT, "fig_A_nyquist_degradation.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)


# ════════════════════════════════════════════════════════════════════════════
def fig_B(bat, per):
    import run_drt_molicell as drt
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.suptitle("FIG B  |  One DRT formalism, two domains: a dominant interfacial relaxation in each, "
                 "~5 decades apart in tau", fontsize=11.5, y=1.00)

    # --- panel 1: DRT gamma(tau) normalized, both domains, shared log-tau axis ---
    # Same Tikhonov-NNLS DRT, same regularisation for both (honest like-for-like).
    drt.LAMBDA_REG = 0.5
    # battery: mid-life spectrum of NYQ_CELL (R_ct / SEI interfacial arc)
    b = bat[NYQ_CELL]; mid = b["Re"].shape[0] // 2
    tb, gb, tpk_b = drt_peak(B_FREQS, b["Re"][mid], b["Im"][mid])
    # perovskite: mid-life spectrum (HF recombination arc: geometric C + R_rec)
    midp = per["Re"].shape[1] // 2
    tp, gp, tpk_p = drt_peak(per["freqs"], per["Re"][:, midp], -per["Im"][:, midp])
    drt.LAMBDA_REG = 0.01  # restore default

    ax[0].plot(tb, gb / gb.max(), color="#C0392B", lw=2,
               label=f"Battery ({NYQ_CELL}) charge-transfer arc\n  tau_peak={tpk_b:.1e}s  (solid-state R_ct)")
    ax[0].plot(tp, gp / gp.max(), color="#2471A3", lw=2,
               label=f"Perovskite HF arc (geom. C + R_rec)\n  tau_peak={tpk_p:.1e}s  (electronic recombination)")
    ax[0].set_xscale("log"); ax[0].set_ylim(0, 1.18)
    ax[0].set_xlabel("relaxation time  tau  /  s   (log)"); ax[0].set_ylabel("DRT  gamma(tau)  (normalized)")
    ax[0].set_title("Same Tikhonov-NNLS DRT resolves a dominant interfacial arc per domain",
                    fontsize=9.5)
    ax[0].legend(fontsize=7.5, loc="upper center")
    ax[0].annotate("", xy=(tpk_p, 1.08), xytext=(tpk_b, 1.08),
                   arrowprops=dict(arrowstyle="<->", color="gray"))
    ax[0].text(np.sqrt(tpk_b * tpk_p), 1.10, f"~{np.log10(tpk_b/tpk_p):.1f} decades in tau",
               ha="center", fontsize=8.5, color="gray")

    # --- panel 2: normalized arc-growth trajectories (same monotonic law) ---
    # perovskite
    Rp_p = per["Rp"]; ns = len(Rp_p)
    fp = np.arange(ns) / (ns - 1)
    ax[1].plot(fp, 100 * (Rp_p / Rp_p[0] - 1), "o-", ms=3, color="#2471A3",
               label="Perovskite arc Rp (mild aging, 13 h)")
    ax[1].set_xlabel("normalized aging  (t / t_end)")
    ax[1].set_ylabel("perovskite  Delta Rp / Rp0  /  %", color="#2471A3")
    ax[1].tick_params(axis="y", labelcolor="#2471A3")
    ax[1].set_title("Both: monotonic interfacial-resistance growth\n(extent differs -- battery aged to end-of-life)",
                    fontsize=9.5)

    ax2 = ax[1].twinx()
    for c in BCELLS:
        b = bat[c]; Rp = b["Rp"]; f = b["cyc"] / b["cyc"].max()
        ax2.plot(f, 100 * (Rp / Rp[0] - 1), lw=1.1, alpha=0.7,
                 color="#C0392B" if c == NYQ_CELL else "#E59866")
    ax2.set_ylabel("battery  Delta Rp / Rp0  /  %  (CA cells)", color="#C0392B")
    ax2.tick_params(axis="y", labelcolor="#C0392B")
    from matplotlib.lines import Line2D
    ax[1].legend(handles=[Line2D([0],[0], color="#2471A3", marker="o", label="Perovskite (mild, 13 h)"),
                          Line2D([0],[0], color="#C0392B", label="Battery CA cells (to EOL+)")],
                 fontsize=8, loc="upper left")

    plt.tight_layout()
    p = os.path.join(OUT, "fig_B_tau_scale_separation.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)
    return tpk_b, tpk_p


# ════════════════════════════════════════════════════════════════════════════
def fig_C(bat, per):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.suptitle("FIG C  |  The impedance descriptor is degradation-informative in both domains",
                 fontsize=12, y=1.00)

    # --- battery: arc descriptor Rp -> SOH (pooled across cells) ---
    Rp_all, soh_all = [], []
    for c in BCELLS:
        b = bat[c]; Rp_all.append(b["Rp"]); soh_all.append(b["soh"])
    Rp_all = np.concatenate(Rp_all); soh_all = np.concatenate(soh_all)
    r_b, _ = pearsonr(Rp_all, soh_all)
    cm = plt.cm.tab10(np.linspace(0, 1, len(BCELLS)))
    i0 = 0
    for i, c in enumerate(BCELLS):
        n = len(bat[c]["soh"])
        ax[0].scatter(bat[c]["Rp"] * 1e3, bat[c]["soh"], s=8, color=cm[i], alpha=0.6, label=c)
        i0 += n
    ax[0].set_xlabel("arc descriptor  Rp = Re(1Hz)-Re(10kHz)  /  mOhm")
    ax[0].set_ylabel("SOH  (capacity / initial)")
    ax[0].set_title(f"Battery: single arc descriptor tracks SOH\nPearson r = {r_b:.3f}  (CA cells pooled)", fontsize=9.5)
    ax[0].legend(fontsize=7, ncol=2, markerscale=1.5)

    # --- perovskite: descriptor (Rp) & spectral PC1 -> aging coordinate ---
    Rp_p = per["Rp"]; ns = len(Rp_p); step = np.arange(ns)
    r_p, _ = pearsonr(step, Rp_p)
    ax[1].plot(step, Rp_p, "o-", ms=3, color="#2471A3", label=f"arc Rp  (r vs aging = {r_p:.3f})")
    ax[1].set_xlabel("aging step (0 -> ~13 h)")
    ax[1].set_ylabel("perovskite arc Rp ~ R_rec  /  Ohm", color="#2471A3")
    ax[1].tick_params(axis="y", labelcolor="#2471A3")

    # spectral PC1 on per-spectrum normalized full spectra
    X = np.vstack([per["Re"].T, ]).T  # placeholder
    feats = np.hstack([per["Re"].T, per["Im"].T])           # (50, 70)
    Xs = StandardScaler().fit_transform(feats)
    pc1 = PCA(n_components=2).fit_transform(Xs)[:, 0]
    if pearsonr(step, pc1)[0] < 0:
        pc1 = -pc1
    r_pc, _ = pearsonr(step, pc1)
    ax3 = ax[1].twinx()
    ax3.plot(step, pc1, "s--", ms=3, color="#117A65", label=f"spectral PC1 (r={r_pc:.3f})")
    ax3.set_ylabel("spectral PC1 (full EIS)", color="#117A65")
    ax3.tick_params(axis="y", labelcolor="#117A65")
    ax[1].set_title(f"Perovskite: arc descriptor & full-spectrum PC1\nencode a monotonic degradation coordinate",
                    fontsize=9.5)
    from matplotlib.lines import Line2D
    ax[1].legend(handles=[Line2D([0],[0], color="#2471A3", marker="o", label=f"arc Rp (r={r_p:.2f})"),
                          Line2D([0],[0], color="#117A65", marker="s", ls="--", label=f"spectral PC1 (r={r_pc:.2f})")],
                 fontsize=8, loc="lower right")

    plt.tight_layout()
    p = os.path.join(OUT, "fig_C_descriptor_predictive.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    print("saved", p)
    print(f"  battery Rp~SOH r={r_b:.3f} | perovskite Rp~aging r={r_p:.3f} | PC1~aging r={r_pc:.3f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    bat = load_battery()
    per = load_perovskite()
    fig_A(bat, per)
    tb, tp = fig_B(bat, per)
    fig_C(bat, per)
    print(f"\nbattery tau_peak={tb:.2e}s  perovskite tau_peak={tp:.2e}s  "
          f"separation={np.log10(tb/tp):.1f} decades")
    print("Done. Figures in", OUT)
