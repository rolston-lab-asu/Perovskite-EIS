"""
Parse perovskite PAIOS exports from DataForHitesh.zip (2 devices x 2 temps).

Folder layout (one folder per measurement cycle):
  85c-temp-light/  light-t358-k[-N]  light-aged device @ 358 K
                     - 50 fast spectra (35 pts, 10 MHz - 10 Hz), Apr 14, ~16 min cadence
                     - 22 full spectra (90 pts, 10 MHz - 10 mHz), May 12-19, ~7.2 h cadence
                   dark-t358-k[-N]   dark-control device @ 358 K, 22 full spectra
  test/            light-t300-k[-N] / dark-t300-k[-N]  @ 300 K, 48 each (35 pts), Feb 11-12

Each folder: 11-jv-basic_1d.txt (pre-IS JV summary at 0/50/100% light intensity),
33-is_1d.txt (impedance sweep), 44-jv-basic_1d.txt (post-IS JV summary).
"light"/"dark" = DEVICE identity (from the '# Device:' header), not measurement condition.

Splits folders into 5 series, orders each by the 'Measured between' start timestamp
(folder name suffix is NOT chronological), and saves one npz per series:
  freqs (n_f), Re (n_f, n_t), Im (n_f, n_t), t_hours (n_t),
  jsc/voc/pmax/ff (n_t, from pre-IS JV at 100% intensity), rp (arc diameter)
"""
import os
import re
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = r"C:\Users\hithe\Downloads\Perovskite EIS\DataForHitesh"
OUT_DATA = r"crossdomain\data\perovskite"
OUT_FIG = r"crossdomain\output"
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_FIG, exist_ok=True)

# IS columns (0-indexed): 0 freq, 17 Re(Z), 18 Im(Z)
# JV-1d columns: 0 light intensity (0/0.5/1), 5 Jsc(A), 6 Voc(V), 9 Pmpp(W), 10 FF


def parse_paios(path):
    """Return (header_dict, data_array) for a PAIOS _1d export."""
    hdr, rows = {}, []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#"):
                m = re.search(r"Measured between (.+?) and", s)
                if m:
                    hdr["start"] = datetime.strptime(m.group(1).strip(),
                                                     "%m/%d/%Y, %I:%M %p")
                m = re.search(r"# Device: (.+)", s)
                if m:
                    hdr["device"] = m.group(1).strip()
                continue
            if not s:
                continue
            try:
                rows.append([float(p) for p in s.split("\t")])
            except ValueError:
                continue
    return hdr, np.array(rows)


def classify(group, folder, n_pts):
    """Map a measurement folder to a series key, or None to skip."""
    if group == "85c-temp-light":
        if folder.startswith("light"):
            return "l358_fast" if n_pts == 35 else "l358_full"
        if folder.startswith("dark"):
            return "d358_full"
    else:  # test
        if folder.startswith("light"):
            return "l300"
        if folder.startswith("dark"):
            return "d300"
    return None  # stragglers: 'test', '1-t300-k*', '2-t300-k'


# ---- walk folders ------------------------------------------------------------
series = {}  # key -> list of dicts
for group in ("85c-temp-light", "test"):
    for folder in sorted(os.listdir(os.path.join(SRC, group))):
        fdir = os.path.join(SRC, group, folder)
        is_path = os.path.join(fdir, "33-is_1d.txt")
        if not os.path.isdir(fdir) or not os.path.exists(is_path):
            continue
        hdr, dat = parse_paios(is_path)
        start = hdr.get("start")
        if start is None or start.year < 2020:   # broken/epoch timestamps
            print(f"  skip {group}/{folder}: bad timestamp {start}")
            continue
        key = classify(group, folder, dat.shape[0])
        if key is None:
            print(f"  skip {group}/{folder}: unclassified")
            continue
        rec = {"start": start, "folder": folder,
               "freq": dat[:, 0], "re": dat[:, 17], "im": dat[:, 18]}
        # pre-IS JV summary, 100%-intensity row
        jv_path = os.path.join(fdir, "11-jv-basic_1d.txt")
        rec["jv"] = [np.nan] * 4
        if os.path.exists(jv_path):
            _, jv = parse_paios(jv_path)
            full = jv[np.isclose(jv[:, 0], 1.0)]
            if len(full):
                r = full[0]
                # Jsc -> mA (abs), Voc V, Pmpp -> uW, FF
                rec["jv"] = [abs(r[5]) * 1e3, r[6], r[9] * 1e6, r[10]]
        series.setdefault(key, []).append(rec)

