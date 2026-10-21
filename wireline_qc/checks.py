"""Acceptance checks, pre-job checklist and HSE risk scoring."""
import numpy as np
import pandas as pd

from .config import *


def acceptance_checks(df, w, qsum, flags, nominal, ev, tops):
    hz = tops[tops.Formation == TARGET_ZONE]
    rows = []

    def add(item, ok, remark, na=False):
        rows.append(dict(Check=item, Status="Not available" if na else ("Pass" if ok else "Review"), Remarks=remark))

    add("Required curves present (GR, density, neutron, resistivity)", all(c in df for c in MAIN),
        "All four main curves found")
    step = np.diff(w.DEPTH.values)
    add("Regular depth sampling, no logging skips", (step > 1.5 * nominal).sum() == 0,
        f"nominal step {nominal:.4f} m; {(step > 1.5 * nominal).sum()} gap(s)")
    worst = qsum.set_index("Curve").Null_pct[MAIN].max()
    add("Null values below 5 % on main curves (in logged interval)", worst < 5, f"worst curve {worst:.1f} % null")
    oor = qsum.set_index("Curve").OutOfRange_samples[MAIN].sum()
    add("Out-of-range samples below 1 % of interval", oor / len(w) < 0.01,
        f"{oor} samples ({100 * oor / len(w):.2f} %)")
    wo = qsum.set_index("Curve").Washout_pct.get("CALI", 0)
    add("Washout below 10 % of interval", wo < 10, f"{wo:.1f} % of interval has enlarged hole")
    if len(hz):
        z = ev[ev.FORMATION == TARGET_ZONE]
        cov = 100 * z.VALID.mean()
        add(f"Valid data over {TARGET_ZONE} (target) above 90 %", cov > 90, f"{cov:.0f} % valid after QC")
    add("Tool calibration records and repeat section", False,
        "Not included in the LAS file - request from logging company", na=True)
    return pd.DataFrame(rows)


def readiness(path):
    ck = pd.read_csv(path).fillna("")
    open_items = ck[ck.Status != "Done"]
    verdict = ("READY - all checks complete" if open_items.empty
               else f"NOT READY - {len(open_items)} of {len(ck)} checks open")
    return ck, open_items, verdict


def risk_table(path):
    rk = pd.read_csv(path)
    rk["Score"] = rk["Likelihood(1-5)"] * rk["Severity(1-5)"]
    rk["Rating"] = pd.cut(rk.Score, [0, 5, 11, 25], labels=["Low", "Medium", "High"])
    return rk.sort_values("Score", ascending=False).reset_index(drop=True)


