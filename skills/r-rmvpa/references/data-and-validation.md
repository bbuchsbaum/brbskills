# Data and validation

Use this route for data assembly, leakage, folds, matrix targets, or geometry
errors. Local installed help takes precedence over these snapshot examples.

## Data contracts

`mvpa_dataset(train_data, test_data = NULL, mask)` takes `neuroim2::NeuroVec`
images and a `NeuroVol` mask. A plain matrix is not a drop-in image argument.
Image layout is x × y × z × observation; ROI feature matrices are observation ×
feature. Images and masks must share full spatial geometry, including transforms,
not merely array dimensions. Preserve existing NIfTI geometry when reading files;
do not reconstruct a space with guessed voxel sizes to silence a mismatch.

For a synthetic observation × voxel matrix, this example deliberately uses an
identity space. It also illustrates matrix targets and distinct CV labels.

```r
library(rMVPA)
set.seed(104)
n <- 48L
dims <- c(3L, 3L, 3L)
X <- matrix(rnorm(n * prod(dims)), nrow = n)
dataset <- mvpa_dataset(
  neuroim2::NeuroVec(array(as.vector(t(X)), c(dims, n)),
                    neuroim2::NeuroSpace(c(dims, n))),
  mask = neuroim2::NeuroVol(array(1, dims), neuroim2::NeuroSpace(dims))
)
metadata <- data.frame(run = rep(1:4, each = 12), row_id = seq_len(n))
targets <- cbind(semantic = rnorm(n), visual = rnorm(n))
design <- mvpa_design(metadata, cv_labels = seq_len(n), targets = targets,
                      block_var = ~ run)
cv <- blocked_cross_validation(design$block_var)
stopifnot(isTRUE(all.equal(unname(get_feature_matrix(dataset)), unname(X))))
```

For categorical decoding, use a factor response with `y_train = ~ condition`.
Numeric labels can be interpreted as regression targets. Do not supply both
`y_train` and `cv_labels`. For vector-valued outcomes, pass a numeric matrix to
`targets`, not a formula. `y_train(design)` continues to return the CV labels;
models requiring matrix targets use `model_targets(design)`.

For external test data, align `test_data`, `test_design`, `y_test` or
`targets_test`, and feature order explicitly. Check how the selected model uses
external partitions; merely supplying a test image does not establish independence.
Use `mvpa_surface_dataset()`, `mvpa_clustered_dataset()`, or the multibasis
constructors for their actual data classes, consulting their installed help.

## Folds and transformations

- `blocked_cross_validation(block_var)` holds out whole blocks. For new-run
  generalization, use run IDs; for new-participant generalization, hold participants
  out. Repeated items and sessions may require a different grouping. Make run IDs
  unique across participants when pooling observations.
- `split_by` supplies reporting subsets. It does not hold those groups out of
  training. Inspect actual train/test indices for overlap, coverage, class support,
  and the claimed grouping. Repeated assessments are not additional independent
  observations.
- Use custom folds when one blocking vector cannot express the design. Inspect
  `custom_cross_validation()` and `crossval_samples()` help for the installed
  representation; do not invent an `rsample` interchange format.
- Outer CV does not repair preprocessing learned from all observations. Fit
  feature selection, scaling, PCA, alignment, nuisance regression, and tuning on
  training rows at the appropriate level. Even unsupervised transformations can
  expose held-out observations. A fixed external feature representation has a
  different provenance from one learned on the analysis data.
- Inner validation must also respect dependence. For Feature RSA, explicitly
  choose blocked inner selection when rows are run-dependent; its compatibility
  defaults are not a methodological recommendation. For banded ridge, declare
  `block_var_train` and `time_series` on the design, and inspect purge semantics.

`validate_analysis(spec)` returns pass/warn/fail checks for supported families.
Address failed checks and explain material warnings. Small synthetic examples may
legitimately trigger sample-size warnings. A pass cannot prove actual row identity,
no leakage upstream, appropriate null hypotheses, or valid group inference.

Source/help pointers: `mvpa_dataset`, `mvpa_design`, `model_targets`,
`cross_validation`, `validate_analysis`; vignettes `Constructing_Datasets`,
`CrossValidation`, `FeatureSelection`.
