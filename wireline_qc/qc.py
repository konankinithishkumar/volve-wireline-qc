"""Data-quality checks: nulls, ranges, spikes, depth steps and hole condition."""
import numpy as np
import pandas as pd

from .config import *
from .loaders import runs


def analysis_window(df):
    """Depth range where all main curves are present (the usable logged interval)."""
    ok = df[MAIN].notna().all(axis=1).values
    s, e = max(runs(ok), key=lambda r: r[1] - r[0])         # longest continuous section
    return df.DEPTH[s], df.DEPTH[e]


def inventory(df, mapping):
    rows = []
    for c in ALL:
        if c not in df:
            continue
        s = df[c].notna()
        rows.append(dict(Curve=c, LAS_mnemonic=mapping[c][0], Unit=mapping[c][1],
                         Top=df.DEPTH[s].min(), Base=df.DEPTH[s].max(), Samples=int(s.sum()),
                         Min=df[c][s].min(), Median=df[c][s].median(), Max=df[c][s].max()))
    return pd.DataFrame(rows)


def run_qc(w):
    """w = data inside the analysis window. Returns flags table + per-curve boolean 'bad' masks."""
    flags = []
    bad = {c: pd.Series(False, index=w.index) for c in ALL if c in w}
    d = w.DEPTH.values

    def add(c, issue, s, e, detail):
        flags.append(dict(Curve=c, Issue=issue, Top=round(d[s], 2), Base=round(d[e], 2),
                          Samples=e - s + 1, Detail=detail))

    for c in bad:
        x = w[c]
        for s, e in runs(x.isna().values):                       # nulls
            add(c, "Missing / null", s, e, f"{e - s + 1} null samples")
            bad[c].iloc[s:e + 1] = True
        lo, hi = VALID_RANGE[c]
        for s, e in runs(((x < lo) | (x > hi)).values):          # out of range
            seg = x.iloc[s:e + 1]
            add(c, "Out of range", s, e, f"min {seg.min():.2f} / max {seg.max():.2f}, valid {lo}-{hi}")
            bad[c].iloc[s:e + 1] = True
        y = np.log10(x.where(~bad[c] & (x > 0))) if c in ("RT", "RM") else x.where(~bad[c])
        med = y.rolling(SPIKE_WINDOW, center=True, min_periods=3).median()
        dev = (y - med).abs()
        scale = max(1.4826 * dev.median(), SPIKE_FLOOR * (y.quantile(0.95) - y.quantile(0.05)))
        thr = SPIKE_SIGMA * scale                                   # floor stops blocky curves over-flagging
        for s, e in runs(((dev > thr) & ~bad[c]).fillna(False).values):   # narrow spikes only
            if e - s + 1 <= SPIKE_MAX_SAMPLES:
                add(c, "Spike", s, e, f"{e - s + 1} sample(s) deviate > {SPIKE_SIGMA:g} robust sigma")
                bad[c].iloc[s:e + 1] = True

    # hole condition: caliper washout invalidates density / neutron (pad / source-detector contact)
    washout = pd.Series(False, index=w.index)
    if "CALI" in w:
        gauge = w.CALI.rolling(WASHOUT_WINDOW, center=True, min_periods=50).median()
        washout = ((w.CALI - gauge) > WASHOUT_DELTA).fillna(False)
        for s, e in runs(washout.values):
            add("CALI", "Washout / enlarged hole", s, e,
                f"caliper up to {w.CALI.iloc[s:e + 1].max():.1f} in vs gauge {gauge.iloc[s:e + 1].median():.1f} in")
        for c in ("RHOB", "NPHI"):
            bad[c] |= washout

    # depth sampling
    step = np.diff(d)
    nominal = float(np.median(step))
    for i in np.where(step > 1.5 * nominal)[0]:
        flags.append(dict(Curve="DEPTH", Issue="Depth gap", Top=round(d[i], 2), Base=round(d[i + 1], 2),
                          Samples=1, Detail=f"{step[i]:.2f} m step vs nominal {nominal:.4f} m"))
    flags = pd.DataFrame(flags)
    if len(flags):
        flags = flags.sort_values(["Top", "Curve"]).reset_index(drop=True)
    return flags, bad, washout, nominal


def qc_summary(flags, w, bad, nominal):
    n = len(w)
    rows = []
    for c in bad:
        f = flags[flags.Curve == c] if len(flags) else flags
        rows.append(dict(Curve=c,
                         Null_pct=round(100 * w[c].isna().mean(), 2),
                         OutOfRange_samples=int(f[f.Issue == "Out of range"].Samples.sum()) if len(f) else 0,
                         Spike_events=int((f.Issue == "Spike").sum()) if len(f) else 0,
                         Washout_pct=round(100 * (f[f.Issue == "Washout / enlarged hole"].Samples.sum() / n), 2)
                         if (c == "CALI" and len(f)) else np.nan,
                         Excluded_pct=round(100 * bad[c].mean(), 2)))
    return pd.DataFrame(rows)


