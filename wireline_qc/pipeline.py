"""Runs the whole workflow and writes everything to output/."""
import numpy as np
import pandas as pd

from .checks import acceptance_checks, readiness, risk_table
from .config import *
from .evaluation import evaluate, net_intervals
from .loaders import load_log, load_tops
from .plots import plot_log
from .qc import analysis_window, inventory, qc_summary, run_qc
from .report import build_pdf


def main(las_file=None):
    las_file = las_file or LAS_FILE
    df, mapping, meta = load_log(las_file)
    window = analysis_window(df)
    w = df[(df.DEPTH >= window[0]) & (df.DEPTH <= window[1])].reset_index(drop=True)
    tops = load_tops(TOPS_FILE, window[0], window[1])

    inv = inventory(df, mapping)
    flags, bad, washout, nominal = run_qc(w)
    qsum = qc_summary(flags, w, bad, nominal)
    ev, zones, refs, step = evaluate(w, bad, tops)
    hugin = net_intervals(ev, TARGET_ZONE, step)
    checks = acceptance_checks(df, w, qsum, flags, nominal, ev, tops)
    ck, open_items, verdict = readiness(CHECKLIST_FILE)
    rk = risk_table(RISK_FILE)

    inv.to_csv(OUT / "data_inventory.csv", index=False)
    flags.to_csv(OUT / "qc_flags.csv", index=False)
    qsum.to_csv(OUT / "qc_summary.csv", index=False)
    checks.to_csv(OUT / "acceptance_checks.csv", index=False)
    zones.to_csv(OUT / "formation_summary.csv", index=False)
    hugin.to_csv(OUT / "hugin_net_intervals.csv", index=False)
    ev[["DEPTH", "FORMATION", "GR", "RHOB", "NPHI", "RT", "VSH", "PHID", "PHI", "VALID", "NET"]] \
        .to_csv(OUT / "interpreted_log.csv", index=False)

    hz = tops[tops.Formation == TARGET_ZONE].iloc[0]
    plot_log(w, ev, bad, washout, tops, window[0], window[1], OUT / "log_overview.png",
             "Well 15/9-19 SR - full analysis interval (real Volve data)", height=15)
    plot_log(w, ev, bad, washout, tops, hz.Top - 30, min(hz.Base + 40, window[1]), OUT / "log_target_zone.png",
             f"Well 15/9-19 SR - {TARGET_ZONE} and surroundings", height=9)
    build_pdf(OUT / "wireline_qc_report.pdf", meta, mapping, inv, w, window, flags, qsum, checks, zones, hugin,
              refs, step, ck, open_items, verdict, rk, [OUT / "log_overview.png", OUT / "log_target_zone.png"])

    print(f"Analysis window {window[0]:.1f}-{window[1]:.1f} m, {len(w)} samples, step {nominal:.4f}")
    print("\nQC summary:\n", qsum.to_string(index=False))
    print("\nFlag counts:\n", flags.groupby(["Curve", "Issue"]).Samples.agg(["count", "sum"]) if len(flags) else "none")
    print("\nAcceptance:\n", checks.to_string(index=False))
    print("\nZones:\n", zones.to_string(index=False))
    print("\nHugin net:\n", hugin.to_string(index=False))


