"""Basic formation evaluation: Vsh, porosity, net rock, per-formation summary."""
import numpy as np
import pandas as pd

from .config import *
from .loaders import runs


def evaluate(w, bad, tops):
    ev = w.copy()
    for c in MAIN:
        ev[c] = ev[c].where(~bad[c])
    ev[["GR", "RHOB", "NPHI", "RT"]] = ev[["GR", "RHOB", "NPHI", "RT"]].interpolate(limit=MAX_FILL)

    gr0, gr1 = np.nanpercentile(ev.GR, GR_CLEAN_PCT), np.nanpercentile(ev.GR, GR_SHALE_PCT)
    igr = ((ev.GR - gr0) / (gr1 - gr0)).clip(0, 1)
    ev["VSH"] = (0.33 * (2 ** (2 * igr) - 1)).clip(0, 1)           # Larionov (older rocks)

    ev["FORMATION"] = ""
    ev["MATRIX"] = MATRIX["sand"]
    for t in tops.itertuples():
        m = (ev.DEPTH >= t.Top) & (ev.DEPTH < t.Base)
        ev.loc[m, "FORMATION"] = t.Formation
        if t.Formation in CHALK:
            ev.loc[m, "MATRIX"] = MATRIX["chalk"]
    ev["PHID"] = ((ev.MATRIX - ev.RHOB) / (ev.MATRIX - FLUID_DENSITY)).clip(0, 0.45)
    ev["PHIN"] = ev.NPHI.clip(0, 0.45)
    ev["PHI"] = np.sqrt((ev.PHID ** 2 + ev.PHIN ** 2) / 2)            # neutron-density average
    ev["VALID"] = ev[["GR", "RHOB", "NPHI"]].notna().all(axis=1)
    ev["NET"] = ev.VALID & (ev.VSH < VSH_CUTOFF) & (ev.PHI > PHI_CUTOFF)
    ev["RT_IND"] = ev.NET & (ev.RT > RT_INDICATOR)
    step = float(np.median(np.diff(ev.DEPTH)))

    rows = []
    for t in tops.itertuples():
        m = ev.FORMATION == t.Formation
        z = ev[m]
        v = z[z.VALID]
        rows.append(dict(Formation=t.Formation, Top=round(t.Top, 1), Base=round(t.Base, 1),
                         Thickness=round(t.Base - t.Top, 1), Valid_pct=round(100 * z.VALID.mean(), 0),
                         GR_mean=round(v.GR.mean(), 0) if len(v) else np.nan,
                         Vsh_mean=round(v.VSH.mean(), 2) if len(v) else np.nan,
                         Phi_mean=round(v.PHI.mean(), 3) if len(v) else np.nan,
                         RT_median=round(v.RT.median(), 1) if len(v) else np.nan,
                         Net_m=round(z.NET.sum() * step, 1),
                         NTG=round(z.NET.sum() / max(z.VALID.sum(), 1), 2)))
    zones = pd.DataFrame(rows)
    return ev, zones, (gr0, gr1), step


def net_intervals(ev, formation, step, min_m=0.5):
    z = ev[ev.FORMATION == formation].reset_index(drop=True)
    out = []
    for s, e in runs(z.NET.values):
        th = (e - s + 1) * step
        if th >= min_m:
            seg = z.iloc[s:e + 1]
            out.append(dict(Top=round(z.DEPTH[s], 1), Base=round(z.DEPTH[e] + step, 1), Thickness=round(th, 1),
                            Vsh=round(seg.VSH.mean(), 2), Phi=round(seg.PHI.mean(), 3),
                            RT=round(seg.RT.median(), 1),
                            Indicator="RT > %g ohm.m" % RT_INDICATOR if seg.RT_IND.mean() > 0.5 else "-"))
    return pd.DataFrame(out)


