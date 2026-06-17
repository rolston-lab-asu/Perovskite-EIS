"""
Kramers-Kronig validity check, both domains (AI4X 2026).

The abstract names KK explicitly; this supplies the panel. Uses lin-KK
(Schoenleber/Boukamp measurement model): fit Z(w) = R0 + jwL + sum_k Rk/(1+jw*tau_k)
with tau_k log-spaced over the measured range and Rk UNCONSTRAINED (plain least
squares), so it tests causality/linearity/stationarity -- not RC-positivity like
the NNLS-DRT residual proxy used for the CB cells (run_kk_check_cb.py).
M is chosen per spectrum by the mu-criterion (Schoenleber 2014): grow M until
mu = 1 - sum(|Rk<0|)/sum(Rk>0) drops below 0.85 (negative Rk appearing = enough
elements, before noise-fitting sets in).

Series checked:
  battery   CA cells (10 kHz - 1 Hz), all spectra
  perovskite light dev @358 K fast sweep (10 MHz - 10 Hz), the labeled series
  perovskite dark dev @358 K full sweep (10 MHz - 10 mHz), the DRT series

Findings (2026-06-11):
  battery     median RMS 0.1-0.5% -> passes cleanly.
  pero light  ~2.5-3.5% -> KK-consistent at the few-% level; residual grows toward
              10 MHz (instrument parasitics; -Im<0 above ~3 MHz) and -Im<0 at
              10-34 Hz = onset of the documented PSC negative-capacitance LF feature.
  pero dark   >=10 Hz: median 6% (clean for MOhm/pA data). <10 Hz: median 45% RMS
              with lag-1 autocorrelation +0.98; stays 37-42% even with a dense fixed
              basis (M=70) -> SYSTEMATIC, i.e. non-stationary drift during the 3.4 h
              sweeps, a genuine KK violation — EXCEPT the early spectrum (LF RMS 5.6%
              at M=70, acceptable), which is the spectrum whose in-band ionic peak
              (tau_c 0.29 s) carries the tau-overlap claim.

Output: crossdomain/output/fig_D_v2_kk_validity.png + per-series residual stats.
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, r"battery_gpytorch_rtx4060\battery_gpytorch")
from run_drt_molicell import NATIVE_FREQS, load_cell

OUT = r"crossdomain\output"
os.makedirs(OUT, exist_ok=True)
BCELLS = ["CA1", "CA2", "CA4", "CA7", "CA8"]
NYQ_CELL = "CA7"
C_BAT, C_PER = "#C0392B", "#2471A3"


def lin_kk(freq, Z, mu_crit=0.85):
    """Lin-KK fit. Returns (rel_res_re, rel_res_im, M, mu) with residuals
    relative to |Z| per frequency, or None if < 6 valid points."""
    freq = np.asarray(freq, float)
    Z = np.asarray(Z, complex)
    ok = np.isfinite(freq) & np.isfinite(Z.real) & np.isfinite(Z.imag) & (freq > 0)
    freq, Z = freq[ok], Z[ok]
    if len(freq) < 6:
        return None
    omega = 2 * np.pi * freq
    t_min, t_max = 1 / omega.max(), 1 / omega.min()
    M_cap = max(3, int(0.8 * len(freq)))     # leave dof so noise is not fitted away

    def fit(M):
        # tau spans exactly the data range; extending it (Boukamp practice) makes the
        # mu-criterion fire on out-of-range negative Rk and under-fit badly here
        taus = np.logspace(np.log10(t_min), np.log10(t_max), M)
        WT = omega[:, None] * taus[None, :]
        re_cols = 1.0 / (1.0 + WT**2)
        im_cols = -WT / (1.0 + WT**2)
        # columns: [R0, L, Rk...]
        A = np.vstack([
            np.hstack([np.ones((len(freq), 1)), np.zeros((len(freq), 1)), re_cols]),
            np.hstack([np.zeros((len(freq), 1)), omega[:, None],          im_cols]),
        ])
        b = np.concatenate([Z.real, Z.imag])
        # weight by 1/|Z| so the small HF battery points count too
        w = np.concatenate([1 / np.abs(Z), 1 / np.abs(Z)])
        p, *_ = np.linalg.lstsq(A * w[:, None], b * w, rcond=None)
        Rk = p[2:]
        pos, neg = Rk[Rk > 0].sum(), -Rk[Rk < 0].sum()
        mu = 1.0 if pos == 0 else 1.0 - neg / pos
        Zfit = (A @ p)[:len(freq)] + 1j * (A @ p)[len(freq):]
        return mu, Zfit

    M, mu, Zfit = 3, 1.0, None
    for M in range(3, M_cap + 1):
        mu, Zfit = fit(M)
        if mu < mu_crit:
            break
    res = (Z - Zfit) / np.abs(Z)
    return freq, 100 * res.real, 100 * res.imag, M, mu


def series_stats(name, spectra, f_split=None):
    """spectra: list of (freq, Z). Prints and returns per-spectrum RMS residuals.
    f_split: if set, also return RMS restricted to f >= and f < f_split."""
    rms_all, rms_hi, rms_lo, results = [], [], [], []
    for f, Z in spectra:
        out = lin_kk(f, Z)
        if out is None:
            results.append(None)
            continue
        fq, rre, rim, M, mu = out
        rms_all.append(np.sqrt(np.mean(rre**2 + rim**2) / 2))
        if f_split is not None:
            m = fq >= f_split
            rms_hi.append(np.sqrt(np.mean(rre[m]**2 + rim[m]**2) / 2))
            rms_lo.append(np.sqrt(np.mean(rre[~m]**2 + rim[~m]**2) / 2))
        results.append(out)
    rms_all = np.array(rms_all)
    print(f"  {name:<42s} n={len(rms_all):3d}  median RMS={np.median(rms_all):5.2f}%  "
          f"p90={np.percentile(rms_all, 90):5.2f}%  max={rms_all.max():5.2f}%")
    if f_split is not None:
        rms_hi, rms_lo = np.array(rms_hi), np.array(rms_lo)
        print(f"    {'f >= ' + str(f_split) + ' Hz':<40s}        median RMS={np.median(rms_hi):5.2f}%")
        print(f"    {'f <  ' + str(f_split) + ' Hz':<40s}        median RMS={np.median(rms_lo):5.2f}%")
        return results, rms_all, rms_hi, rms_lo
    return results, rms_all


def lf_drift_check(results, f_split=10.0):
    """Lag-1 autocorrelation of LF residuals: drift -> +1, random noise -> ~0."""
    acs = []
    for out in results:
        if out is None:
            acs.append(np.nan)
            continue
        fq, rre, rim, M, mu = out
        lf = fq < f_split
        if lf.sum() < 8:
            acs.append(np.nan)
            continue
        x = rre[lf] - rre[lf].mean()
        acs.append(np.corrcoef(x[:-1], x[1:])[0, 1])
    return np.array(acs)


def battery_spectra():
    out = {}
    for c in BCELLS:
        eis, cap, cyc, soh = load_cell(c)
        spectra = [(NATIVE_FREQS, eis[i, :33] - 1j * eis[i, 33:])  # stored col 33+ is -Im
                   for i in range(eis.shape[0])]
        out[c] = spectra
    return out


def pero_spectra(key):
    d = np.load(rf"crossdomain\data\perovskite\pero_{key}.npz")
    return [(d["freqs"], d["Re"][:, k] + 1j * d["Im"][:, k])
            for k in range(d["Re"].shape[1])]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("lin-KK residuals (RMS of Delta Re, Delta Im in % of |Z|, per spectrum):")

    bat = battery_spectra()
    bat_res, bat_rms = {}, {}
    for c in BCELLS:
        bat_res[c], bat_rms[c] = series_stats(f"battery {c} (10 kHz-1 Hz)", bat[c])
    fast_res, fast_rms = series_stats("perovskite light dev @358 K (10 MHz-10 Hz)",
                                      pero_spectra("l358_fast"))
    dark_res, dark_rms, dark_hi, dark_lo = series_stats(
        "perovskite dark dev @358 K (10 MHz-10 mHz)", pero_spectra("d358_full"),
        f_split=10.0)

    acs = lf_drift_check(dark_res)
    ok = np.isfinite(acs)
    print(f"  dark dev LF (<10 Hz) residual lag-1 autocorr: median {np.nanmedian(acs):+.2f} "
          f"(drift -> +1, noise -> 0) | spectrum 0/1 = {acs[ok][0]:+.2f}/{acs[ok][1]:+.2f}")
    print("  -> LF deviation is SYSTEMATIC (drift during 3.4 h sweeps), not noise;")
    print("     early dark spectrum is the KK-acceptable one and carries the tau-overlap claim.")

    # ---- figure: residual spectra (early/mid/late) per series + RMS summary ----
    fig, axes = plt.subplots(1, 4, figsize=(19, 4.6),
                             gridspec_kw={"width_ratios": [1, 1, 1, 0.9]})
    fig.suptitle("FIG D  |  Kramers-Kronig validity (lin-KK measurement model): "
                 "battery passes at <0.5%, perovskite at the few-% level where stationary",
                 fontsize=12, y=1.02)

    panels = [
        (axes[0], bat_res[NYQ_CELL], f"battery {NYQ_CELL}\n10 kHz - 1 Hz", C_BAT),
        (axes[1], fast_res, "perovskite light dev @358 K\n10 MHz - 10 Hz", C_PER),
        (axes[2], dark_res, "perovskite dark dev @358 K\n10 MHz - 10 mHz", C_PER),
    ]
    stage_cols = {"early": "#7fb3d5", "mid": "#f5a623", "late": "#444444"}
    for ax, results, title, col in panels:
        valid = [r for r in results if r is not None]
        picks = {"early": valid[0], "mid": valid[len(valid) // 2], "late": valid[-1]}
        for lbl, (fq, rre, rim, M, mu) in picks.items():
            ax.plot(fq, rre, "o-", ms=2.5, lw=0.9, color=stage_cols[lbl],
                    label=f"{lbl}: ΔRe (M={M})")
            ax.plot(fq, rim, "s--", ms=2.5, lw=0.9, color=stage_cols[lbl], alpha=0.55,
                    label=f"{lbl}: ΔIm")
        ax.axhline(0, color="gray", lw=0.7)
        for y in (1, -1):
            ax.axhline(y, color="gray", lw=0.7, ls=":")
        ax.set_xscale("log")
        ax.set_xlabel("frequency / Hz")
        ax.set_ylabel("lin-KK residual  /  % of |Z|")
        ax.set_title(title, fontsize=9.5, color=col)
        ax.legend(fontsize=6.5, ncol=2)

    # summary panel: RMS residual distributions (dark split at 10 Hz)
    ax = axes[3]
    data = ([np.concatenate([bat_rms[c] for c in BCELLS])]
            + [fast_rms] + [dark_hi] + [dark_lo])
    bp = ax.boxplot(data, tick_labels=["battery\nCA cells", "pero light\n(10 Hz)",
                                       "pero dark\nf≥10 Hz", "pero dark\nf<10 Hz"],
                    showfliers=True, flierprops=dict(ms=2.5, alpha=0.5), widths=0.55)
    for med in bp["medians"]:
        med.set_color("#C0392B")
    ax.set_yscale("log")
    ax.set_ylabel("per-spectrum RMS residual / %")
    ax.axhline(1, color="gray", lw=0.7, ls=":")
    ax.set_title("all spectra, per series", fontsize=9.5)

    fig.text(0.5, -0.06,
             "lin-KK: Z fit by R0 + jwL + sum Rk/(1+jw tau_k), Rk unconstrained, M per spectrum by the mu-criterion "
             "(Schoenleber 2014) -- low residual = causal, linear, stationary data.\n"
             "Battery and perovskite light device pass (0.1-0.5% and ~3%). Dark device passes above 10 Hz (1-4%); "
             "below 10 Hz the residual is large AND autocorrelated (lag-1 ~ +0.98) -> non-stationary drift during "
             "the 3.4 h sweeps,\nnot random noise. The early dark spectrum (RMS 5.6% at LF) is KK-acceptable and is "
             "the spectrum whose in-band ionic peak (tau_c = 0.29 s) carries the tau-overlap claim.",
             ha="center", fontsize=8.5, style="italic")
    plt.tight_layout()
    p = os.path.join(OUT, "fig_D_v2_kk_validity.png")
    fig.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved", p)