# ---- assemble + save ----------------------------------------------------------
LABELS = {"l358_fast": "light dev @358K, fast soak (10 MHz-10 Hz)",
          "l358_full": "light dev @358K, full sweep (10 MHz-10 mHz)",
          "d358_full": "dark dev @358K, full sweep (10 MHz-10 mHz)",
          "l300": "light dev @300K (10 MHz-10 Hz)",
          "d300": "dark dev @300K (10 MHz-10 Hz)"}

npz = {}
for key in ("l358_fast", "l358_full", "d358_full", "l300", "d300"):
    recs = sorted(series[key], key=lambda r: r["start"])
    freqs = recs[0]["freq"]
    for r in recs:
        assert np.allclose(r["freq"], freqs), f"{key}: frequency grid mismatch"
    Re = np.column_stack([r["re"] for r in recs])
    Im = np.column_stack([r["im"] for r in recs])
    t0 = recs[0]["start"]
    t_hours = np.array([(r["start"] - t0).total_seconds() / 3600 for r in recs])
    jv = np.array([r["jv"] for r in recs])           # (n_t, 4)
    rp = Re[-1, :] - Re[0, :]                        # arc diameter LF - HF
    path = os.path.join(OUT_DATA, f"pero_{key}.npz")
    np.savez(path, freqs=freqs, Re=Re, Im=Im, t_hours=t_hours,
             jsc=jv[:, 0], voc=jv[:, 1], pmax=jv[:, 2], ff=jv[:, 3], rp=rp)
    npz[key] = dict(freqs=freqs, Re=Re, Im=Im, t_hours=t_hours, jv=jv, rp=rp)
    print(f"{key}: {Re.shape[1]} spectra x {len(freqs)} freqs "
          f"({freqs[0]:.0e} -> {freqs[-1]:.0e} Hz), span {t_hours[-1]:.1f} h | "
          f"Rp {rp[0]:.0f} -> {rp[-1]:.0f} Ohm | "
          f"Pmax {jv[0, 2]:.0f} -> {jv[-1, 2]:.0f} uW  -> {path}")

# ---- sanity figure -------------------------------------------------------------
fig, axes = plt.subplots(2, 5, figsize=(24, 8.5))
for j, key in enumerate(("l358_fast", "l358_full", "d358_full", "l300", "d300")):
    d = npz[key]
    n_t = d["Re"].shape[1]
    cmap = plt.cm.viridis(np.linspace(0, 1, n_t))
    ax = axes[0, j]
    for k in range(n_t):
        ax.plot(d["Re"][:, k], -d["Im"][:, k], color=cmap[k], lw=0.7, alpha=0.7)
    ax.set_title(f"{LABELS[key]}\nNyquist (viridis early->late)", fontsize=9)
    ax.set_xlabel("Re(Z) / Ohm"); ax.set_ylabel("-Im(Z) / Ohm")

    ax = axes[1, j]
    ax.plot(d["t_hours"], d["rp"] / d["rp"][0], "o-", ms=3, color="darkred",
            label="Rp/Rp0")
    pm = d["jv"][:, 2]
    if np.isfinite(pm).any() and np.nanmax(pm) > 0:
        ax.plot(d["t_hours"], pm / pm[0], "s-", ms=3, color="steelblue",
                label="Pmax/Pmax0")
    ax.set_xlabel("aging time / h"); ax.set_ylabel("relative")
    ax.legend(fontsize=8); ax.set_title("degradation trends", fontsize=9)
plt.tight_layout()
p = os.path.join(OUT_FIG, "sanity_perovskite_v2.png")
fig.savefig(p, dpi=130, bbox_inches="tight")
print(f"Saved {p}")
