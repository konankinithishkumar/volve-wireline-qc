# Methods and assumptions

## Quality control
| Check | Rule |
|---|---|
| Nulls | LAS null value (-999.25) converted to NaN; each run of NaN is logged |
| Range | GR 0-250 API, RHOB 1.8-3.0 g/cc, NPHI 0-0.60 v/v, resistivity 0.2-2000 ohm.m, DT 40-200 us/ft, caliper 4-20 in |
| Spikes | Deviation from a 7-sample rolling median above 8 robust sigma (1.4826 x MAD, with a floor of 2 % of the P5-P95 range). Only runs of 3 samples or fewer count as spikes, so real thin beds are not removed. Resistivity is tested as log10 |
| Depth | Step larger than 1.5 x the median step is a gap |
| Washout | Caliper more than 1.5 in above a 401-sample rolling-median gauge. Density and neutron are excluded in washouts because the pad and detectors lose contact with the wall |

Flagged samples are excluded from the interpretation copy only; raw data is never changed. Gaps up to
6 samples (about 1 m) are interpolated, longer ones are left empty.

## Formation evaluation
- **Gamma-ray index:** IGR = (GR - GR_clean) / (GR_shale - GR_clean), baselines at the 5th and 99th percentile
  of cleaned GR over the interval (the interval is mostly clean rock, so the 95th percentile gave too low a
  shale line; Heather shale reads about 100 API).
- **Shale volume (Larionov, older rocks):** Vsh = 0.33 x (2^(2 x IGR) - 1), limited to 0-1. Jurassic rocks
  such as Hugin are older rocks, so this is the appropriate form.
- **Density porosity:** PHID = (rho_matrix - RHOB) / (rho_matrix - rho_fluid), rho_matrix 2.65 g/cc for sand and
  shale zones, 2.71 g/cc for the Ekofisk, Tor and Hod chalks, rho_fluid 1.0 g/cc.
- **Combined porosity:** PHI = sqrt((PHID^2 + NPHI^2) / 2). No shale, gas or lithology correction.
- **Net rock:** Vsh < 0.40 and PHI > 0.08 on valid samples.
- **Resistivity indicator:** deep resistivity above 10 ohm.m inside net rock. This only suggests hydrocarbons.
  A saturation calculation (Archie or similar) needs Rw, a, m and n, none of which are available here.

## Acceptance checks
Automatic pass/review on curve availability, depth sampling, nulls, out-of-range share, washout share and valid
data in the target zone. Tool calibration and repeat-section records are marked "not available" because they
are not part of the LAS file.

## Risk scoring
Risk score = likelihood (1-5) x severity (1-5): 1-5 low, 6-11 medium, 12 and above high.
