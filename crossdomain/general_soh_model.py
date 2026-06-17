"""
"General battery model" card for the poster's SDL / NIMO outlook.

Leave-one-CELL-out cross-validation (LOOCV): a single GPR on raw EIS predicts
state of health for a cell it has NEVER seen, trained only on the other cells.
This is the generalization an autonomous lab needs — one impedance->health model
that transfers to new cells — i.e. the health oracle a NIMO-driven self-driving
loop would optimize against.

Method reused verbatim from run_loocv.py (CA1-CA8 Molicell P42A, joint z-score
normalization to remove cell-to-cell impedance offset, fixed RBF l=30, alpha=0.1).
Capacity is converted to SOH = cap / cap[0] per cell. Predictions are pooled
across all 8 held-out cells into one parity plot.

Run: python -X utf8 crossdomain/general_soh_model.py
Output: crossdomain/output/poster/general_soh_model.png/.pdf
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.metrics import r2_score

DATA = Path(r"battery_gpytorch_rtx4060\battery_gpytorch\data\ca_dataset")
OUT = r"crossdomain\output\poster"
os.makedirs(OUT, exist_ok=True)
C_BAT = "#D55E00"
CELLS = [f"CA{i}" for i in range(1, 9)]
L_CAP = 30.0

plt.rcParams.update({
    "font.size": 16, "axes.labelsize": 18, "xtick.labelsize": 15,
    "ytick.labelsize": 15, "legend.fontsize": 12.5, "axes.linewidth": 1.4,
    "savefig.facecolor": "white", "axes.facecolor": "white", "font.family": "Arial",
    "axes.spines.top": False, "axes.spines.right": False,
})


def zscore(X):
    mu = X.mean(0); sig = np.where(X.std(0, ddof=1) == 0, 1, X.std(0, ddof=1))
    return mu, sig


eis = {c: np.loadtxt(DATA / f"EIS_{c}.txt") for c in CELLS}
cap = {c: np.loadtxt(DATA / f"cap_{c}.txt") for c in CELLS}
soh = {c: cap[c] / cap[c][0] for c in CELLS}          # state of health

meas_all, pred_all, r2s = [], [], []
for test in CELLS:
    train = [c for c in CELLS if c != test]
    EIS_tr = np.vstack([eis[c] for c in train]); Y_tr = np.concatenate([soh[c] for c in train])
    EIS_te = eis[test]; Y_te = soh[test]
    mu, sig = zscore(np.vstack([EIS_tr, EIS_te]))
    Xtr = (EIS_tr - mu) / sig; Xte = (EIS_te - mu) / sig
    k = (ConstantKernel(1.0, "fixed") * RBF(L_CAP, "fixed") + WhiteKernel(1.0))
    gpr = GaussianProcessRegressor(kernel=k, normalize_y=True, alpha=0.1,
                                   n_restarts_optimizer=0).fit(Xtr, Y_tr)
    yp = gpr.predict(Xte)
    r2 = r2_score(Y_te, yp); r2s.append(r2)
    meas_all.append(Y_te); pred_all.append(yp)
    print(f"  {test}: held-out R^2 = {r2:.3f}")

meas_all = np.concatenate(meas_all); pred_all = np.concatenate(pred_all)
mean_r2 = np.mean(r2s); pooled_r2 = r2_score(meas_all, pred_all)
print(f"mean per-cell R^2 = {mean_r2:.3f} | pooled R^2 = {pooled_r2:.3f}")

# ── parity plot ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.0, 6.0), constrained_layout=True)
ax.plot([0, 1], [0, 1], "k--", lw=1.2, zorder=1)
ax.scatter(meas_all, pred_all, s=14, alpha=0.45, color=C_BAT, edgecolors="none", zorder=2)
ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.02)
ax.set_xlabel("measured state of health")
ax.set_ylabel("predicted state of health")
ax.text(0.05, 0.93, fr"mean $R^2$ = {mean_r2:.2f}", transform=ax.transAxes,
        fontsize=22, fontweight="bold", color=C_BAT, va="top")
ax.text(0.05, 0.84, "leave-one-cell-out  (8 cells,\nmodel never saw the test cell)",
        transform=ax.transAxes, fontsize=12.5, color="0.4", va="top")
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"general_soh_model.{ext}"), dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"saved {OUT}\\general_soh_model.png/.pdf")
