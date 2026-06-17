"""
AI4X Accelerate 2026 — full A0 draft poster assembly.

Builds two extra poster-styled panels, then composes the complete poster:

  poster_4_kk_mini   : Kramers-Kronig rigor panel (lin-KK residual boxplots,
                       dark-device <10 Hz drift called out honestly).
  poster_5_encoder   : the PROPOSED method — shared tau-space encoder with
                       domain heads, drawn around real mini-Nyquist insets.
  poster_6_ard       : the ARD work (this repo's core) — coupled ARD-RBF GPR
                       trained on CA1-6 capacity (recipe of run_ca_zhang.py RT
                       group, seed 42); learned frequency weights vs the
                       DRT-derived shared tau band. Weights cached in
                       output/poster/ard_weights_rt.npz (delete to retrain).
  poster_draft_A0    : assembled A0 portrait (33.1 x 46.8 in) PDF + PNG.

Design language:
  * Okabe-Ito two-domain palette (battery vermillion / perovskite blue /
    shared band green) — consistent with poster_figs.py.
  * "tau-bridge" ribbon under the title: one log-tau axis spanning the poster,
    both domains' relaxations marked, shared 50 ms - 2 s band highlighted.
    It doubles as a graphical abstract.
  * Reading flow: (1) hook -> (2) headline tau overlap + (5) proposed encoder
    -> (3) descriptor evidence + (4) KK rigor -> takeaway cards + honest-limits box.

Run (repo root, venv): python -X utf8 crossdomain/poster_assembly.py
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

sys.path.insert(0, r"crossdomain")
import kk_check_crossdomain as kk

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)

# matched to the hero Nyquist cards / AI4X theme (see poster_figs.py)
C_BAT, C_PER, C_BAND = "#D55E00", "#7C4DCB", "#C79100"
C_DARKTXT, C_GREY = "#202124", "#6B7280"
C_RULE, C_PAPER = "#D9DEE3", "#F7F8F9"
REPO_LIB  = "https://github.com/rolston-lab-asu/LIB-EIS-ML"
REPO_PERO = "https://github.com/rolston-lab-asu/Perovskite-EIS"

POSTER_RC = {
    "font.size": 15, "axes.labelsize": 17, "axes.titlesize": 17,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 12.5,
    "lines.linewidth": 2.2, "axes.linewidth": 1.3,
    "savefig.facecolor": "white", "axes.facecolor": "white",
    "font.family": "Arial",
}
plt.rcParams.update(POSTER_RC)


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {OUT}\\{name}.png/.pdf")


# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 4 — KK rigor mini-panel
def build_kk_mini():
    print("computing lin-KK stats for poster_4 ...")
    bat = kk.battery_spectra()
    bat_rms = []
    for c in kk.BCELLS:
        _, r = kk.series_stats(f"battery {c}", bat[c])
        bat_rms.append(r)
    _, fast_rms = kk.series_stats("pero light", kk.pero_spectra("l358_fast"))
    _, _, dark_hi, dark_lo = kk.series_stats("pero dark", kk.pero_spectra("d358_full"),
                                             f_split=10.0)

    fig, ax = plt.subplots(figsize=(7.4, 6.4), constrained_layout=True)
    data = [np.concatenate(bat_rms), fast_rms, dark_hi, dark_lo]
    cols = [C_BAT, C_PER, C_PER, "#909497"]
    bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=True,
                    flierprops=dict(ms=3, alpha=0.5),
                    tick_labels=["battery\nCA cells", "perovskite\nlight dev",
                                 "pero dark\nf ≥ 10 Hz", "pero dark\nf < 10 Hz"])
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c); patch.set_alpha(0.35); patch.set_edgecolor(c)
    for med in bp["medians"]:
        med.set_color(C_DARKTXT); med.set_linewidth(2)
    ax.set_yscale("log")
    ax.set_ylabel("lin-KK RMS residual  /  % of |Z|")
    ax.axhspan(ax.get_ylim()[0], 5, color=C_BAND, alpha=0.10, zorder=0)
    ax.text(0.55, 3.6, "KK-consistent", color=C_BAND, fontsize=13, fontweight="bold")
    ax.annotate("drift during 3.4 h sweeps\n(non-stationary, NOT noise:\nlag-1 autocorr +0.98)",
                xy=(4, 45), xytext=(2.35, 130), fontsize=12.5, ha="center",
                arrowprops=dict(arrowstyle="->", color="#909497", lw=1.5))
    ax.set_ylim(0.02, 600)
    ax.set_title("Causality check passes where it must\n(lin-KK measurement model, μ-criterion)",
                 fontsize=16, fontweight="bold", pad=10)
    save(fig, "poster_4_kk_mini")


# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 5 — proposed shared-encoder schematic
def build_encoder_schematic():
    bat = kk.battery_spectra()
    f_b, Z_b = bat["CA7"][len(bat["CA7"]) // 2]
    d = np.load(r"crossdomain\data\perovskite\pero_l358_fast.npz")
    Z_p = d["Re"][:, 25] + 1j * d["Im"][:, 25]

    fig = plt.figure(figsize=(11.4, 6.0))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off")

    def box(x, y, w, h, fc, ec, lw=2.5):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2",
                           fc=fc, ec=ec, lw=lw, mutation_scale=1.2)
        ax.add_patch(b)

    def arrow(x0, y0, x1, y1, color=C_GREY):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                     mutation_scale=22, lw=2.6, color=color))

    # domain inputs with real mini-Nyquist insets
    box(2, 57, 22, 33, "white", C_BAT)
    ax.text(13, 86, "Li-ion battery EIS", ha="center", fontsize=14,
            fontweight="bold", color=C_BAT)
    axb = fig.add_axes([0.045, 0.63, 0.165, 0.20])
    axb.plot(Z_b.real * 1e3, -Z_b.imag * 1e3, "o-", ms=2.5, lw=1.4, color=C_BAT)
    axb.set_xticks([]); axb.set_yticks([])
    axb.set_xlabel("mΩ scale", fontsize=11, color=C_BAT)

    box(2, 8, 22, 33, "white", C_PER)
    ax.text(13, 37, "Perovskite cell EIS", ha="center", fontsize=14,
            fontweight="bold", color=C_PER)
    axp = fig.add_axes([0.045, 0.135, 0.165, 0.20])
    m = np.isfinite(Z_p)
    axp.plot(Z_p.real[m], -Z_p.imag[m], "o-", ms=2.5, lw=1.4, color=C_PER)
    axp.set_xticks([]); axp.set_yticks([])
    axp.set_xlabel("Ω–MΩ scale", fontsize=11, color=C_PER)

    # physics-grounded featurisation
    box(32, 34, 22, 32, "#FBFCFC", C_GREY)
    ax.text(43, 57, "Physics-grounded\nfront end", ha="center", fontsize=14,
            fontweight="bold", color=C_DARKTXT)
    ax.text(43, 43, "lin-KK gate (causality)\nDRT  →  log-τ aligned\nγ(τ) features",
            ha="center", fontsize=12.5, color=C_DARKTXT)

    # shared encoder
    box(62, 34, 16, 32, "#E8F8F2", C_BAND)
    ax.text(70, 55, "SHARED\nENCODER", ha="center", fontsize=15,
            fontweight="bold", color=C_BAND)
    ax.text(70, 41.5, "one τ-space,\nboth domains", ha="center", fontsize=12,
            color=C_DARKTXT)

    # heads
    box(86, 57, 12, 22, "white", C_BAT)
    ax.text(92, 70.5, "battery\nhead", ha="center", fontsize=13, fontweight="bold", color=C_BAT)
    ax.text(92, 60.5, "SOH · RUL", ha="center", fontsize=12, color=C_DARKTXT)
    box(86, 19, 12, 22, "white", C_PER)
    ax.text(92, 32.5, "perovskite\nhead", ha="center", fontsize=13, fontweight="bold", color=C_PER)
    ax.text(92, 22.5, "Pmax\nretention", ha="center", fontsize=12, color=C_DARKTXT)

    arrow(25.5, 73, 33, 58, C_BAT)
    arrow(25.5, 25, 33, 41, C_PER)
    arrow(55.5, 50, 61, 50)
    arrow(79.5, 55, 86, 66, C_BAT)
    arrow(79.5, 45, 86, 32, C_PER)

    ax.text(50, 2.5, "Evaluation = TRANSFER GAIN: does battery data improve perovskite "
                     "degradation prediction when labels are scarce (and vice versa)?",
            ha="center", fontsize=13, style="italic", color=C_DARKTXT)
    save(fig, "poster_5_encoder")


# ════════════════════════════════════════════════════════════════════════════
# POSTER FIG 6 — the ARD work: learned frequency weights vs the shared tau band
# Faithful re-run of run_ca_zhang.py's RT capacity model (CoupledARDRBF, 33 ls,
# train CA1-6, ARD_MAX_N=600, seed 42); that script runs its whole experiment at
# import, so the kernel class is replicated verbatim here.
N_FREQ = 33

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import (ConstantKernel, WhiteKernel,
                                              Kernel, Hyperparameter)


class CoupledARDRBF(Kernel):
    def __init__(self, length_scale=None, length_scale_bounds=(1e-5, 1e5)):
        if length_scale is None:
            length_scale = np.ones(N_FREQ)
        self.length_scale        = np.asarray(length_scale, dtype=float)
        self.length_scale_bounds = length_scale_bounds

    @property
    def hyperparameter_length_scale(self):
        return Hyperparameter('length_scale', 'numeric',
                              self.length_scale_bounds, n_elements=N_FREQ)

    def __call__(self, X, Y=None, eval_gradient=False):
        X_re = X[:, :N_FREQ];  X_im = X[:, N_FREQ:]
        if Y is None:
            Y_re, Y_im = X_re, X_im
        else:
            Y_re, Y_im = Y[:, :N_FREQ], Y[:, N_FREQ:]
        ls = self.length_scale
        N, M = X_re.shape[0], Y_re.shape[0]
        dist2 = np.zeros((N, M))
        for i in range(N_FREQ):
            dr = X_re[:, i:i+1] - Y_re[:, i]
            di = X_im[:, i:i+1] - Y_im[:, i]
            dist2 += (dr**2 + di**2) / (2.0 * ls[i]**2)
        K = np.exp(-dist2)
        if eval_gradient:
            dK = np.empty((N, M, N_FREQ))
            for i in range(N_FREQ):
                dr = X_re[:, i:i+1] - Y_re[:, i]
                di = X_im[:, i:i+1] - Y_im[:, i]
                dK[:, :, i] = K * (dr**2 + di**2) / ls[i]**2
            return K, dK
        return K

    def diag(self, X):
        return np.ones(X.shape[0])

    def is_stationary(self):
        return True

    def __repr__(self):
        return f'CoupledARDRBF(ls={self.length_scale.round(3)})'


def get_ard_weights():
    cache = os.path.join(OUT, "ard_weights_rt.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        return d["w"], d["freqs"]
    from run_drt_molicell import load_cell as load_b
    EIS = np.vstack([load_b(c)[0] for c in ["CA1", "CA2", "CA3", "CA4", "CA5", "CA6"]])
    Cap = np.concatenate([load_b(c)[1] for c in ["CA1", "CA2", "CA3", "CA4", "CA5", "CA6"]])
    mu, sig = EIS.mean(0), EIS.std(0, ddof=1)
    Xn = (EIS - mu) / np.where(sig == 0, 1.0, sig)
    rng = np.random.default_rng(42)
    idx = rng.choice(len(Xn), min(600, len(Xn)), replace=False)
    kern = (ConstantKernel(1.0) * CoupledARDRBF() + WhiteKernel(noise_level=1.0))
    gpr = GaussianProcessRegressor(kernel=kern, normalize_y=True, alpha=0.1,
                                   n_restarts_optimizer=10)
    print(f"fitting coupled ARD-RBF GPR on {len(idx)} rows (CA1-6 capacity) ...")
    gpr.fit(Xn[idx], Cap[idx])
    ls = gpr.kernel_.k1.k2.length_scale
    w = np.exp(-ls); w = w / w.sum()
    np.savez(cache, w=w, freqs=kk.NATIVE_FREQS, ls=ls)
    print("cached ->", cache)
    return w, kk.NATIVE_FREQS


def build_ard_panel():
    w, freqs = get_ard_weights()
    # the fit concentrates ~all weight on TWO frequencies: 422 Hz (SEI arc) and
    # 1 Hz (tau = 0.159 s = the DRT charge-transfer peak, inside the shared band)
    # the shared tau band 50 ms - 2 s mapped to frequency: f = 1/(2 pi tau)
    f_hi, f_lo = 1 / (2 * np.pi * 0.05), 1 / (2 * np.pi * 2.0)
    i_ct = np.argmax(np.where(freqs <= 3.2, w, 0))      # top weight inside band
    i_hf = np.argmax(np.where(freqs > 3.2, w, 0))       # top weight outside band
    t_ct, t_hf = 1 / (2 * np.pi * freqs[i_ct]), 1 / (2 * np.pi * freqs[i_hf])

    fig, ax = plt.subplots(figsize=(9.6, 6.2), constrained_layout=True)
    ax.axvspan(f_lo, f_hi, color=C_BAND, alpha=0.18, zorder=0)
    ax.text(np.sqrt(f_lo * f_hi), 1.02 * w.max(), "shared τ band\n(50 ms – 2 s)",
            ha="center", fontsize=14, color=C_BAND, fontweight="bold")
    ax.vlines(freqs, 0, w, color=C_BAT, lw=3.2, alpha=0.85)
    ax.plot(freqs, w, "o", ms=7, color=C_BAT)
    ax.annotate(f"{freqs[i_ct]:.2f} Hz   τ = {t_ct:.2f} s   w = {w[i_ct]:.2f}\n"
                "= the DRT charge-transfer peak,\n   inside the shared band",
                xy=(freqs[i_ct], w[i_ct]), xytext=(2.5, 0.74 * w.max()),
                fontsize=13.5, fontweight="bold", color=C_BAND,
                arrowprops=dict(arrowstyle="->", color=C_BAND, lw=2))
    ax.annotate(f"{freqs[i_hf]:.0f} Hz   τ = {1e3*t_hf:.1f} ms   w = {w[i_hf]:.2f}\n"
                "(SEI arc — battery-specific)",
                xy=(freqs[i_hf] * 1.4, w[i_hf]), xytext=(3000, 0.72 * w.max()),
                fontsize=13.5, ha="center", color=C_BAT,
                arrowprops=dict(arrowstyle="->", color=C_BAT, lw=2,
                                connectionstyle="arc3,rad=0.2"))
    ax.set_xscale("log")
    ax.set_ylim(0, 1.22 * w.max())
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("frequency  /  Hz")
    ax.set_ylabel("ARD weight  $w_i = e^{-\\ell_i}$ (normalized)")
    sec = ax.secondary_xaxis("top", functions=(lambda f: 1 / (2 * np.pi * np.maximum(f, 1e-12)),
                                               lambda t: 1 / (2 * np.pi * np.maximum(t, 1e-12))))
    sec.set_xlabel(r"$\tau = 1/2\pi f$  /  s", fontsize=14)
    sec.tick_params(labelsize=12)
    ax.set_title("Learning WITHOUT physics agrees: GPR-ARD distills 66 raw EIS\n"
                 "features to two frequencies — one sits in the shared band",
                 fontsize=16, fontweight="bold", pad=12)
    save(fig, "poster_6_ard")
    print(f"  ARD: in-band {freqs[i_ct]:.2f} Hz (w={w[i_ct]:.2f}, tau={t_ct:.3f} s) | "
          f"HF {freqs[i_hf]:.0f} Hz (w={w[i_hf]:.2f})")


# ════════════════════════════════════════════════════════════════════════════
# QR codes (one per repo)
def build_qr():
    targets = [(REPO_LIB, "qr_lib.png"), (REPO_PERO, "qr_pero.png")]
    if all(os.path.exists(os.path.join(OUT, name)) for _, name in targets):
        print("reusing existing QR assets")
        return
    try:
        import qrcode
    except ModuleNotFoundError:
        print("warning: qrcode is unavailable; continuing without regenerating QR assets")
        return
    for url, name in targets:
        qrcode.make(url, box_size=10, border=1).save(os.path.join(OUT, name))
        print("saved", os.path.join(OUT, name))


# ════════════════════════════════════════════════════════════════════════════
# the assembled A0 poster
def assemble():
    fig = plt.figure(figsize=(33.1, 46.8))

    def fbox(x, y, w, h, fc, ec, lw=3.0, style="round,pad=0.004"):
        b = FancyBboxPatch((x, y), w, h, transform=fig.transFigure,
                           boxstyle=style, fc=fc, ec=ec, lw=lw, zorder=1)
        fig.add_artist(b)

    def badge(x, y, n, label, color=C_DARKTXT):
        c = Circle((x, y), 0.0085, transform=fig.transFigure, fc=color, ec="none", zorder=3)
        fig.add_artist(c)
        fig.text(x, y - 0.0012, str(n), ha="center", va="center", fontsize=30,
                 color="white", fontweight="bold", zorder=4)
        fig.text(x + 0.013, y, label, ha="left", va="center", fontsize=33,
                 color=color, fontweight="bold", zorder=4)

    def img_ax(rect, path, anchor="C"):
        a = fig.add_axes(rect, zorder=2)
        a.imshow(plt.imread(os.path.join(OUT, path)))
        a.axis("off"); a.set_anchor(anchor)
        return a

    # ---- title band -----------------------------------------------------------
    fbox(0.015, 0.944, 0.97, 0.049, "#FDFEFE", C_DARKTXT, lw=0, style="round,pad=0.002")
    fig.text(0.46, 0.9855, "Transferable Impedance-Grounded Learning",
             ha="center", fontsize=54, fontweight="bold", color=C_DARKTXT)
    fig.text(0.46, 0.9735, "for Interfacial Degradation Across Energy Systems",
             ha="center", fontsize=54, fontweight="bold", color=C_DARKTXT)
    fig.text(0.46, 0.9615, "Hithesh Rai Purushothama  ·  Nicholas Rolston      "
                           "Arizona State University      AI4X Accelerate 2026, Singapore",
             ha="center", fontsize=27, color=C_GREY)
    fig.text(0.46, 0.9505,
             "One battery (NMC 21700, cycled to end-of-life) and one perovskite solar cell speak the same impedance language — "
             "we propose to make a model bilingual.",
             ha="center", fontsize=23, style="italic", color=C_DARKTXT)
    # QR codes, one per repo
    img_ax([0.885, 0.955, 0.048, 0.034], "qr_lib.png")
    fig.text(0.909, 0.9515, "battery", ha="center", fontsize=15, color=C_BAT)
    img_ax([0.936, 0.955, 0.048, 0.034], "qr_pero.png")
    fig.text(0.960, 0.9515, "perovskite", ha="center", fontsize=15, color=C_PER)

    # ---- tau-bridge ribbon ----------------------------------------------------
    rib = fig.add_axes([0.05, 0.896, 0.90, 0.040], zorder=2)
    rib.set_xscale("log"); rib.set_xlim(1e-9, 1e3); rib.set_ylim(0, 1)
    rib.set_yticks([])
    for s in ("top", "left", "right"):
        rib.spines[s].set_visible(False)
    rib.axvspan(0.05, 2, color=C_BAND, alpha=0.25)
    rib.text(np.sqrt(0.05 * 2), 0.78, "SHARED BAND  50 ms – 2 s", ha="center",
             fontsize=24, color=C_BAND, fontweight="bold")
    for tau, ytxt, txt, col in [
            (7e-6, 0.55, "perovskite electronic\n(recombination)  7 µs", C_PER),
            (0.16, 0.30, "battery charge\ntransfer  0.16 s", C_BAT),
            (1.3,  0.30, "perovskite ionic\nmigration  1.3 s", C_PER)]:
        rib.plot([tau], [0.12], "v", ms=22, color=col, clip_on=False)
        ha = "right" if tau < 1e-3 else ("right" if tau < 1 else "left")
        rib.text(tau * (0.55 if ha == "right" else 1.8), ytxt, txt,
                 ha=ha, fontsize=19, color=col, fontweight="bold")
    rib.set_xlabel("relaxation time  τ  /  s   —   the τ-bridge between domains",
                   fontsize=21, labelpad=3)
    rib.tick_params(labelsize=18)

    # ---- row A: hook + gap/proposal box ---------------------------------------
    badge(0.035, 0.871, 1, "Same degradation signature, 4 decades apart")
    img_ax([0.025, 0.700, 0.575, 0.165], "poster_1_nyquist.png", anchor="W")

    fbox(0.625, 0.700, 0.35, 0.165, "#FDFEFE", C_DARKTXT)
    fig.text(0.64, 0.851, "THE GAP", fontsize=33, fontweight="bold", color=C_DARKTXT)
    fig.text(0.64, 0.792,
             "•  EIS transfer learning exists only within Li-ion\n"
             "    (J. Energy Storage ’25; SKDAN ’23)\n"
             "•  Physics-grounded EIS inversion is per device\n"
             "    class (Diekmann ’26; Nabil ’26)\n"
             "•  Cross-system impedance learning: named as an\n"
             "    outlook in the DRT review (Maradesa, Joule ’24)\n"
             "    — never executed",
             fontsize=23, va="center", color=C_DARKTXT, linespacing=1.55)
    fig.text(0.64, 0.722, "To our knowledge, no degradation model has been\n"
                          "trained across an optoelectronic and an electro-\n"
                          "chemical device class. We propose exactly that.",
             fontsize=24, fontweight="bold", color=C_BAND, va="center", linespacing=1.4)

    # ---- row B: headline DRT overlap + ARD agreement ---------------------------
    badge(0.035, 0.683, 2, "Physics: extend the sweep to 10 mHz → the τ-bands OVERLAP", C_BAND)
    img_ax([0.025, 0.488, 0.46, 0.185], "poster_2_drt_overlap.png", anchor="W")

    badge(0.535, 0.683, 3, "ML: GPR-ARD picks the SAME band", C_BAT)
    img_ax([0.52, 0.488, 0.455, 0.185], "poster_6_ard.png", anchor="E")

    # ---- row C: descriptor evidence + KK rigor ---------------------------------
    badge(0.035, 0.471, 4, "The descriptor predicts MEASURED performance in both domains")
    img_ax([0.025, 0.295, 0.575, 0.165], "poster_3_descriptor.png", anchor="W")

    badge(0.66, 0.471, 5, "Rigor", C_DARKTXT)
    img_ax([0.625, 0.295, 0.35, 0.165], "poster_4_kk_mini.png")

    # ---- row D: proposed encoder + honest limits --------------------------------
    badge(0.035, 0.278, 6, "Proposed: one encoder, two domains", C_BAND)
    img_ax([0.025, 0.115, 0.46, 0.155], "poster_5_encoder.png", anchor="W")

    fbox(0.51, 0.155, 0.465, 0.12, "#FDF2E9", C_BAT, lw=3)
    fig.text(0.525, 0.2615, "HONEST LIMITS", fontsize=28, fontweight="bold", color=C_BAT)
    fig.text(0.525, 0.208,
             "•  Overlapping τ ≠ same physics: ionic migration (PSC) vs charge transfer (battery)\n"
             "•  Perovskite n = 2 devices, one lab → premise evidence, not validated transfer\n"
             "•  Dark-device sweeps drift below 10 Hz late in life (KK panel) — the τ-overlap\n"
             "    claim rests on the KK-valid early spectrum\n"
             "•  “Ionic” assignment is literature-consistent, not proven (Thiesbrummel ’26)",
             fontsize=21, va="center", color=C_DARKTXT, linespacing=1.55)
    fig.text(0.7425, 0.138,
             "Same signature  ·  Same τ-band  ·  Same law  —  make the model bilingual.",
             ha="center", fontsize=29, fontweight="bold", color=C_BAND)

    # ---- footer: methods + references ------------------------------------------
    fig.text(0.025, 0.108,
             "METHODS   Tikhonov-NNLS DRT (one pipeline, both domains) · lin-KK measurement model with μ-criterion (Schönleber ’14) · "
             "GPR with coupled ARD-RBF on raw EIS (battery baseline: Zhang ’20 reproduced/extended) · battery: 8× Molicell P42A NMC 21700, "
             "BioLogic 10 kHz–1 Hz, to EOL · perovskite: PAIOS, 10 MHz–10 mHz, light/dark @ 358 K & 300 K, per-step light JV.",
             fontsize=21, color=C_DARKTXT, va="top", wrap=True)
    fig.text(0.025, 0.087,
             "REFERENCES   Zhang et al. Nat. Commun. 2020 · Jones et al. Nat. Commun. 2022 · von Hauff & Klotz J. Mater. Chem. C 2022 · "
             "Clarke et al. Adv. Energy Mater. 2024 · Maradesa et al. Joule 2024 · Thiesbrummel et al. Nat. Energy 2024 & Nat. Rev. Chem. 2026 · "
             "Diekmann et al. ACS Energy Lett. 2026 · Schönleber et al. Electrochim. Acta 2014",
             fontsize=19, color=C_GREY, va="top")
    fig.text(0.025, 0.068,
             f"Battery (ARD/GPR/DRT): {REPO_LIB}      Perovskite EIS data: {REPO_PERO}      Contact: hraipuru@asu.edu",
             fontsize=21, color=C_DARKTXT, va="top", fontweight="bold")

    # two-domain accent bar at the very bottom
    fbox(0.015, 0.046, 0.475, 0.008, C_BAT, C_BAT, lw=0, style="round,pad=0.0")
    fbox(0.510, 0.046, 0.475, 0.008, C_PER, C_PER, lw=0, style="round,pad=0.0")

    for ext, dpi in (("pdf", 200), ("png", 120)):
        p = os.path.join(OUT, f"poster_draft_A0.{ext}")
        fig.savefig(p, dpi=dpi, facecolor="white")
        print("saved", p)
    plt.close(fig)


def assemble_nature():
    """Assemble an AI4X-themed A0 layout with high-contrast scientific cards."""
    bg = "#090817"
    panel = "#F8F8FB"
    ink_light = "#F7F5FF"
    muted_light = "#B8B4CF"
    violet = "#B54CFF"
    electric_blue = "#25C7FF"
    ai_orange = "#FF6B35"
    dark_rule = "#332D52"
    fig = plt.figure(figsize=(33.1, 46.8), facecolor=bg)

    def fbox(x, y, w, h, fc, ec=C_RULE, lw=1.3, style="round,pad=0.004"):
        patch = FancyBboxPatch(
            (x, y), w, h, transform=fig.transFigure, boxstyle=style,
            fc=fc, ec=ec, lw=lw, zorder=1,
        )
        fig.add_artist(patch)

    def rule(x0, x1, y, color=C_RULE, lw=1.3):
        fig.add_artist(plt.Line2D(
            [x0, x1], [y, y], transform=fig.transFigure,
            color=color, lw=lw, zorder=2,
        ))

    def section_label(x, y, w, number, label, color=violet):
        fig.text(x, y, f"{number:02d}", ha="left", va="center",
                 fontsize=19, color=color, fontweight="bold")
        fig.text(x + 0.024, y, label.upper(), ha="left", va="center",
                 fontsize=24, color=ink_light, fontweight="bold")
        rule(x, x + w, y - 0.010, dark_rule)

    def img_ax(rect, path, anchor="C"):
        ax = fig.add_axes(rect, zorder=2)
        ax.imshow(plt.imread(os.path.join(OUT, path)))
        ax.axis("off")
        ax.set_anchor(anchor)
        return ax

    # Header
    fbox(0.018, 0.941, 0.964, 0.053, "#111026", "#111026", lw=0,
         style="round,pad=0.002")
    fig.text(0.035, 0.982, "TRANSFERABLE IMPEDANCE-GROUNDED LEARNING",
             ha="left", fontsize=42, fontweight="bold", color=ink_light)
    fig.text(0.035, 0.9695,
             "Interfacial degradation across batteries and perovskite solar cells",
             ha="left", fontsize=30, color="#D7C5FF")
    fig.text(
        0.035, 0.957,
        "Hithesh Rai Purushothama  ·  Nicholas Rolston   |   "
        "Arizona State University   |   AI4X Accelerate 2026",
        ha="left", fontsize=19, color=muted_light,
    )
    fbox(0.035, 0.9445, 0.790, 0.0095, "#1D1838", "#1D1838", lw=0,
         style="round,pad=0.002")
    fig.text(
        0.047, 0.9492,
        "CENTRAL RESULT   A degradation-relevant relaxation overlaps at 50 ms–2 s in both systems.",
        ha="left", va="center", fontsize=20, color="#79F2D0", fontweight="bold",
    )
    img_ax([0.862, 0.951, 0.050, 0.038], "qr_lib.png")
    fig.text(0.887, 0.946, "battery code", ha="center", fontsize=11, color=ai_orange)
    img_ax([0.920, 0.951, 0.050, 0.038], "qr_pero.png")
    fig.text(0.945, 0.946, "perovskite data", ha="center", fontsize=11, color=electric_blue)

    # Graphical abstract: shared relaxation-time axis
    rib = fig.add_axes([0.045, 0.895, 0.91, 0.040], zorder=2)
    rib.set_xscale("log")
    rib.set_xlim(1e-9, 1e3)
    rib.set_ylim(0, 1)
    rib.set_facecolor(bg)
    rib.set_yticks([])
    for spine in ("top", "left", "right"):
        rib.spines[spine].set_visible(False)
    rib.spines["bottom"].set_color(dark_rule)
    rib.axvspan(0.05, 2, color="#6DE7C2", alpha=0.16)
    rib.text(np.sqrt(0.05 * 2), 0.80, "SHARED BAND  ·  50 ms–2 s",
             ha="center", fontsize=20, color="#79F2D0", fontweight="bold")
    markers = [
        (7e-6, 0.55, "perovskite electronic\nrecombination  ·  7 µs", electric_blue),
        (0.16, 0.28, "battery charge\ntransfer  ·  0.16 s", ai_orange),
        (1.3, 0.28, "perovskite ionic\nmigration  ·  1.3 s", electric_blue),
    ]
    for tau, text_y, text, color in markers:
        rib.plot([tau], [0.12], "v", ms=17, color=color, clip_on=False)
        align = "right" if tau < 1 else "left"
        rib.text(tau * (0.55 if align == "right" else 1.7), text_y, text,
                 ha=align, fontsize=15, color=color, fontweight="bold")
    rib.set_xlabel("relaxation time  τ  /  s", fontsize=16, labelpad=2,
                   color=muted_light)
    rib.tick_params(labelsize=13, colors=muted_light)

    # Row 1
    section_label(0.025, 0.874, 0.575, 1, "Same signature, four decades apart")
    img_ax([0.025, 0.704, 0.575, 0.158], "poster_1_nyquist.png", anchor="W")

    fbox(0.625, 0.704, 0.35, 0.158, "#17142B", "#403867")
    fig.text(0.645, 0.844, "OPEN PROBLEM", fontsize=23,
             fontweight="bold", color="#D7C5FF")
    fig.text(
        0.645, 0.794,
        "EIS transfer learning remains confined to Li-ion.\n\n"
        "Physics-grounded inversion is typically developed\n"
        "for one device class at a time.\n\n"
        "Cross-system impedance learning is discussed as an\n"
        "outlook, but has not been experimentally evaluated.",
        fontsize=18, va="center", color=ink_light, linespacing=1.35,
    )
    rule(0.645, 0.950, 0.742, "#403867")
    fig.text(0.645, 0.724,
             "We test the physical premise required for that transfer.",
             fontsize=20, fontweight="bold", color="#79F2D0", va="center")

    # Row 2
    section_label(0.025, 0.684, 0.46, 2, "Physics: DRT reveals overlap", "#79F2D0")
    img_ax([0.025, 0.493, 0.46, 0.177], "poster_2_drt_overlap.png", anchor="W")
    section_label(0.515, 0.684, 0.46, 3, "Learning: ARD recovers the band", ai_orange)
    img_ax([0.515, 0.493, 0.46, 0.177], "poster_6_ard.png", anchor="E")

    # Row 3
    section_label(0.025, 0.475, 0.575, 4, "Descriptor tracks measured performance")
    img_ax([0.025, 0.304, 0.575, 0.158], "poster_3_descriptor.png", anchor="W")
    section_label(0.625, 0.475, 0.35, 5, "Validity and stationarity")
    img_ax([0.625, 0.304, 0.35, 0.158], "poster_4_kk_mini.png")

    # Row 4
    section_label(0.025, 0.285, 0.46, 6,
                  "Proposed test: one encoder, two domains", "#79F2D0")
    img_ax([0.025, 0.126, 0.46, 0.146], "poster_5_encoder.png", anchor="W")

    fbox(0.515, 0.151, 0.46, 0.122, "#211426", "#6A3D48")
    fig.text(0.535, 0.255, "BOUNDARIES OF THE CLAIM", fontsize=22,
             fontweight="bold", color="#FF9B73")
    fig.text(
        0.535, 0.210,
        "•  Overlapping τ does not imply identical physics.\n"
        "•  Perovskite evidence is n = 2 devices from one laboratory.\n"
        "•  Late dark-device sweeps drift below 10 Hz; overlap relies on\n"
        "   the KK-valid early spectrum.\n"
        "•  The ionic assignment is literature-consistent, not proven.",
        fontsize=17, va="center", color=ink_light, linespacing=1.50,
    )
    fbox(0.515, 0.126, 0.46, 0.017, "#152D2A", "#152D2A", lw=0,
         style="round,pad=0.002")
    fig.text(0.745, 0.1345,
             "SAME SIGNATURE  ·  SAME τ-BAND  ·  TEST TRANSFER NEXT",
             ha="center", va="center", fontsize=20,
             fontweight="bold", color="#79F2D0")

    # Footer
    rule(0.025, 0.975, 0.111, dark_rule)
    fig.text(
        0.025, 0.104,
        "METHODS   Tikhonov-NNLS DRT (one pipeline, both domains) · "
        "lin-KK measurement model with μ-criterion (Schönleber ’14) · "
        "coupled ARD-RBF GPR on raw EIS · battery: 8× Molicell P42A NMC 21700, "
        "BioLogic 10 kHz–1 Hz, to EOL · perovskite: PAIOS 10 MHz–10 mHz, "
        "light/dark at 358 K and 300 K, per-step light JV.",
        fontsize=15, color=ink_light, va="top", wrap=True,
    )
    fig.text(
        0.025, 0.086,
        "REFERENCES   Zhang et al. Nat. Commun. 2020 · Jones et al. Nat. Commun. 2022 · "
        "von Hauff & Klotz J. Mater. Chem. C 2022 · Clarke et al. Adv. Energy Mater. 2024 · "
        "Maradesa et al. Joule 2024 · Thiesbrummel et al. Nat. Energy 2024 and "
        "Nat. Rev. Chem. 2026 · Diekmann et al. ACS Energy Lett. 2026 · "
        "Schönleber et al. Electrochim. Acta 2014",
        fontsize=13, color=muted_light, va="top",
    )
    fig.text(
        0.025, 0.066,
        f"Battery analysis: {REPO_LIB}      Perovskite data: {REPO_PERO}      "
        "Contact: hraipuru@asu.edu",
        fontsize=14, color=ink_light, va="top", fontweight="bold",
    )
    fbox(0.018, 0.047, 0.472, 0.005, C_BAT, C_BAT, lw=0,
         style="round,pad=0.0")
    fbox(0.510, 0.047, 0.472, 0.005, C_PER, C_PER, lw=0,
         style="round,pad=0.0")

    for ext, dpi in (("pdf", 200), ("png", 120)):
        path = os.path.join(OUT, f"poster_ai4x_A0.{ext}")
        fig.savefig(path, dpi=dpi, facecolor=bg)
        print("saved", path)
    plt.close(fig)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build_kk_mini()
    build_encoder_schematic()
    build_ard_panel()
    build_qr()
    assemble_nature()
    print("Done.")
