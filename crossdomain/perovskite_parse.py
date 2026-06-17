"""
Parse perovskite PAIOS export: aging series under light @ 358 K (85 C).
  - IS  (Cole-Cole): 35 frequencies (10 MHz -> 10 Hz, log) x 50 spectra
  - JV  (Basic):     50 sweeps interleaved over the same ~13 h

Extracts, per aging step:
  - EIS arc diameter Rp = Re(Z)_LF - Re(Z)_HF  (always-available degradation signal)
  - JV metrics Voc, Jsc, Pmax, FF + relative retention (PSC analog of SOH)

Saves clean arrays to crossdomain/data/perovskite/ and a sanity figure.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

PERO = r"C:\Users\hithe\Downloads\Perovskite EIS"
IS_FILE = os.path.join(PERO, "3-is-impedance-cole-cole.txt")
JV_FILE = os.path.join(PERO, "1-jv-basic-jv.txt")
OUT_DATA = r"crossdomain\data\perovskite"
OUT_FIG = r"crossdomain\output"
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_FIG, exist_ok=True)


def read_paios_data(path):
    """Return (n_rows, 100) float array of the numeric block after '### Data:'."""
    rows = []
    in_data = False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip().startswith("### Data:"):
                in_data = True
                continue
            if not in_data:
                continue
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split("\t")
            try:
                rows.append([float(p) for p in parts])
            except ValueError:
                continue
    return np.array(rows)


# ---- EIS -------------------------------------------------------------------
eis = read_paios_data(IS_FILE)          # (35, 100)
n_freq = eis.shape[0]
n_spec = eis.shape[1] // 2
# 35 log-spaced freqs, 10 MHz (row 0, HF) -> 10 Hz (row -1, LF)
freqs = np.logspace(np.log10(1e7), np.log10(10), n_freq)
Re = eis[:, 0::2]                        # (35, 50)
Im = eis[:, 1::2]                        # (35, 50)  PAIOS Im(Z); >0 inductive, <0 capacitive
print(f"EIS: {n_freq} freqs x {n_spec} spectra | f {freqs[0]:.2e} -> {freqs[-1]:.2e} Hz")

# Arc diameter (polarization resistance): low-f Re minus high-f Re per spectrum
Re_hf = Re[0, :]                         # at 10 MHz (series/contact R)
Re_lf = Re[-1, :]                        # at 10 Hz
Rp = Re_lf - Re_hf                       # arc diameter ~ Rrec + Rct
print(f"  Re_HF range {Re_hf.min():.2f}-{Re_hf.max():.2f} Ohm | "
      f"Rp(arc) range {Rp.min():.2f}-{Rp.max():.2f} Ohm")

# ---- JV --------------------------------------------------------------------
jv = read_paios_data(JV_FILE)           # (Npts, 100)
n_jv = jv.shape[1] // 2
print(f"JV: {jv.shape[0]} points x {n_jv} sweeps")

voc, jsc, pmax, ff = [], [], [], []
for k in range(n_jv):
    V = jv[:, 2 * k]
    I = jv[:, 2 * k + 1]                 # mA
    order = np.argsort(V)
    V, I = V[order], I[order]
    # power-generating quadrant: P = -V*I (photocurrent convention I<0 for V>0)
    P = -V * I
    pm = P.max()
    pmax.append(pm)
    # Voc: V at I=0 crossing (interp)
    try:
        sign = np.sign(I)
        idx = np.where(np.diff(sign) != 0)[0]
        if len(idx):
            i0 = idx[-1]
            v_oc = V[i0] - I[i0] * (V[i0 + 1] - V[i0]) / (I[i0 + 1] - I[i0])
        else:
            v_oc = np.nan
    except Exception:
        v_oc = np.nan
    voc.append(v_oc)
    # Jsc: |I| at V=0 (interp)
    j_sc = np.interp(0.0, V, I)
    jsc.append(abs(j_sc))
    vp = V[np.argmax(P)]
    ip = I[np.argmax(P)]
    ff.append(pm / (v_oc * abs(j_sc)) if (v_oc and j_sc) else np.nan)

voc = np.array(voc); jsc = np.array(jsc); pmax = np.array(pmax); ff = np.array(ff)
print(f"  Voc {np.nanmin(voc):.3f}-{np.nanmax(voc):.3f} V | "
      f"Jsc {jsc.min():.3f}-{jsc.max():.3f} mA | "
      f"Pmax {pmax.min():.4f}-{pmax.max():.4f} mW | "
      f"FF {np.nanmin(ff):.3f}-{np.nanmax(ff):.3f}")

# aging-time axis (sweep index -> fraction of run)
step = np.arange(n_spec)
ret_pmax = pmax[:n_spec] / pmax[0] if pmax[0] > 0 else pmax[:n_spec]

# ---- save ------------------------------------------------------------------
np.savez(os.path.join(OUT_DATA, "perovskite_aging.npz"),
         freqs=freqs, Re=Re, Im=Im, Rp=Rp, Re_hf=Re_hf,
         voc=voc, jsc=jsc, pmax=pmax, ff=ff, step=step)
print(f"Saved {OUT_DATA}\\perovskite_aging.npz")

# ---- sanity figure ---------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
cmap = plt.cm.viridis(np.linspace(0, 1, n_spec))
for k in range(n_spec):
    ax[0].plot(Re[:, k], -Im[:, k], color=cmap[k], lw=0.8, alpha=0.7)
ax[0].set_xlabel("Re(Z) / Ohm"); ax[0].set_ylabel("-Im(Z) / Ohm")
ax[0].set_title("Perovskite Nyquist over aging\n(viridis: early->late, light @ 358 K)")

ax[1].plot(step, Rp, "o-", ms=3, color="darkred")
ax[1].set_xlabel("aging step (0->~13 h)"); ax[1].set_ylabel("arc diameter Rp / Ohm")
ax[1].set_title("EIS degradation signal")

ax[2].plot(step, ret_pmax, "s-", ms=3, color="steelblue", label="Pmax retention")
ax[2].plot(step, voc[:n_spec] / voc[0], "^-", ms=3, color="seagreen", label="Voc/Voc0")
ax[2].plot(step, ff[:n_spec] / ff[0], "v-", ms=3, color="darkorange", label="FF/FF0")
ax[2].set_xlabel("aging step"); ax[2].set_ylabel("retention")
ax[2].set_title("JV performance retention"); ax[2].legend(fontsize=8)

plt.tight_layout()
p = os.path.join(OUT_FIG, "sanity_perovskite.png")
fig.savefig(p, dpi=140, bbox_inches="tight")
print(f"Saved {p}")
