"""Reading the LAS file and formation tops."""
import lasio
import numpy as np
import pandas as pd

from .config import CURVE_ALIASES


def load_log(path):
    las = lasio.read(str(path))
    raw = las.df().reset_index().rename(columns={las.df().index.name or "DEPT": "DEPTH"})
    raw = raw.replace(las.well["NULL"].value, np.nan)
    units = {c.mnemonic: c.unit for c in las.curves}
    df = pd.DataFrame({"DEPTH": raw["DEPTH"]})
    mapping = {}
    for std, names in CURVE_ALIASES.items():
        for n in names:
            if n in raw.columns:
                df[std] = raw[n]; mapping[std] = (n, units.get(n, "")); break
    if "NPHI" in df and str(mapping["NPHI"][1]).strip() in ("%", "PU", "pu"):
        df["NPHI"] = df["NPHI"] / 100.0                      # percent -> v/v
    meta = {k: las.well[k].value for k in ("WELL", "FLD", "COMP") if k in las.well}
    return df.sort_values("DEPTH").reset_index(drop=True), mapping, meta


def load_tops(path, top, base):
    t = pd.read_csv(path, header=None, names=["Formation", "Top"], encoding="utf-8-sig")
    t = t.sort_values("Top").reset_index(drop=True)
    t["Base"] = t["Top"].shift(-1).fillna(base)
    t = t[(t.Base > top) & (t.Top < base)].copy()
    t["Top"] = t["Top"].clip(lower=top); t["Base"] = t["Base"].clip(upper=base)
    return t.reset_index(drop=True)


def runs(mask):
    """(start, end) index pairs of consecutive True values."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return []
    d = np.diff(np.r_[0, m.view(np.int8), 0])
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0] - 1))


