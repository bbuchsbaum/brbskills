# Subject estimates to group analysis through NIfTI

Use this recipe when exporting fmrireg fits for fmrigds. It uses public APIs
reviewed on 2026-09-27; check the installed versions before applying it.

Contents: [estimand](#choose-the-observation-and-maps),
[export](#export-separate-effect-and-se-files),
[geometry and coverage](#verify-geometry-and-coverage),
[import](#build-the-fmrigds-source), [group model](#choose-the-group-model),
[evidence](#review-and-verification).

## Choose the observation and maps

For the ordinary independent-subject group model, produce one signed, scalar
contrast estimate per person and estimand, with its matching contrast SE. Combine
runs within person using the declared first-level model or a justified pooling
model; preserve its uncertainty. Repeated runs/sessions are not extra independent
subjects. A paired A-minus-B contrast is often best formed at first level, where
coefficient covariance is available. SE(A-minus-B) is not generally
sqrt(SE(A)^2 + SE(B)^2).

Use unthresholded **contrast beta + contrast SE**, with common contrast sign,
numeric weights, HRF interpretation and units. Raw regressor betas, t/z/p maps,
and F statistics are different quantities. An omnibus F test does not supply a
signed effect with an SE for this route. Preserve t/df and other diagnostics when
needed, but do not substitute them for effect/uncertainty maps.

## Export separate effect and SE files

For an existing validated fit containing the requested contrasts:

```r
files <- fmrireg::write_results(
  fit, path = subject_output_dir, subject = subject_id, task = task_id,
  space = verified_space_label, desc = analysis_id,
  format = "nifti", strategy = "by_stat", save_betas = FALSE,
  contrasts = requested_contrasts, contrast_match = "exact",
  contrast_stats = c("beta", "se"), overwrite = FALSE
)
stopifnot(all(c("beta", "se") %in% names(files)))
beta_path <- files$beta$nifti
se_path <- files$se$nifti
beta_json <- files$beta$json
se_json <- files$se$json
stopifnot(all(file.exists(c(beta_path, se_path, beta_json, se_json))))
```

`by_stat` writes one beta file and one SE file per subject, with contrasts on the
fourth axis. Read each JSON `ContrastOrder`; do not infer volume order from the
requested selector order. Require identical beta/SE order and the same order for
all subjects. A singleton fourth axis may be read as 3D.

`by_contrast` with several statistics instead stacks **statistics** on that axis.
Do not feed that combined beta/SE/t image to the importer as if each volume were a
contrast beta. If separate files per contrast are needed, export one contrast at
a time with `by_stat` into distinct contrast directories. Prevent path collisions:
the by-stat filenames themselves do not contain a contrast ID.

For native jobs, `reduce_write_results(format="nifti", stats=c("beta","se"),
...)` uses this by-stat layout. Its default beta/tstat pair omits SE; request SE
explicitly. Inspect job metadata and returned paths. The reducer can also write
raw regressor betas (`files$betas`); those are not `files$beta` contrast maps.

Retain the sidecars, actual fitted coverage mask, and a manifest keyed by subject,
unit, contrast ID and volume index. Add model/design and contrast weights, scaling,
run aggregation, spatial reference, input/code hashes, package commits and QC
status. Sidecars provide useful labels/inference metadata but do not replace this
record. Keep failed/missing contrasts explicit: a writer can omit unavailable
outputs, and a failed export can leave partial files. Compare expected versus
written maps before marking a subject ready.

## Verify geometry and coverage

`space=` labels an output; it does not register or resample it. Inputs must already
represent corresponding anatomy on the intended common grid, or pass through a
documented, validated spatial transformation with an explicit uncertainty policy.
SE/variance propagation through interpolation is not established by merely
resampling an SE image like an effect image.
Fitting preprocessed BOLD on the final common grid avoids a later SE-map
interpolation step, but still requires registration and coverage QC. Review
anatomical extraction, EPI-to-anatomical alignment and template alignment
separately where applicable; affine normalization can leave local mismatch.

Check **every** beta, SE and mask: first three dimensions, voxel-to-world affine,
voxel sizes/units and spatial reference. Verify qform/sform consistency where
applicable. Equal array lengths or identical `space-` labels are insufficient.
The reviewed fmrigds NIfTI importer uses the first image's geometry; it does not
compare all subsequent image or mask affines. A successful import is not spatial
validation.

fmrireg fills outside-mask voxels with zero. fmrigds includes the entire grid if
no mask is supplied, and zero is a valid observation. Carry the original fitted
coverage masks. An approved intersection mask is a simple common-support choice;
it changes the search domain and must be recorded. For partial coverage, encode
unavailable subject/voxel/contrast values as `NA` in both beta and SE in derived
handoff files, using coverage masks and validity diagnostics. Preserve originals.
Do not identify missingness from `beta == 0` or hide invalid SEs with an epsilon.

The checked fmrigds main revision has no `MaskPolicy(zero_is_missing=...)` option;
some newer branches do. Even where available, that option is not a replacement
for known coverage masks when real zero effects are possible. Verify coverage
threshold semantics: this main revision pools subject and contrast axes for a
group mask threshold. Apply contrast-specific coverage separately if required.
Retain samplewise contributing N; positive finite SE is required for precision
weighting, independently of finite beta coverage.

## Build the fmrigds source

Build `subject_files` from the checked manifest, one row per independent person,
with columns `subject`, `beta`, `se`, `beta_json`, `se_json`. Pair by the complete
analysis keys before constructing it; never sort beta and SE paths independently.

```r
stopifnot(!anyNA(subject_files$subject), !anyDuplicated(subject_files$subject),
          all(file.exists(c(subject_files$beta, subject_files$se))))
read_order <- function(p) {
  as.character(jsonlite::read_json(p, simplifyVector = TRUE)$ContrastOrder)
}
contrast_ids <- read_order(subject_files$beta_json[1])
stopifnot(length(contrast_ids) > 0L, !anyDuplicated(contrast_ids))
for (p in c(subject_files$beta_json, subject_files$se_json)) {
  stopifnot(identical(read_order(p), contrast_ids))
}
src <- fmrigds::nifti_source(
  beta = subject_files$beta, se = subject_files$se,
  subjects = subject_files$subject, contrasts = contrast_ids
)
plan <- fmrigds::gds(src, format = "nifti", mask = group_mask_path)
fmrigds::explain(plan)
```

Explicit subjects declare that beta/SE vectors are already aligned; they bypass
filename pairing safeguards. Therefore validate identity in the manifest first.
The current importer can pair BIDS filenames automatically, but explicit reviewed
keys avoid dependence on filename heuristics. Sidecar labels are supplied here
explicitly; the importer does not discover `ContrastOrder` for you.

The native NIfTI source takes `se`, not variance. It reads an SE assay; variance
can be derived with `fmrigds::derive(plan, "var")`, and precision-aware reducers
derive `var = se^2` when needed. Do not put variance files in the `se` slot. GDS
arrays are sample × subject × contrast. Inspect one block against the source
images for values, mask index order and both axis labels before cohort fitting.

## Choose the group model

Choose the population estimand and model before inspecting significant maps.
For an appropriate equal-weight one-sample model, `fmrigds::one_sample(plan)`
constructs a lazy group OLS plan; `group_ols(plan, ~ group + age, col_data=...)`
adds a reviewed subject-keyed design. These use between-subject variation for
uncertainty. Genuine first-level SEs also allow an appropriate precision-aware
random-effects meta-analysis via `reduce(plan, method="random")`. Fixed-effects
precision pooling is not the default population model.

Importing SE maps does not make equal-weight OLS precision weighted. For a small
one-sample integration test, independently compare the group mean, between-person
SE, t, contributing N and df against arithmetic on the imported effects. Keep
this arithmetic check distinct from validation of the scientific model.

Compute the chosen plan after model/cohort checks. Preserve actual N, df,
uncertainty and diagnostics, and apply the declared multiplicity correction over
the full search family. OLS returns names such as `coef:(Intercept)` and
`se_coef:(Intercept)`; inspect the result's assays before exporting. Separate
contrast slices do not by themselves model within-person covariance. A repeated
design needs a supported model or a justified within-person reduction.

## Review and verification

Reviewed sources: fmrireg
[`write_results`](https://github.com/bbuchsbaum/fmrireg/blob/8aca5ba50380840d7537f8397ab05f7f2e81a934/R/bids_export.R),
fmrigds
[`nifti_source` and adapter](https://github.com/bbuchsbaum/fmrigds/blob/829139e4bbc3dadbda13710e0bfcccad2aa6a1a4/R/adapter-nifti.R),
[`group_ols` / `one_sample`](https://github.com/bbuchsbaum/fmrigds/blob/829139e4bbc3dadbda13710e0bfcccad2aa6a1a4/R/scalar-map-workflow.R).
fmrireg also has `format="gds"`; at this pin that exporter packages regressor-level
assays, so it is not interchangeable with this selected-contrast NIfTI handoff.
No conversion from `collect_results()` to a ready cohort GDS is assumed here.

A tiny synthetic fit/export/import/group arithmetic check accompanies the
fmrireg skill. It checks this route with multiple subjects, contrasts and a sparse
mask. It does not validate study registration, coverage choices, temporal-noise
calibration, or a production group model. Re-run in the selected package environment.
An actual one-run cohort handoff also leaves within-person run pooling and
repeated-session handling untested; qualify those paths separately before
claiming support from that execution.
