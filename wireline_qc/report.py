"""PDF report."""
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle

from .config import *


def tbl(data, widths, font=7.5, hdr="#1f3b57"):
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(hdr)), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), font),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.3, colors.grey)]
    for i in range(2, len(data), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f1f4f8")))
    t.setStyle(TableStyle(st))
    return t


def build_pdf(path, meta, mapping, inv, w, window, flags, qsum, checks, zones, hugin, refs, step,
              ck, open_items, verdict, rk, plots):
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12)
    cell = ParagraphStyle("c", parent=ss["BodyText"], fontSize=7.5, leading=9)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=colors.HexColor("#1f3b57"), spaceBefore=8)
    P = lambda s: Paragraph(str(s), cell)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.4 * cm, rightMargin=1.4 * cm,
                            topMargin=1.3 * cm, bottomMargin=1.3 * cm,
                            title="Wireline Log QC and Evaluation - Volve 15/9-19 SR")
    s = [Paragraph("Wireline Log QC and Basic Formation Evaluation", ss["Title"]),
         Paragraph(f"<b>Well {meta.get('WELL', '15/9-19')} SR - Volve field area, Norwegian North Sea</b> "
                   "(real data, Equinor Volve open data set - see DATA_SOURCE.md for provenance and licence).<br/>"
                   f"Analysis interval {window[0]:.0f}-{window[1]:.0f} m MD where GR, density, neutron and "
                   f"resistivity all exist; {len(w)} samples at {step:.4f} m. Target zone: {TARGET_ZONE}.", body)]

    nflag = 0 if flags.empty else len(flags)
    review = (checks.Status != "Pass").sum()
    s += [Paragraph("1. Summary", h2),
          Paragraph(f"Data acceptance: <b>{'ACCEPT WITH FLAGS' if review else 'ACCEPT'}</b> - {review} of "
                    f"{len(checks)} checks need review. {nflag} QC events were logged; flagged samples were "
                    "excluded from interpretation (short gaps up to ~1 m interpolated, longer gaps left empty). "
                    "Raw data is never modified.", body),
          Paragraph("2. Data inventory (full file)", h2)]
    data = [["Curve", "LAS", "Unit", "From (m)", "To (m)", "Samples", "Min", "Median", "Max"]] + [
        [r.Curve, r.LAS_mnemonic, r.Unit, f"{r.Top:.0f}", f"{r.Base:.0f}", r.Samples, f"{r.Min:.2f}",
         f"{r.Median:.2f}", f"{r.Max:.2f}"] for r in inv.itertuples()]
    s.append(tbl(data, [1.6 * cm, 1.8 * cm, 1.8 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2.2 * cm, 2.2 * cm]))
    s.append(Paragraph("GR runs the whole well; density, neutron and resistivity cover the lower part only, "
                       "so the analysis is limited to the interval where all are present.", body))

    s.append(Paragraph("3. Data acceptance checks", h2))
    t = tbl([["Check", "Status", "Remarks"]] + [[P(r.Check), r.Status, P(r.Remarks)] for r in checks.itertuples()],
            [8 * cm, 2 * cm, 7.8 * cm])
    for i, r in enumerate(checks.itertuples(), start=1):
        if r.Status != "Pass":
            t.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fde2e2"))]))
    s.append(t)

    s.append(Paragraph("4. QC summary by curve (analysis interval)", h2))
    data = [["Curve", "Null %", "Out-of-range samples", "Spike events", "Washout %", "Excluded %"]] + [
        [r.Curve, r.Null_pct, r.OutOfRange_samples, r.Spike_events,
         "-" if pd.isna(r.Washout_pct) else r.Washout_pct, r.Excluded_pct] for r in qsum.itertuples()]
    s.append(tbl(data, [2 * cm, 2.5 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm]))
    s.append(Paragraph(f"Checks: nulls; physical ranges; narrow spikes (rolling median, {SPIKE_SIGMA:g} robust sigma, "
                       f"max {SPIKE_MAX_SAMPLES} samples); caliper washout (> {WASHOUT_DELTA} in above local gauge) - "
                       "density and neutron are excluded in washouts; depth skips. Full event list: "
                       "output/qc_flags.csv.", body))
    if nflag:
        top = flags.sort_values("Samples", ascending=False).head(10)
        s.append(Paragraph("Ten largest QC events", h2))
        data = [["Curve", "Issue", "Top (m)", "Base (m)", "Samples", "Detail"]] + [
            [r.Curve, P(r.Issue), f"{r.Top:.1f}", f"{r.Base:.1f}", r.Samples, P(r.Detail)] for r in top.itertuples()]
        s.append(tbl(data, [1.5 * cm, 3.6 * cm, 1.8 * cm, 1.8 * cm, 1.6 * cm, 7.5 * cm]))

    s += [PageBreak(), Paragraph("5. Log display - full analysis interval", h2),
          Image(str(plots[0]), width=17 * cm, height=17 * cm * 15 / 12), PageBreak(),
          Paragraph(f"6. Log display - {TARGET_ZONE} and surroundings", h2),
          Image(str(plots[1]), width=17 * cm, height=17 * cm * 9 / 12)]

    s.append(Paragraph(
        "<b>Method and assumptions.</b> Vsh: Larionov (older rocks) from a gamma-ray index with baselines at the "
        f"5th/99th percentile of cleaned GR ({refs[0]:.0f} / {refs[1]:.0f} API) for the whole interval. Porosity: "
        f"density porosity (matrix {MATRIX['sand']} g/cc sand, {MATRIX['chalk']} g/cc for Ekofisk/Tor/Hod chalk, "
        f"fluid {FLUID_DENSITY} g/cc) averaged with neutron porosity by root-mean-square; no shale, gas or "
        "lithology corrections. Net rock = Vsh &lt; %.2f and porosity &gt; %.2f. Net is a rock-quality flag, "
        "<b>not</b> net pay: no water saturation is computed because no reliable Rw is available." %
        (VSH_CUTOFF, PHI_CUTOFF), body))

    s += [PageBreak(), Paragraph("7. Formation summary", h2)]
    data = [["Formation", "Top", "Base", "Thk", "Valid %", "GR", "Vsh", "Phi", "RT med", "Net m", "NTG"]] + [
        [P(r.Formation), r.Top, r.Base, r.Thickness, r.Valid_pct, r.GR_mean, r.Vsh_mean, r.Phi_mean, r.RT_median,
         r.Net_m, r.NTG] for r in zones.itertuples()]
    s.append(tbl(data, [3.4 * cm, 1.4 * cm, 1.4 * cm, 1.2 * cm, 1.4 * cm, 1.2 * cm, 1.2 * cm, 1.3 * cm, 1.6 * cm,
                        1.4 * cm, 1.2 * cm]))
    s.append(Paragraph(f"Net rock intervals in {TARGET_ZONE}", h2))
    if hugin.empty:
        s.append(Paragraph("No intervals meet the cutoffs after QC.", body))
    else:
        data = [["Top", "Base", "Thk (m)", "Vsh", "Phi", "RT med", "Indicator"]] + [
            [r.Top, r.Base, r.Thickness, r.Vsh, r.Phi, r.RT, r.Indicator] for r in hugin.itertuples()]
        s.append(tbl(data, [2 * cm, 2 * cm, 2 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 4 * cm]))
    s.append(Paragraph("A resistivity indicator means RDEP above %g ohm.m in clean porous rock; it needs a "
                       "saturation calculation and fluid data to be confirmed." % RT_INDICATOR, body))

    s.append(Paragraph("8. Pre-job readiness checklist (illustrative template)", h2))
    t = tbl([["Category", "Item", "Status", "Remarks"]] + [[P(r.Category), P(r.Item), P(r.Status), P(r.Remarks)]
                                                          for r in ck.itertuples()],
            [2.6 * cm, 7.2 * cm, 1.8 * cm, 6.2 * cm])
    for i, r in enumerate(ck.itertuples(), start=1):
        if r.Status != "Done":
            t.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fde2e2"))]))
    s += [t, Paragraph(f"Result: <b>{verdict}</b>. These statuses are a worked example for a wireline job; "
                       "they are not records from the real Volve job.", body),
          Paragraph("9. HSE risk register (generic wireline hazards)", h2)]
    data = [["Hazard", "Activity", "L", "S", "Score", "Rating", "Controls", "Owner"]] + [
        [P(r.Hazard), P(r.Activity), r._3, r._4, r.Score, r.Rating, P(r._5), P(r._6)] for r in rk.itertuples()]
    s.append(tbl(data, [2.8 * cm, 2.6 * cm, 0.6 * cm, 0.6 * cm, 1 * cm, 1.3 * cm, 6.2 * cm, 2.4 * cm]))
    s.append(Paragraph("Score = Likelihood x Severity: 1-5 Low, 6-11 Medium, 12+ High.", body))

    s.append(Paragraph("10. Limitations and unresolved issues", h2))
    items = ["Calibration records, repeat section and the logging contractor's own QC are not in the dataset; "
             "the data cannot be formally accepted without them.",
             "Neutron porosity is assumed to be a limestone/sandstone-scaled v/v value; the LAS header does not say "
             "which matrix the tool was calibrated to.",
             "No water saturation, core calibration or fluid data - net rock is not net pay.",
             "Washout flags depend on a rolling-median gauge estimate, not the true bit size.",
             "Thin beds below the sampling and tool resolution are not resolved."]
    s += [Paragraph("&bull; " + i, body) for i in items]
    doc.build(s)


