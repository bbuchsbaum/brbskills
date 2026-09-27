# Learn from an existing analysis

Use this reference when reviewing, adapting, or extending an existing script.
It distills a 2026-09-27 review of 41 study-side R scripts, including 22 using
bidser. Related variants are not independent validation. Preserve working manual
frame/design workflows; adopt templates when they solve the requested batch need.

## Recover the actual analysis

Trace input roots, sourced helpers, arguments/environment variables, package
versions/commit IDs, model construction and downstream consumers. A script's
directory, filename, comments, or output tag may describe a different dataset or
engine from the code it runs. Save the resolved configuration and inspect returned
engine/noise/variance metadata; report requested and realized settings separately.

Before retaining a workaround, identify the failure it addressed and check the
selected installed API, relevant upstream source/tests, and a small synthetic
reproduction when practical. Record whether it is obsolete, still needed for
that input/version, or unverified. Upstream fixes do not establish what is installed
on a worker. Do not silently upgrade packages or refit historical analyses.

Examples from the dated review:

- The claim that `write_results()` only writes HDF5 is obsolete: current upstream
  supports NIfTI. Prefer the public writer when it meets the output contract.
- fmrireg's contrast helpers are now reexports from fmridesign; an old namespace
  masking comment is not a reason to mandate a replacement implementation.
- Stripping nuisance-list names to avoid an integer-format error was unnecessary
  in a synthetic probe of current fmridesign. List order still determines runs.
- Bidser's current event reader handles simple whitespace/mixed delimiters, but a
  synthetic quoted file with R-style row names did not parse correctly. Verify the
  exact format before deleting a manual parser; do not infer support from `.tsv`.

These are version-bound findings, not a compatibility guarantee. Source pins:
[fmrireg](https://github.com/bbuchsbaum/fmrireg/tree/8aca5ba50380840d7537f8397ab05f7f2e81a934),
[fmridesign](https://github.com/bbuchsbaum/fmridesign/tree/cfd0c309aa29ff6302e276dfc0584f5f60b6bd78),
[bidser](https://github.com/bbuchsbaum/bidser/tree/e6d09f85a206dc59db23a086c875b869b5d51891).

## Build a design before an expensive fit

Make a design-only path where useful: read metadata, events, confounds and image
headers; build the actual model and save its diagnostics before loading full BOLD.
Use one explicit run table to order scans, events, confounds and masks. Check unique
subject/session/task/run/acquisition keys, per-run TR and stored volumes, and
confound rows. Equal lengths do not prove matching identities. Record dropped or
missing units and the approved policy; do not silently fix alignment by exclusion.

For multi-phase trials, retain the original trial key, phase, onset, duration and
modulator coverage in the modeled event table. Validate units, timing origin,
overlaps and boundary events. A crop and HRF convolution can otherwise count the
same delay twice. Investigate timing with acquisition/stimulus evidence; do not
tune an offset simply to maximize the target activation.

State the centering/scaling population and transformation order for each modulator.
Preserve missingness and constant-modulator status. Centering event values does
not guarantee orthogonality after convolution, varying durations, run weighting,
or nuisance projection. Inspect the realized combined design and numeric contrast
weights; regex matches and correct vector lengths do not establish estimability.
Use the [design checks](design-decisions.md) and [confound policy](confounds.md).

## Make a pilot answer a specific question

Keep a small exact/reference fit with the same rows, mask, units and model.
Compare named estimates, scale, contrasts and uncertainty; high coefficient
correlation alone can hide bias or incorrect SEs. Verify that requested settings
are actually used. Consult the package's specialist documentation when an
experimental method is explicitly part of the analysis.

For temporal-noise checks, inspect representative runs and regions using the
actual design and fitted noise parameters. Reset histories at run boundaries.
If whitening externally, apply the same operator to response and full design.
Agreement with an independent QR solve checks coefficients conditional on that
transformation; it does not validate the noise estimator or inferential calibration.
Residual autocorrelation summaries are diagnostics, not proof of calibrated p-values.

Keep study choices explicit: nuisance counts, drift flexibility, AR order/pooling,
centering, minimum cell counts, clipping/exclusion rules, and bootstrap blocks.
Do not turn successful execution or a historical pilot comment into a default.

## Preserve a verifiable handoff

Save realized event/design columns, run/volume mapping, contrast weights, scaling,
mask/grid identity, coefficient order, resolved controls and version provenance.
Downstream analysis should consume this record rather than reconstructing a
similar formula and accidentally changing durations, coding or run selection.
Missing conditions, invalid voxels and unestimable effects remain explicit missing
outputs; zero is a possible scientific value, not a failure marker.

After writing, compare the requested outputs with the returned manifest and
inspect readable dimensions, coefficient/contrast identity, valid-mask values,
and estimate/SE pairs. A returned fit, caught export warning, existing filename,
or success marker alone is insufficient. Distinguish fitted, exported and
validated states. Bind reusable caches and completion receipts to inputs, code,
settings and environment; do not resume solely because a file exists.
