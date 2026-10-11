# Offline analysis code

This local reproduction package reads the frozen inputs and recreates nineteen analytical CSV tables and eleven composite figures (Figures 1–8 and S1–S3). It does not export the manuscript or Word documents. See Sources.md for provenance and reuse conditions; no blanket open licence is assigned.

## Run

Use Python 3.12 and an isolated environment. The numerical replay was validated with the pinned versions in 代码/requirements.txt. Install dependencies, then run from the extracted package root:

    python -m pip install -r 代码/requirements.txt
    python 代码/复现分析.py

Dependency installation may require internet access; the analysis and figure replay itself uses only included local inputs and makes no live data requests. No API account or credentials are required for the frozen replay. Source acquisition from the original services is separate and is not re-executed.

Matplotlib must be able to resolve an installed, appropriately licensed Times New Roman font. The font is not included. The driver runs the statistical analysis, an independent numerical check, English table rendering, four main-figure scripts and the supplementary-figure script in that order. Numerical model refits reproduce the specified exploratory analysis; the script never selects predictors by P value. The one stopped model remains recorded in the diagnostics.

All paths used for analysis are relative to the extracted package root. The original machine-specific dependency-path injections were removed only in these portable copies. GBD citation-date explanations in two generated-output strings were corrected without altering numerical logic. The four main-figure scripts come from the latest 正式分析/代码 versions, including updated legend sizes; their source and portable hashes are in 核验/Portable changes.json. Embedded historical provenance paths in input metadata are documentation, not runtime dependencies.

Replay writes or replaces outputs under 表格, 图形, 核验 and 报告 inside the extracted package. Avoid running it in a folder containing unrelated work. Generated figure formats are PDF, SVG and PNG with low-resolution previews and source CSV files. No original fonts, original large GBD download archives, expired-download fetcher, old manuscript/Word generation scripts or reference-publication PDFs are included.

## Validation and interpretation

Expected statistics-table hashes and input/code hashes are listed in Inventory.json. The separate validation report records the actual tested environment, table-byte comparison, figure counts and ZIP CRC results. Identical binary image/PDF files are not expected across platforms because renderer/font versions and embedded metadata can vary. Source estimates and denominators should agree under the frozen numerical environment.

The companion Source data.zip contains the frozen nineteen analytical CSVs, forty-three figure-source CSVs and six English-labelled machine-readable CSVs. The current code bundle contains the inputs needed to reconstruct the analytical tables and all eleven figures. Original reference-paper text/images are excluded. Use the accompanying sources and definitions when interpreting the outputs; national availability responses are not individual medication use.
