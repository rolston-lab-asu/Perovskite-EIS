"""
AI4X 2026 poster — assembled as a single clear WORKFLOW (Nick's review of v17).

Three boxed steps, both domains (battery = orange, perovskite = purple) running
in parallel through every step, for a non-ECS audience:

  (1) MEASURE EIS          two Nyquist hooks, arc grows as the device ages
  (2) READ THE SPECTRUM    two ways to find the SAME interfacial process:
                             - equivalent-circuit model  (textbook)
                             - distribution of relaxation times  (model-free),
                               incl. the explicit EIS->DRT extraction schematic
  (3) DESCRIPTOR -> DEGRADATION   one impedance descriptor predicts measured
                                  SOH (battery) and Pmax retention (perovskite)

Embeds the existing 300-dpi cards inside native boxes/arrows/headers so the
section formatting is clean and consistent. Dropped vs v17: battery-only
Arrhenius panel, SDL/NIMO card, the "10 Hz cutoff" DRT annotation.

Run (repo root, venv): python -X utf8 crossdomain/workflow_assembly.py
Output: crossdomain/output/poster/workflow_A0.png/.pdf
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)

C_BAT, C_PER, C_BAND = "#D55E00", "#7C4DCB", "#C79100"
C_INK, C_GREY, C_RULE = "#202124", "#6B7280", "#D9DEE3"
REPO_LIB = "https://github.com/rolston-lab-asu/LIB-EIS-ML"
REPO_PERO = "https://github.com/rolston-lab-asu/Perovskite-EIS"

plt.rcParams.update({"font.family": "Arial", "savefig.facecolor": "white"})

fig = plt.figure(figsize=(33.1, 46.8))


def fbox(x, y, w, h, fc="#FDFEFE", ec=C_INK, lw=3.0, style="round,pad=0.006"):
    fig.add_artist(FancyBboxPatch((x, y), w, h, transform=fig.transFigure,
                                  boxstyle=style, fc=fc, ec=ec, lw=lw, zorder=1))


def header(x, y, num, text, color):
    fig.text(x, y, num, ha="left", va="center", fontsize=46,
             fontweight="bold", color=color, zorder=4)
    fig.text(x + 0.034, y, text, ha="left", va="center", fontsize=34,
             fontweight="bold", color=C_INK, zorder=4)


def varrow(x, y0, y1):
    fig.add_artist(FancyArrowPatch((x, y0), (x, y1), transform=fig.transFigure,
                                   arrowstyle="-|>", mutation_scale=46,
                                   lw=4.5, color=C_BAND, zorder=5))


def img(rect, path, anchor="C"):
    a = fig.add_axes(rect, zorder=2)
    a.imshow(plt.imread(os.path.join(OUT, path)))
    a.axis("off"); a.set_anchor(anchor)
    return a


def domain_tag(x, y, text, color):
    fig.text(x, y, text, ha="center", va="center", fontsize=24,
             fontweight="bold", color=color, zorder=4)


# ── title ─────────────────────────────────────────────────────────────────────
fig.text(0.5, 0.982, "Transferable Impedance-Grounded Learning for",
         ha="center", fontsize=58, fontweight="bold", color=C_INK)
fig.text(0.5, 0.969, "Interfacial Degradation Across Energy Systems",
         ha="center", fontsize=58, fontweight="bold", color=C_INK)
fig.text(0.5, 0.956,
         "Hithesh Rai Purushothama  ·  Nicholas Rolston    ·    "
         "Arizona State University    ·    AI4X Accelerate 2026",
         ha="center", fontsize=28, color=C_GREY)
fig.text(0.5, 0.945,
         "One question:  can a battery and a perovskite solar cell be read with the "
         "SAME impedance workflow, even 10,000× apart in scale?",
         ha="center", fontsize=27, style="italic", fontweight="bold", color=C_BAND)

# ── BOX 1 — measure ───────────────────────────────────────────────────────────
fbox(0.035, 0.745, 0.93, 0.185)
header(0.052, 0.912, "1", "MEASURE EIS  —  the interfacial arc grows as each device ages",
       C_BAND)
img([0.055, 0.755, 0.43, 0.135], "perovskite_nyquist_card.png", anchor="W")
img([0.515, 0.755, 0.43, 0.135], "battery_nyquist_card.png", anchor="E")
domain_tag(0.27, 0.90, "Perovskite solar cell   (Ω scale)", C_PER)
domain_tag(0.73, 0.90, "Li-ion battery  NMC 21700   (mΩ scale)", C_BAT)

varrow(0.5, 0.742, 0.717)

# ── BOX 2 — read the spectrum ─────────────────────────────────────────────────
fbox(0.035, 0.300, 0.93, 0.415)
header(0.052, 0.697, "2",
       "READ THE SPECTRUM  —  two routes find the SAME interfacial process", C_BAND)
# column divider + labels
fig.add_artist(plt.Line2D([0.503, 0.503], [0.315, 0.672], transform=fig.transFigure,
                          color=C_RULE, lw=2.5, zorder=3))
fig.text(0.268, 0.676, "Equivalent-circuit model  (textbook)",
         ha="center", fontsize=26, fontweight="bold", color=C_INK)
fig.text(0.737, 0.676, "Distribution of relaxation times  (model-free)",
         ha="center", fontsize=26, fontweight="bold", color=C_INK)
# left column: ECM fits, both domains
img([0.050, 0.490, 0.42, 0.175], "ecm_perovskite_card.png", anchor="N")
img([0.050, 0.312, 0.42, 0.165], "ecm_battery_card.png", anchor="N")
# right column: EIS->DRT extraction schematic, then the overlap
img([0.515, 0.560, 0.455, 0.105], "drt_extraction_card.png", anchor="N")
img([0.560, 0.315, 0.36, 0.215], "drt_combined_card.png", anchor="N")

varrow(0.5, 0.297, 0.272)

# ── BOX 3 — descriptor ────────────────────────────────────────────────────────
fbox(0.035, 0.110, 0.93, 0.160)
header(0.052, 0.252, "3",
       "THE DESCRIPTOR PREDICTS MEASURED DEGRADATION  —  in BOTH domains", C_BAND)
img([0.080, 0.115, 0.84, 0.125], "poster_3_descriptor.png", anchor="C")

# ── takeaway + footer ─────────────────────────────────────────────────────────
fig.text(0.5, 0.097,
         "Same workflow, same interfacial mechanism, same descriptor → the premise "
         "for a model that learns degradation across both device classes.",
         ha="center", fontsize=29, fontweight="bold", color=C_BAND)
fig.text(0.04, 0.072,
         "METHODS   One pipeline, both domains: EIS → equivalent-circuit fit (R-CPE) "
         "and Tikhonov-NNLS DRT → relaxation time τ → arc descriptor Rp.   "
         "Battery: 8× Molicell P42A NMC 21700, BioLogic 10 kHz–1 Hz, to end-of-life.   "
         "Perovskite: PAIOS, 10 MHz–10 mHz, light @ 358 K, per-step JV.",
         ha="left", va="top", fontsize=20, color=C_INK, wrap=True)
fig.text(0.04, 0.052,
         f"Battery code & data: {REPO_LIB}      Perovskite EIS data: {REPO_PERO}"
         "      Contact: hraipuru@asu.edu",
         ha="left", va="top", fontsize=20, fontweight="bold", color=C_INK)
# two-domain accent bar
fbox(0.035, 0.040, 0.46, 0.006, C_BAT, C_BAT, lw=0, style="round,pad=0.0")
fbox(0.505, 0.040, 0.46, 0.006, C_PER, C_PER, lw=0, style="round,pad=0.0")

for ext, dpi in (("png", 110), ("pdf", 200)):
    p = os.path.join(OUT, f"workflow_A0.{ext}")
    fig.savefig(p, dpi=dpi, facecolor="white")
    print("saved", p)
plt.close(fig)
