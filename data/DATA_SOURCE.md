# Data source and provenance

| Item | Detail |
|---|---|
| Well | 15/9-19 SR, Volve field area (Block 15/9, Norwegian North Sea) |
| Operator | Equinor (formerly Statoil) |
| Original dataset | Equinor **Volve** open data set, released 2018 for research and education |
| Files used | `15-9-19_SR_COMP.LAS` (composite wireline log, LAS 2.0, 102-4637 m MD) and `15_9_19_SR_TOPS_NPD.csv` (formation tops, MD, from the Norwegian Petroleum Directorate) |
| How the copy was obtained | Downloaded from the public GitHub repository `andymcdgeo/Petrophysics-Python-Series` (code under MIT licence), folder `Data/` and `Data/Volve/` |
| Licence of the data | **Equinor Open Data Licence** (named on Equinor's Volve page: https://www.equinor.com/en/what-we-do/digitalisation-in-our-dna/volve-field-data-village-download.html). The licence terms were not readable when this project was built - read them yourself before redistributing the data. |
| Modifications | None. The LAS file is unchanged; all processing happens in `src/wireline_qc.py` |

Attribution: well-log data from the Equinor Volve Data Village. This project is an independent educational
exercise and is not endorsed by Equinor.

The pre-job checklist and HSE risk register in `data/` are generic illustrative templates written for this
project. They are NOT records from the real Volve logging job.
