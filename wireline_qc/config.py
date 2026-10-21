"""Paths, curve names and all tuning parameters in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAS_FILE = ROOT / "data/raw/15-9-19_SR_COMP.LAS"
TOPS_FILE = ROOT / "data/raw/15_9_19_SR_TOPS_NPD.csv"
CHECKLIST_FILE = ROOT / "data/prejob_checklist.csv"
RISK_FILE = ROOT / "data/hse_risk_register.csv"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

TARGET_ZONE = "HUGIN FM"            # reservoir of interest in this well
CURVE_ALIASES = {                   # standard name -> possible mnemonics in the LAS
    "GR": ["GR"], "RHOB": ["RHOB", "DEN"], "NPHI": ["NPHI", "NEU"], "RT": ["RDEP", "RT", "ILD", "LLD"],
    "RM": ["RMED", "RM", "ILM"], "DT": ["AC", "DT"], "CALI": ["CALI", "CAL"]}
MAIN = ["GR", "RHOB", "NPHI", "RT"]
ALL = ["GR", "RHOB", "NPHI", "RT", "RM", "DT", "CALI"]

# ---- QC parameters ----------------------------------------------------------------------
VALID_RANGE = {"GR": (0, 250), "RHOB": (1.8, 3.0), "NPHI": (0.0, 0.60), "RT": (0.2, 2000),
               "RM": (0.2, 2000), "DT": (40, 200), "CALI": (4, 20)}
SPIKE_WINDOW, SPIKE_SIGMA, SPIKE_MAX_SAMPLES = 7, 8.0, 3   # spike = narrow (<= ~0.5 m) outlier
WASHOUT_WINDOW, WASHOUT_DELTA = 401, 1.5                   # caliper > local gauge + 1.5 in
SPIKE_FLOOR = 0.02                                         # noise floor: 2 % of the P5-P95 range
MAX_FILL = 6                                               # interpolate gaps up to ~1 m only

# ---- interpretation parameters ----------------------------------------------------------
CHALK = {"EKOFISK FM", "TOR FM", "HOD FM"}                 # limestone matrix zones
MATRIX = {"sand": 2.65, "chalk": 2.71}
FLUID_DENSITY = 1.00
VSH_CUTOFF, PHI_CUTOFF, RT_INDICATOR = 0.40, 0.08, 10.0
GR_CLEAN_PCT, GR_SHALE_PCT = 5, 99    # GR baselines (percentiles of cleaned GR over the interval)


