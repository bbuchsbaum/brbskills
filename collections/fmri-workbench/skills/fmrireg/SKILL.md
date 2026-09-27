---
name: fmrireg
description: "Specify, diagnose, fit, or export first-level task-fMRI GLMs with fmrireg, including HRFs, nuisance baselines, contrasts, and native batch jobs. Use independently of group analysis and reports; not for preprocessing."
license: MIT
compatibility: Requires local filesystem access; R for package execution and Python 3.10+ for optional helpers.
metadata:
  version: "0.1.0"
  reviewed: "2026-09-27"
---

# First-level fMRI with fmrireg

Start from preprocessed BOLD with aligned events/confounds, an fmri_frame,
matrices, or validated bindings. This skill works without bidser, fmrigds, or
neuromosaic. Do not import a whole cohort workflow for a formula/API question.

For an analysis, read the [operating contract](references/operating-contract.md)
and reuse prior decisions. Verify the installed [API](references/api.md) and
[capabilities](references/capabilities.md). Ask only unresolved first-level
scientific questions; do not interview about group covariates or report atlases.

When adapting an existing script or joining bidser inputs to a manual model, use
[existing analysis patterns](references/existing-analyses.md). Preserve the
estimand and downstream outputs; verify historical workarounds against the
selected package versions before retaining them.

## Specify an estimable model

When the intended model is still open, inspect the event tables and use
[events to candidate designs](references/events-to-design.md) to propose supported
questions and contrasts before choosing a formula.

Record the event meaning and timing origin, duration/amplitude handling, HRF and
basis interpretation, contrast sign/weights, run structure, scaling, nuisance,
and temporal-noise model. Use [design decisions](references/design-decisions.md)
and [confounds](references/confounds.md) only as needed. Inspect the realized
matrix: matching rows, finite values, columns/condition counts per run, rank,
conditioning, residual degrees of freedom, and contrast estimability. Plot a
small design/timing sample. Treat a missing condition as unavailable, not zero.
Do not silently delete nuisance columns, change contrasts, or simplify a
preregistered model to make a fit run.

Use the public frame/design interfaces and `fmri_lm()`. For new repeated-fit workflows prefer
`fmri_template()` + explicit bindings + `instantiate()` + `preflight()`; read
[batch and export](references/batch-and-export.md). The `from_bids()` shortcut
requires a separately certified unambiguous dataset; its reviewed implementation
is not safe to assume for mixed TR, repeated run labels across sessions, or
multiple echoes/representations. Use `as_manifest()` for explicit bindings.

## Test and fit

`scripts/smoke_first_level.R` is a small synthetic compatibility test, not a
production default. `assets/first_level_template.R` builds jobs from reviewed
bindings and explicit choices without launching them. Verify a representative
pilot (and distinct acquisition strata), coefficient/contrast signs, residuals,
uncertainty, and execution resources before approved fan-out. Use native job
failure records and file-backed reducers; keep whole fits out of agent context.
The reviewed `noise_spec(censor=...)` is not regression-volume removal; it only
affects AR estimation/whitening and is inert for iid noise. Do not treat OLS, AR prewhitening, robust weighting, and accelerated engines as
statistically interchangeable. A fast engine needs its own validity check.

## Export and stop at scope

Export unthresholded contrast estimates plus SE/variance and needed statistics/
df; carry coefficient order, contrast weights, masks/space, units, temporal-noise
settings, and complete provenance. See [artifact contracts](references/artifact-contracts.md).
For group-ready results retain within-person covariance when required. Do not
average t/z maps as if they were effect estimates. For NIfTI inputs to fmrigds,
follow the [subject-to-group recipe](references/nifti-handoff.md): separate contrast
beta/SE files, explicit contrast order, verified grids and coverage masks.
`scripts/smoke_nifti_handoff.R` checks this route on synthetic data when both
packages are available. Group inference is optional;
a first-level request ends with first-level outputs and QC.

Apply explicitly confirmed, applicable preferences, but never infer that examples
such as motion24 or B-spline drift are a user's defaults. Freeze realized nuisance
columns and drift basis details in the analysis record. Return exact outputs,
failed units, and limitations; never claim a test ran when only source was read.
