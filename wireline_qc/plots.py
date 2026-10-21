"""Multi-track log plots."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import *
from .loaders import runs


def plot_log(w, ev, bad, washout, tops, top, base, path, title, show_tops=True, height=11):
    m = (w.DEPTH >= top) & (w.DEPTH <= base)
    d = w.DEPTH[m]
    e = ev[m]
    fig, ax = plt.subplots(1, 6, figsize=(12, height), sharey=True,
                           gridspec_kw={"width_ratios": [1, 0.7, 1, 1, 0.9, 0.35]})
    gr = w.GR.where(~bad["GR"])[m]
    ax[0].plot(gr, d, color="green", lw=0.7); ax[0].set_xlim(0, 150); ax[0].set_title("GR (API)")
    ax[0].fill_betweenx(d, 0, gr.clip(upper=150), where=gr < 60, color="#f2d64b", alpha=0.4)

    ax[1].plot(w.CALI[m], d, color="black", lw=0.7); ax[1].set_xlim(5, 18); ax[1].set_title("Caliper (in)")
    for s, en in runs(washout[m].values):
        ax[1].axhspan(d.iloc[s], d.iloc[en], color="red", alpha=0.35)

    ax[2].plot(w.RM[m].where(w.RM[m] > 0), d, color="#d98000", lw=0.7, label="RMED")
    ax[2].plot(w.RT.where(~bad["RT"])[m], d, color="red", lw=0.8, label="RDEP")
    ax[2].set_xscale("log"); ax[2].set_xlim(0.2, 2000); ax[2].set_title("Resistivity (ohm.m)")
    ax[2].legend(fontsize=6, loc="lower right")

    rh = w.RHOB.where(~bad["RHOB"])[m]
    ax[3].plot(rh, d, color="crimson", lw=0.7); ax[3].set_xlim(1.95, 2.95)
    ax[3].set_title("RHOB (g/cc) red\nNPHI (v/v) blue", fontsize=9)
    t2 = ax[3].twiny(); t2.plot(w.NPHI.where(~bad["NPHI"])[m], d, color="blue", lw=0.7, ls="--")
    t2.set_xlim(0.45, -0.15); t2.tick_params(labelsize=6)

    ax[4].plot(e.VSH, d, color="saddlebrown", lw=0.8, label="Vsh")
    ax[4].plot(e.PHI, d, color="teal", lw=0.8, label="Phi (N-D)")
    ax[4].set_xlim(0, 1); ax[4].set_title("Vsh and porosity"); ax[4].legend(fontsize=6, loc="lower right")

    ax[5].fill_betweenx(d, 0, 1, where=e.NET.values, color="gold", step="mid")
    ax[5].set_xticks([]); ax[5].set_title("Net")

    # QC markers: excluded main-curve samples
    for c, a, lo, hi in (("GR", ax[0], 0, 150), ("RHOB", ax[3], 1.95, 2.95)):
        bm = bad[c][m] & w[c][m].notna() & ~washout[m]
        if bm.any():
            a.scatter(w[c][m][bm].clip(lo, hi), d[bm], marker="x", color="black", s=14, zorder=5, clip_on=False)

    if show_tops:
        for t in tops.itertuples():
            if top <= t.Top <= base:
                for a in ax:
                    a.axhline(t.Top, color="navy", lw=0.6, ls=":")
                ax[0].text(149, t.Top, t.Formation.replace(" FM", ""), fontsize=6, color="navy",
                           va="bottom", ha="right")
    ax[0].set_ylim(base, top); ax[0].set_ylabel("Depth MD (m)")
    for a in ax:
        a.grid(alpha=0.25)
    fig.suptitle(title, fontweight="bold")
    fig.text(0.5, 0.005, "x = excluded sample   |   red band = washout   |   dotted lines = formation tops   |   "
             "yellow = net (Vsh < %.2f, Phi > %.2f)" % (VSH_CUTOFF, PHI_CUTOFF), ha="center", fontsize=7)
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(path, dpi=120)
    plt.close(fig)


