# Stage artifacts: semantic contracts

Artifacts are local files, not claims that a universal converter exists. The
Python plan envelope is deliberately small; package-native models/jobs/GDS
plans remain authoritative inside each stage.

## Discovery handoff

`inventory.json` contains a schema version, scan timestamp, dataset roots and
scope, acquisition/representation rows, metadata provenance, and explicit
validation states. Distinguish file enumeration, metadata resolution, header
checks, join validation, BIDS validation, and scientific readiness. "Not checked"
is different from "passed". A fingerprint manifest includes metadata/events/
confounds and selected images; inexpensive size/mtime indexes support discovery,
but content hashes or immutable object versions are required for approved reuse.

A selected row identifies subject, session, task, acquisition, run, direction,
echo/echo combination, derivative pipeline/version, description, spatial frame,
resolution/density, and file format. Missing entities are explicit, not wildcards.
Store full run keys; never join on row order or run number alone. Keep detailed
per-subject values local and supply only necessary aggregates to the model.

## First-level handoff

`first-level-index.tsv` has unique subject/unit, contrast ID, effect path, SE or
variance path, statistic/df paths when relevant, mask/grid identity, and QC state.
A JSON companion freezes the contrast expression and numeric weights, coefficient
order, model/noise settings, scaling/units, run aggregation, input and code hashes,
package versions, and missingness. Export unthresholded estimates and uncertainty.
`se` is standard error; `var = se^2`, never `var = se`. Preserve covariance needed
for later within-person comparisons. Do not reconstruct an effect and its variance
from a z map alone. Distinguish ordinary/robust/approximate uncertainty contracts.

For a small tabular bridge, use fmrigds columns
`sample,subject,contrast,beta,var`; retain a sidecar identifying sample order and
spatial semantics. Voxel index "17" is not a portable anatomical coordinate.
Use native image/HDF5 adapters for large data, verify their installed input
contract, and test one source block before cohort ingestion. The
[NIfTI handoff](nifti-handoff.md) gives a verified public-API route with separate
contrast beta/SE files; record the volume index as well as each contrast's path.

## Group handoff

`group-index.tsv` plus `inference.json` records design/formula, subject order,
level of independence, covariate coding, estimands, uncertainty model, actual N
per sample, missingness, mask, spatial frame, test distribution/df, sidedness,
multiple-testing family, correction, and alpha. Preserve estimates, SE/variance,
unthresholded statistics/p, corrected p/q when available, and the exact rejection
mask. All spatial arrays must share a verified lattice or a documented transform.
A correction over each chunk separately is not a whole-brain correction.

## Report handoff

A neuromosaic map manifest carries analysis_id, map_id, path, role, quantity,
distribution, and label; metadata identifies the background/atlas version and
space, inference manifest, display thresholds, and disclosure level. Do not call
q-values p-values or t-statistics z-statistics. Reports must distinguish corrected
inference from exploratory display controls. Data selected by the same statistic
can illustrate a result but cannot independently confirm it. Record empty results
and failures; do not tune a threshold until a pleasing picture appears.

## Completion

A completed stage has readable outputs, validation/QC receipts, explicit failed
units and reasons, reproducible code/environment, and a handoff. A coordinator
is complete when the **requested** stages are complete or a precise blocker is
reported, not when every possible stage has been run.
