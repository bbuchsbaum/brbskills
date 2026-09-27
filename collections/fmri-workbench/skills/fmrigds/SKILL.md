---
name: fmrigds
description: "Build and validate group-level fMRI analyses with fmrigds from existing effect/statistic maps or tables: covariates, uncertainty, repeated measures, corrections, and cohort examination. Does not require first-level refitting."
license: MIT
compatibility: Requires local filesystem access; R for package execution and Python 3.10+ for optional helpers.
metadata:
  version: "0.1.0"
  reviewed: "2026-09-27"
---

# Group fMRI with fmrigds

Accept existing subject estimates/maps/tables or a first-level handoff; do not
require BIDS or fmrireg. For an API question, read only [API](references/api.md).
For a new analysis also read the [operating contract](references/operating-contract.md)
and [inference decisions](references/inference.md). Check [installed capabilities](references/capabilities.md).

## Establish the observation and estimand

Verify subject identity/order, independent units, repeated sessions/conditions,
spatial alignment, contrast semantics and units, masks, missingness, covariates,
and the meaning of available assays. Follow the [handoff bridge](references/handoff.md).
An SE is not a variance; a z/p map cannot uniquely supply an effect and its
sampling variance. Effects without uncertainty can support a suitable unweighted
group model; do not invent unit variance for precision weighting. Repeated runs
are not independent subjects. A fixed-effects teaching example is not a default
population model.

Ask only material unresolved group decisions: estimand/model/covariates,
repeated-measures structure, uncertainty assumptions, inclusion/missingness,
and correction family. Freeze the proposed model and contrast before inspecting
its interesting outcomes. Fit neither an unsupported general mixed model nor
a whole-brain correction independently by chunk.

## Build a lazy plan

Use `gds()` or documented `as_gds()` inputs, keyed covariate attachment, explicit
`reduce()` or appropriate public model helper, and `posthoc()` where justified.
Inspect `explain()` / `preview()` / `validate()` before approved `compute()`.
`assets/group_template.R` constructs a lazy plan from explicit inputs; it does
not execute. `scripts/smoke_group.R` checks a known fixed-effects arithmetic
identity on tiny synthetic data, not a production model choice.

Choose public registered methods supported by the installed version. The reviewed
LMM family is intentionally restricted: do not assume arbitrary lmer syntax,
random effects, missing layouts, or covariance structures. Unsupported science
requires an explicit alternative adapter/model, not silent simplification.

## Examine, correct, export

Use `examine_group()` where supported to separate validity concerns, model
surprise, and influence. A review priority is not an exclusion rule. Record
sensitivity analyses without redefining the primary cohort opportunistically.
Preserve actual per-sample N, model/variance diagnostics, convergence flags,
heterogeneity where relevant, and missingness. Correct over the declared full
family, accounting explicitly for mask, contrasts, sidedness, and post-selection.
Retain unthresholded effects/statistics, uncertainty, p/q and rejection masks.

Complete the [artifact contract](references/artifact-contracts.md) with a frozen
inference manifest. A reporting stage is optional; do not rerun a model just to
make maps look more impressive. A report renderer's cluster threshold is not a
statistical correction. Deliver outputs and limitations, including any failed
subjects/samples, numerical approximations, or unsupported assumptions.
