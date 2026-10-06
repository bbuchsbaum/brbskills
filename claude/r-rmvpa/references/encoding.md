# Encoding and Feature RSA

Contents: [banded ridge](#banded-ridge), [example](#runnable-banded-ridge),
[Feature RSA](#feature-rsa), [retention](#retention-and-resources).

## Banded ridge

Use `feature_sets()` → `feature_sets_design()` → `banded_ridge_model()` →
`run_banded_ridge()` for stimulus-feature groups predicting individual neural
responses. Predictors live on the **design**; brain responses live on the
**dataset**. Design `cv_labels` are bookkeeping indices, not response values.

Declare `block_var_train` and `time_series = TRUE` for run-dependent observations.
Outer folds must test every row exactly once for this family. Default outer folds
require intact blocks and use at most five folds; an explicit blocked CV object
can express leave-one-run-out. Inner folds are local to each outer training set.
With explicit fold lists, supply indices in the documented coordinate system and
meet the requested purge already: those lists are checked, not silently modified.

Choose selection metric and scopes before fitting. Response-wise alpha/theta
selection differs from shared ROI selection. A single fixed candidate skips inner
selection, so an `NA` inner score is expected. `alphas = "auto"` scales the grid
to the design; inspect `$selection_diagnostics` for saturation and poor prediction
rather than interpreting a boundary-selected penalty as well tuned.

`delta_sets` requests independently retuned leave-one-band-out predictive effects.
They are matched outer-OOF `R2_full - R2_without_band`, may be negative, and need
not sum to full-model R2. They are not additive unique/shared variance components.
Each requested reduced model adds fitting work. Do not clip negative effects.

## Runnable banded ridge

This fixture uses an explicitly constructed encoding relation and four runs.
Its purpose is API and alignment verification, not empirical validation.

```r
library(rMVPA)
set.seed(107)
n <- 48L
dims <- c(2L, 2L, 2L)
features <- matrix(rnorm(n * 6), n, 6)
brain <- features %*% matrix(rnorm(6 * prod(dims)), 6, prod(dims)) +
  matrix(rnorm(n * prod(dims), sd = 0.5), n, prod(dims))
dataset <- mvpa_dataset(
  neuroim2::NeuroVec(array(as.vector(t(brain)), c(dims, n)),
                    neuroim2::NeuroSpace(c(dims, n))),
  mask = neuroim2::NeuroVol(array(1, dims), neuroim2::NeuroSpace(dims))
)
bands <- feature_sets(features, blocks(visual = 3, semantic = 3))
design <- feature_sets_design(bands, block_var_train = rep(1:4, each = 12),
                              time_series = TRUE)
spec <- banded_ridge_model(
  dataset, design,
  outer_crossval = blocked_cross_validation(rep(1:4, each = 12)),
  tune_crossval = 2L, alphas = c(0.1, 1, 10),
  theta_method = "fixed", theta = c(visual = 0.5, semantic = 0.5),
  return_predictions = TRUE, target_batch_size = 4L
)
result <- run_banded_ridge(spec)
head(result$metrics)
result$selection_diagnostics
```

## Feature RSA

`feature_rsa_design(F = ..., labels = ..., block_var = ...)` carries an
observation-aligned feature representation; `feature_rsa_model()` predicts neural
patterns from those features using PLS, PCR, ridge, or elastic net. It is an
encoding analysis despite its name. For a similarity-derived representation,
`S` is a **similarity matrix**, not an arbitrary distance matrix; `F` overrides
`S` when supplied.

- For PLS/PCR on dependent runs, choose `ncomp_selection = "blocked"` and retain
  at least two training blocks within every outer fold. `"loo"` is the compatibility
  default. `"pve"` and `"max"` answer different selection questions.
- For ridge, `lambda_selection = "blocked"` refits centering/scaling within
  inner blocks; `"fixed"` requires one supplied lambda. Pattern-discrimination
  or rank-percentile tuning also requires blocked selection and at least two
  eligible observations in each inner assessment block. Do not transfer banded
  ridge alpha values blindly: penalty normalization differs.
- `feature_standardize = "scale"` changes feature geometry by equalizing columns.
  For amplitude-bearing PCA/eigen scores or pre-whitened features, consider
  `"center"` to preserve their relative magnitudes. Similarity-derived designs
  default to centering in the inspected version. Learn transformations only on
  eligible training rows; do not pre-standardize all rows to mimic these options.
- Pattern correlation compares matching predicted/observed spatial patterns.
  Pattern discrimination and rank percentile compare candidates jointly withheld
  in the same outer fold. `rdm_correlation` uses jointly withheld pairs. Recombining
  OOF predictions does not license comparisons to observations that trained those
  predictions. Voxel temporal correlation and global reconstruction are different
  quantities; correlation squared is not predictive R2.

Use `run_regional()` or supported searchlights for the desired scalar metrics.
`return_predictions = TRUE` retains OOF matrices and fold IDs for extraction by
`feature_rsa_predictions()`. This differs from both classifier prediction tables
and `return_rdm_vectors`. Preserve fold eligibility in any post-hoc metric.

## Retention and resources

Plan retention before a large run. Feature RSA refuses retained OOF predictions
for overlapping searchlights. Request them regionally when required. For banded
ridge, predictions, primal/dual weights, and diagnostics have explicit retention
options and a `max_retained_mb` contract. `target_batch_size` controls response
chunks; `memory_limit_mb` bounds solver intermediates and its cache separately,
so it is not a process-RSS ceiling. Inspect actual allocation provenance and
overflow behavior. A no-retention result cannot later yield saved coefficients.

Source/help pointers: `feature_sets`, `feature_sets_design`, `banded_ridge_model`,
`run_banded_ridge`, `feature_rsa_design`, `feature_rsa_model`,
`feature_rsa_predictions`; vignettes `Banded_Ridge_Encoding`, `Feature_RSA`,
`Feature_RSA_Advanced_Workflows`, `Feature_RSA_Connectivity`.
