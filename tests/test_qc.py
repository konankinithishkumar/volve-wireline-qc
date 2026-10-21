import numpy as np
import pandas as pd

from wireline_qc.evaluation import evaluate
from wireline_qc.loaders import runs
from wireline_qc.qc import run_qc


def synthetic_log(n=400):
    rng = np.random.default_rng(1)
    depth = 3000 + 0.1524 * np.arange(n)
    return pd.DataFrame({
        "DEPTH": depth,
        "GR": 40 + rng.normal(0, 2, n),
        "RHOB": 2.40 + rng.normal(0, 0.01, n),
        "NPHI": 0.20 + rng.normal(0, 0.005, n),
        "RT": 10 * np.exp(rng.normal(0, 0.05, n)),
        "RM": 10 * np.exp(rng.normal(0, 0.05, n)),
        "DT": 80 + rng.normal(0, 1, n),
        "CALI": 8.5 + rng.normal(0, 0.02, n),
    })


def test_runs_finds_consecutive_blocks():
    mask = np.array([0, 1, 1, 0, 0, 1, 0, 1, 1, 1], dtype=bool)
    assert runs(mask) == [(1, 2), (5, 5), (7, 9)]
    assert runs(np.zeros(5, dtype=bool)) == []


def test_clean_log_raises_no_flags():
    flags, bad, washout, step = run_qc(synthetic_log())
    assert flags.empty
    assert abs(step - 0.1524) < 1e-6


def test_null_range_spike_and_washout_are_flagged():
    w = synthetic_log()
    w.loc[50:54, "NPHI"] = np.nan          # nulls
    w.loc[100, "GR"] = 400                 # out of range
    w.loc[200, "RHOB"] = 2.9               # narrow spike, still in valid range
    w.loc[300:310, "CALI"] = 12.0          # washout
    flags, bad, washout, _ = run_qc(w)
    issues = set(zip(flags.Curve, flags.Issue))
    assert ("NPHI", "Missing / null") in issues
    assert ("GR", "Out of range") in issues
    assert ("RHOB", "Spike") in issues
    assert ("CALI", "Washout / enlarged hole") in issues
    assert bad["RHOB"][300:311].all()      # density excluded inside the washout


def test_evaluation_values_stay_physical():
    w = synthetic_log()
    flags, bad, washout, _ = run_qc(w)
    tops = pd.DataFrame({"Formation": ["TEST FM"], "Top": [w.DEPTH.min()], "Base": [w.DEPTH.max() + 1]})
    ev, zones, refs, step = evaluate(w, bad, tops)
    assert ev.VSH.between(0, 1).all()
    assert ev.PHI.between(0, 0.45).all()
    assert len(zones) == 1
