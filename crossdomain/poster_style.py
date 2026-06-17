"""
Single source of truth for AI4X poster card styling.

Every card script imports RC + PAL from here so the assembled poster reads as
one designed unit (consistent font, tick, line weight, palette). Tweak once,
re-run the cards, and the whole poster updates.

Usage in a card script (runs from repo root):
    import sys; sys.path.insert(0, r"crossdomain")
    from poster_style import RC, PAL
    plt.rcParams.update(RC)
"""

# Okabe-Ito-derived two-domain palette (battery = vermillion, perovskite =
# violet, shared band = gold) + neutral inks. Matches the hero Nyquist ramps.
PAL = {
    "bat":  "#D55E00",   # Li-ion battery
    "per":  "#7C4DCB",   # perovskite solar cell
    "band": "#C79100",   # shared relaxation-time band / accents
    "ink":  "#202124",   # body text / axes
    "grey": "#6B7280",   # secondary text
    "rule": "#D9DEE3",   # dividers / light rules
    "bat_dark": "#2B0A02",
    "per_dark": "#170A2C",
    "wire": "#3A3A3A",    # circuit schematic wires
}

# Canonical Matplotlib rcParams shared by all cards. Point sizes are absolute,
# so for consistent text on the poster place each card at a width proportional
# to its figure width (see POSTER_LAYOUT.md).
RC = {
    "font.family": "Arial",
    "font.size": 16,
    "axes.labelsize": 18,
    "axes.titlesize": 17,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 13.5,
    "axes.linewidth": 1.4,
    "xtick.major.width": 1.4,
    "ytick.major.width": 1.4,
    "xtick.major.size": 5.5,
    "ytick.major.size": 5.5,
    "lines.linewidth": 2.2,
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
}
