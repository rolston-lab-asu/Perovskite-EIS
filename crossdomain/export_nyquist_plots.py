"""Export separate poster-ready Nyquist plots for battery and perovskite data."""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BATTERY_DIR = ROOT / "battery_gpytorch_rtx4060" / "battery_gpytorch"
sys.path.insert(0, str(BATTERY_DIR))

from run_drt_molicell import load_cell


OUT = Path(__file__).resolve().parent / "output" / "poster" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

TEXT = "#172033"
GRID = "#D8DCE3"

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 18,
    "axes.labelsize": 23,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "axes.linewidth": 1.4,
    "xtick.major.width": 1.3,
    "ytick.major.width": 1.3,
    "xtick.major.size": 6,
    "ytick.major.size": 6,
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
})


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(TEXT)
    ax.spines["bottom"].set_color(TEXT)
    ax.tick_params(colors=TEXT)
    ax.grid(True, color=GRID, linewidth=0.7, alpha=0.55)
    ax.set_axisbelow(True)


def save(fig, name):
    for ext in ("png", "pdf"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        print("saved", path)
    plt.close(fig)


def battery_plot():
    eis, _, _, soh = load_cell("CA7")
    re_z, im_z = eis[:, :33], eis[:, 33:]
    n = len(soh)
    colors = plt.cm.viridis(np.linspace(0, 1, n))

    fig, ax = plt.subplots(figsize=(7.4, 6.2), constrained_layout=True)
    for i in range(n):
        ax.plot(re_z[i] * 1e3, -im_z[i] * 1e3,
                color=colors[i], linewidth=1.15, alpha=0.78)

    ax.set_xlabel(r"Re$(Z)$ / m$\Omega$", color=TEXT)
    ax.set_ylabel(r"$-$Im$(Z)$ / m$\Omega$", color=TEXT)
    style_axes(ax)

    sm = plt.cm.ScalarMappable(
        cmap="viridis",
        norm=plt.Normalize(vmin=float(soh.min()), vmax=float(soh.max())),
    )
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.048, pad=0.025)
    cb.set_label("State of health", fontsize=19, color=TEXT)
    cb.ax.tick_params(labelsize=16, colors=TEXT)
    cb.outline.set_linewidth(1.0)
    save(fig, "nyquist_battery_CA7")


def perovskite_plot():
    data = np.load(
        Path(__file__).resolve().parent
        / "data" / "perovskite" / "pero_l358_fast.npz"
    )
    re_z, im_z = data["Re"], data["Im"]
    time_h = data["t_hours"]
    n = len(time_h)
    colors = plt.cm.viridis(np.linspace(0, 1, n))

    fig, ax = plt.subplots(figsize=(7.4, 6.2), constrained_layout=True)
    for i in range(n):
        ax.plot(re_z[:, i], -im_z[:, i],
                color=colors[i], linewidth=1.35, alpha=0.82)

    ax.set_xlabel(r"Re$(Z)$ / $\Omega$", color=TEXT)
    ax.set_ylabel(r"$-$Im$(Z)$ / $\Omega$", color=TEXT)
    style_axes(ax)

    sm = plt.cm.ScalarMappable(
        cmap="viridis",
        norm=plt.Normalize(vmin=float(time_h.min()), vmax=float(time_h.max())),
    )
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.048, pad=0.025)
    cb.set_label("Aging time / h", fontsize=19, color=TEXT)
    cb.ax.tick_params(labelsize=16, colors=TEXT)
    cb.outline.set_linewidth(1.0)
    save(fig, "nyquist_perovskite_358K")


if __name__ == "__main__":
    battery_plot()
    perovskite_plot()
