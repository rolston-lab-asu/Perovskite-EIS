"""
EIS Analysis Script for Perovskite Solar Cell Degradation Study
================================================================
Parses PAIOS Characterization Suite 4.4 EIS export files,
plots Nyquist / Bode spectra, checks time-invariance (consecutive
sweep overlap), and runs Kramers-Kronig (Lin-KK) validation.

Usage
-----
1. Place your PAIOS .txt export file(s) in the data/ folder.
2. Update DATA_DIR and the filenames in main() as needed.
3. Run:  python analysis/analyze_eis.py
4. Figures are saved to data/figures/.

PAIOS Sign Convention
---------------------
PAIOS exports Im(Z) directly in standard EIS convention:
    Im(Z) < 0  for capacitive elements
    Im(Z) > 0  for inductive elements (cable artifact at very high f)
Complex impedance: Z = Z_real + 1j * Z_imag
Nyquist y-axis  : -Im(Z) vs Z_real

Dependencies
------------
    pip install numpy matplotlib impedance

References
----------
- Lazanas & Prodromidis, ACS Meas. Sci. Au 2023, 3, 162 (EIS tutorial)
- Klotz et al., RSC Adv. 2019, 9, 33436 (time-series EIS on PSCs)
- Clarke et al., Adv. Energy Mater. 2024, 14, 2400955 (spectral zoo)
- Ravishankar et al., Energy Environ. Sci. 2024, 17, 1229 (rise time constants)
- Schonleber et al., Electrochim. Acta 2014, 131, 20 (Lin-KK method)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path
from impedance.validation import linKK

# ---------------------------------------------------------------------------
# Configuration — edit these to match your experiment
# ---------------------------------------------------------------------------
DATA_DIR   = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)

# PAIOS IS sweep parameters (read from file header)
F_START_HZ  = 10e6    # Hz — upper frequency limit
F_END_HZ    = 10.0    # Hz — lower frequency limit (extend to 10e-3 ideally)
N_FREQ      = 35      # number of frequency points
TEMPERATURE = 358     # K  (85 C for accelerated degradation study)
AMPLITUDE   = 10e-3   # V  — RECOMMENDED value; update if different


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_paios_eis(filepath, f_start=F_START_HZ, f_end=F_END_HZ):
    """
    Parse a PAIOS EIS export file containing multiple consecutive sweeps.

    PAIOS format
    ------------
    - Header lines start with # or ###
    - Data block starts after '### Data:'
    - Each row  = one frequency point
    - Columns alternate: Z_real(sweep1), Z_imag(sweep1), Z_real(sweep2), ...
    - Im(Z) < 0 for capacitive (standard EIS convention, exported directly)

    Parameters
    ----------
    filepath : str or Path
    f_start  : float, upper frequency in Hz (from PAIOS header)
    f_end    : float, lower frequency in Hz (from PAIOS header)

    Returns
    -------
    frequencies : ndarray, shape (N,)
    sweeps      : list of complex ndarray, each shape (N,)
    n_sweeps    : int
    """
    filepath = Path(filepath)
    data_rows = []
    with open(filepath, "r") as f:
        in_data = False
        for line in f:
            line = line.strip()
            if "### Data:" in line:
                in_data = True
                continue
            if in_data and line and not line.startswith("#"):
                data_rows.append([float(x) for x in line.split()])

    data = np.array(data_rows)
    n_freq, n_cols = data.shape
    n_sweeps = n_cols // 2

    frequencies = np.logspace(np.log10(f_start), np.log10(f_end), n_freq)

    sweeps = []
    for i in range(n_sweeps):
        z_real = data[:, 2 * i]
        z_imag = data[:, 2 * i + 1]
        sweeps.append(z_real + 1j * z_imag)   # standard complex impedance

    print(f"  Loaded : {filepath.name}")
    print(f"  Sweeps : {n_sweeps}   |   Freq points : {n_freq}")
    print(f"  Freq   : {frequencies[-1]:.2g} Hz -- {frequencies[0]:.2g} Hz")
    return frequencies, sweeps, n_sweeps


# ---------------------------------------------------------------------------
# Plot 1 — All Nyquist sweeps coloured by time
# ---------------------------------------------------------------------------

def plot_nyquist_all(frequencies, sweeps, label="EIS"):
    n = len(sweeps)
    colors = cm.plasma(np.linspace(0.05, 0.95, n))

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: full time series
    ax = axes[0]
    for i, (Z, c) in enumerate(zip(sweeps, colors)):
        ax.plot(Z.real, -Z.imag, "-", color=c, lw=0.8,
                alpha=0.6 + 0.4 * (i / n))
    ax.plot(sweeps[0].real,  -sweeps[0].imag,  "o-", color="blue",
            lw=2, ms=4, label="Sweep 1 (t=0)", zorder=5)
    ax.plot(sweeps[-1].real, -sweeps[-1].imag, "s-", color="red",
            lw=2, ms=4, label=f"Sweep {n} (final)", zorder=5)
    sm = plt.cm.ScalarMappable(cmap="plasma",
                                norm=plt.Normalize(vmin=1, vmax=n))
    plt.colorbar(sm, ax=ax, label="Sweep number  ->  Time")
    ax.set_xlabel("Z' (Ohm)")
    ax.set_ylabel("-Z'' (Ohm)")
    ax.set_title(f"{label} -- All {n} sweeps")
    ax.legend()
    ax.grid(True, alpha=0.25)

    # Right: first 3 vs last — time-invariance check
    ax2 = axes[1]
    check = [(0, "blue", "Sweep 1"),
             (1, "royalblue", "Sweep 2"),
             (2, "cornflowerblue", "Sweep 3"),
             (n - 1, "red", f"Sweep {n}")]
    for idx, c, lbl in check:
        Z = sweeps[idx]
        ax2.plot(Z.real, -Z.imag, "o-", color=c, lw=1.8, ms=4, label=lbl)
    ax2.set_xlabel("Z' (Ohm)")
    ax2.set_ylabel("-Z'' (Ohm)")
    ax2.set_title("Time-invariance check: Sweeps 1-3 vs Final")
    ax2.legend()
    ax2.grid(True, alpha=0.25)
    ax2.text(0.02, 0.97,
             "Overlapping 1-3 -> time-invariant\nSeparation -> ionic migration",
             transform=ax2.transAxes, fontsize=8, va="top",
             bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.85))

    plt.tight_layout()
    out = OUTPUT_DIR / f"{label}_nyquist_all.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {out.name}")


# ---------------------------------------------------------------------------
# Plot 2 — Impedance evolution over time at selected frequencies
# ---------------------------------------------------------------------------

def plot_time_evolution(frequencies, sweeps, label="EIS"):
    n = len(sweeps)
    sweep_idx = np.arange(1, n + 1)
    targets = [1e6, 1e5, 1e4, 1e3, 1e2, frequencies[-1]]
    labels  = ["1 MHz", "100 kHz", "10 kHz", "1 kHz", "100 Hz",
               f"{frequencies[-1]:.0f} Hz (lowest)"]
    fidx = [np.argmin(np.abs(frequencies - t)) for t in targets]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()

    for ax, fi, fl in zip(axes, fidx, labels):
        zr = np.array([Z[fi].real  for Z in sweeps])
        zi = np.array([-Z[fi].imag for Z in sweeps])
        ax.plot(sweep_idx, zr, "b-o", ms=3, lw=1.2, label="Z' (real)")
        ax.plot(sweep_idx, zi, "r-s", ms=3, lw=1.2, label="-Z'' (imag)")
        ax.set_xlabel("Sweep number")
        ax.set_ylabel("Impedance (Ohm)")
        ax.set_title(f"f = {fl}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)

    plt.suptitle(f"{label} -- Impedance Evolution Over Time",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    out = OUTPUT_DIR / f"{label}_time_evolution.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {out.name}")


# ---------------------------------------------------------------------------
# Plot 3 — Bode plot
# ---------------------------------------------------------------------------

def plot_bode(frequencies, sweeps, label="EIS"):
    n = len(sweeps)
    selected = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    colors = cm.plasma(np.linspace(0.05, 0.95, len(selected)))

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for idx, c in zip(selected, colors):
        Z = sweeps[idx]
        axes[0].semilogx(frequencies, 20 * np.log10(np.abs(Z)),
                         "-", color=c, lw=1.5, label=f"Sweep {idx+1}")
        axes[1].semilogx(frequencies, np.angle(Z, deg=True),
                         "-", color=c, lw=1.5, label=f"Sweep {idx+1}")

    axes[0].set_ylabel("|Z| (dB Ohm)")
    axes[0].set_title(f"{label} -- Bode Plot (selected sweeps)")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, which="both", alpha=0.25)
    axes[1].set_xlabel("Frequency (Hz)")
    axes[1].set_ylabel("Phase (deg)")
    axes[1].axhline(-45, color="gray", linestyle="--", alpha=0.5, lw=0.8)
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].legend(fontsize=9)

    plt.tight_layout()
    out = OUTPUT_DIR / f"{label}_bode.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {out.name}")


# ---------------------------------------------------------------------------
# Plot 4 — Consecutive sweep comparison (time-invariance test)
# ---------------------------------------------------------------------------

def plot_consecutive_comparison(frequencies, sweeps, label="EIS"):
    n = len(sweeps)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    pairs = [(0, 1, "Beginning (Sweeps 1 & 2)"),
             (n - 2, n - 1, f"End (Sweeps {n-1} & {n})")]

    for ax, (i, j, title) in zip(axes, pairs):
        Z1, Z2 = sweeps[i], sweeps[j]
        ax.plot(Z1.real, -Z1.imag, "b-o",  ms=5, lw=2, label=f"Sweep {i+1}")
        ax.plot(Z2.real, -Z2.imag, "r--s", ms=5, lw=2, label=f"Sweep {j+1}")
        dZ = np.abs(Z1 - Z2) / np.abs(Z1) * 100
        ax.set_xlabel("Z' (Ohm)")
        ax.set_ylabel("-Z'' (Ohm)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.25)
        ax.text(0.02, 0.05,
                f"Mean deviation: {np.mean(dZ):.1f}%\n"
                f"Max  deviation: {np.max(dZ):.1f}%",
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    plt.suptitle(f"{label} -- Consecutive Sweep Overlap Check",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    out = OUTPUT_DIR / f"{label}_consecutive_check.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {out.name}")


# ---------------------------------------------------------------------------
# KK Validation (Lin-KK method, Schonleber et al. 2014)
# ---------------------------------------------------------------------------

def run_kk_validation(frequencies, sweeps, label="EIS"):
    """
    Run Lin-KK on first, mid, and last sweep.
    Acceptance criteria (from Lazanas tutorial):
        max residual < 1%  -> excellent
        max residual < 2%  -> acceptable
        max residual >= 2% -> fail (nonlinear or non-stationary)
    """
    n = len(sweeps)
    validate_idx = sorted(set([0, 1, n // 4, n // 2, 3 * n // 4, n - 1]))
    n_val = len(validate_idx)

    fig, axes = plt.subplots(n_val, 2, figsize=(14, 4.5 * n_val))
    if n_val == 1:
        axes = axes.reshape(1, -1)

    results = []
    for row, idx in enumerate(validate_idx):
        Z = sweeps[idx]
        lbl = f"Sweep {idx+1}"
        try:
            M, mu, Z_fit, res_re, res_im = linKK(
                frequencies, Z, c=0.85, max_M=50,
                fit_type="complex", add_cap=True)

            max_res = max(np.max(np.abs(res_re)),
                         np.max(np.abs(res_im))) * 100
            rms_res = np.sqrt(np.mean(res_re**2 + res_im**2)) * 100

            status = ("PASS (excellent)" if max_res < 1.0
                      else "PASS (acceptable)" if max_res < 2.0
                      else "FAIL")
            results.append(dict(sweep=idx+1, max_res=max_res,
                                rms_res=rms_res, status=status))

            ax1 = axes[row, 0]
            ax1.plot(Z.real, -Z.imag, "bo", ms=5, label="Data")
            ax1.plot(Z_fit.real, -Z_fit.imag, "r-", lw=2, label="Lin-KK fit")
            ax1.set_xlabel("Z' (Ohm)")
            ax1.set_ylabel("-Z'' (Ohm)")
            ax1.set_title(f"{lbl} -- KK Fit  [{status}]")
            ax1.legend()
            ax1.grid(True, alpha=0.25)

            ax2 = axes[row, 1]
            ax2.semilogx(frequencies, res_re * 100, "b-o",
                         ms=4, lw=1.2, label="Real residual")
            ax2.semilogx(frequencies, res_im * 100, "r-s",
                         ms=4, lw=1.2, label="Imag residual")
            ax2.axhspan(-1, 1, alpha=0.12, color="green",
                        label="+-1% band")
            ax2.axhspan(-2, -1, alpha=0.08, color="orange")
            ax2.axhspan(1, 2,  alpha=0.08, color="orange",
                        label="+-2% band")
            ax2.axhline(0, color="black", lw=0.8)
            ax2.set_xlabel("Frequency (Hz)")
            ax2.set_ylabel("Residual (%)")
            ax2.set_title(f"{lbl} -- Residuals  "
                          f"(max={max_res:.2f}%, rms={rms_res:.2f}%)")
            ax2.legend(fontsize=8)
            ax2.grid(True, which="both", alpha=0.25)

        except Exception as e:
            results.append(dict(sweep=idx+1, status=f"ERROR: {e}"))
            axes[row, 0].text(0.5, 0.5, f"KK failed:\n{e}",
                              transform=axes[row, 0].transAxes, ha="center")

    kT_q = 8.617e-5 * TEMPERATURE
    plt.suptitle(
        f"{label} -- Kramers-Kronig Validation\n"
        f"T = {TEMPERATURE} K ({TEMPERATURE-273} C)  |  "
        f"Amplitude = {int(AMPLITUDE*1000)} mV  |  "
        f"kT/q = {kT_q*1000:.1f} mV",
        fontsize=12, fontweight="bold")
    plt.tight_layout()
    out = OUTPUT_DIR / f"{label}_kk_validation.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {out.name}")

    # Summary
    print("\n" + "-" * 58)
    print(f"  KK Validation Summary -- {label}")
    print("-" * 58)
    print(f"  {'Sweep':>8}  {'Max res%':>10}  {'RMS res%':>10}  Status")
    print("-" * 58)
    for r in results:
        if "max_res" in r:
            print(f"  {r['sweep']:>8}  {r['max_res']:>10.2f}  "
                  f"{r['rms_res']:>10.2f}  {r['status']}")
        else:
            print(f"  {r['sweep']:>8}  {'--':>10}  {'--':>10}  {r['status']}")
    print("-" * 58)
    print(f"\n  Amplitude : {int(AMPLITUDE*1000)} mV  |  "
          f"kT/q at {TEMPERATURE}K : {kT_q*1000:.1f} mV  |  "
          f"Ratio : {AMPLITUDE/kT_q:.2f}x")
    if AMPLITUDE / kT_q > 1.0:
        print("  WARNING: amplitude > kT/q -> nonlinear response -> "
              "reduce to 10 mV")
    else:
        print("  OK: amplitude < kT/q -> linear regime")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 58)
    print("  Perovskite EIS Analysis")
    print("=" * 58)

    # Dataset 1: Light only
    print("\n[1] EIS Light Only")
    print("-" * 40)
    f1, s1, _ = parse_paios_eis(DATA_DIR / "EISLightonly.txt")
    plot_nyquist_all(f1, s1,            label="LightOnly")
    plot_bode(f1, s1,                   label="LightOnly")
    plot_time_evolution(f1, s1,         label="LightOnly")
    plot_consecutive_comparison(f1, s1, label="LightOnly")
    run_kk_validation(f1, s1,           label="LightOnly")

    # Dataset 2: Light + Dark
    print("\n[2] EIS Light + Dark")
    print("-" * 40)
    f2, s2, _ = parse_paios_eis(DATA_DIR / "EISlightDark.txt")
    plot_nyquist_all(f2, s2,            label="LightDark")
    plot_bode(f2, s2,                   label="LightDark")
    plot_time_evolution(f2, s2,         label="LightDark")
    plot_consecutive_comparison(f2, s2, label="LightDark")
    run_kk_validation(f2, s2,           label="LightDark")

    print(f"\n  All figures saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
