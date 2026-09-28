# PoTeC lme4 skill trial

Open `analysis.html` for the rendered report or `analysis.qmd` for the executable
Quarto source. `findings.md` and `skill-assessment.md` are included in the rendered
document. This is an informed exploratory pilot, not a blind skill evaluation.
The print version is `output/pdf/potec-lme4-analysis.pdf`.

The main fits are a full eligible-word log-FPRT LMM (95,683 first-pass-fixated
observations) and a seeded quarter-word FPReg GLMM (33,600 observations). Both
retain 75 readers and 12 texts. Numerical qualification remains unresolved;
the report does not certify either analysis as ready for confirmatory inference.

## Files and reproduction

Run commands from this directory. Required packages are lme4, lmerTest,
data.table, ggplot2, jsonlite, statmod, reformulas, knitr and rmarkdown; Quarto
1.7.32 rendered the report. Exact installed versions are recorded with the fits.
No package installer is run by these scripts.

```sh
python3 fetch_data.py
Rscript --vanilla prepare.R
Rscript --vanilla fit.R lmm quarter diagonal
Rscript --vanilla fit.R glmm quarter diagonal
Rscript --vanilla fit.R lmm full diagonal
Rscript --vanilla fit.R lmm quarter correlated
Rscript --vanilla fit.R lmm full diagonal strict
Rscript --vanilla summarize.R full quarter
Rscript --vanilla sensitivity.R
Rscript --vanilla verify.R
quarto render analysis.qmd
```

To render the print version, also install the R package `kableExtra` and a TeX
distribution with XeLaTeX, then run:

```sh
quarto render analysis.qmd --to pdf --metadata-file analysis-pdf.yml --output potec-lme4-analysis.pdf --output-dir output/pdf
```

The PDF uses the same retained results, wraps wide tables and code output, and
hides executable R chunks. The HTML retains expandable R code.

The two incomplete attempts were `fit.R lmm full diagonal alternate` (600-second
limit) and `check_glmm_derivatives.R` (900-second limit). Their timeout receipts
are preserved. Ordinary fits had a 900-second limit, except the correlated
quarter LMM (600 seconds). Logs were captured with the installed lean-logs
wrapper. The launch receipt identifies the original code hash; its exact initial
fitting script is archived in `provenance/fit.initial.R` and is not a separate
entry point. Later changes added warm starts for numerical checks.

`data-manifest.json` pins Git source files, the independently downloaded OSF
archive, and the skill snapshot. Existing inputs are verified against it before
reuse. `analysis-plan.yml` records the decisions made before fitting. The original
source skill was left unchanged.

`data/`, `outputs/`, and `logs/` are local ignored artifacts, not bundled public
data. Outputs retain row IDs, scaling, fitted objects, raw conditions, audits,
tables, plots and session information. The HTML embeds its plots. Re-rendering
uses retained fits rather than silently rerunning expensive models. A matching
Satterthwaite fit is cached to avoid recomputing its derivatives; a parameter
mismatch stops summary generation instead of reusing stale inference.

Rendering in the Codex sandbox failed at Quarto's CPU-detection step. The local
render succeeded with authorized access to the installed runtime. That original
render did not publish or commit the report.

## Repository preparation

The source, frozen HTML/PDF reports and audit receipts are retained together;
downloaded inputs, fitted objects and execution logs remain local and ignored.
The redirect URL in `data-manifest.json` has its expiring query signature removed.
Stable source URLs and input checksums are unchanged, and `fetch_data.py` now
omits redirect query strings when creating future manifests. Cached inputs and
artifact consistency checks were reverified before committing, without refitting.

The report's derivative-check paragraph describes the script's intended sequence.
The timed-out attempt left no completed objective/Hessian receipt, so that
paragraph must not be read as evidence that the check passed. The original
rendered reports and scientific limitations are preserved.
