# Pattern models and confirmation

Contents: [fit](#fit-and-retain), [example](#runnable-pattern-fit),
[interpretation](#interpretation), [confirmation](#independent-confirmation),
[group](#group-analysis).

## Fit and retain

`pattern_model()` is an experimental forward reduced-rank model relating targets
to neural features, with a training-estimated residual covariance. It derives
decoding and encoding readouts from that fit. Supply categorical responses through
`mvpa_design(y_train = ...)`, or matrix targets through `targets` and
`model_targets()`. CV labels are separate from matrix targets.

`rank = "auto"` selects predictive rank with nested CV; a fixed rank does not
test that dimensionality statistically. `penalty$sparse` acts on forward-pattern
rows; `signed_smooth` penalizes signed graph differences. `support_smooth` is
reserved and rejected, not a synonym for signed smoothing. Preserve feature
identities, including basis channels, when constructing graphs or mapping outputs.

Use `run_global()` for one whole-domain model; regional fits estimate separate
models. Searchlight outputs are scalar summaries. Set `return_fits = TRUE` for
fold fits and ledgers, and `refit = TRUE` when a full-training descriptive or
deployment fit is required. Refitting does not create new held-out evidence.

## Runnable pattern fit

```r
library(rMVPA)
set.seed(108)
sample <- gen_sample_dataset(c(2, 2, 2), 48, blocks = 4, nlevels = 2)
metadata <- data.frame(condition = factor(rep(c("a", "b"), 24)),
                       run = rep(1:4, each = 12))
design <- mvpa_design(metadata, y_train = ~ condition, block_var = ~ run)
spec <- pattern_model(
  sample$dataset, design,
  crossval = blocked_cross_validation(design$block_var),
  rank = 1L, noise = list(type = "diag"),
  return_predictions = TRUE, return_fits = TRUE, refit = TRUE
)
result <- run_global(spec)
result$performance_table
```

This is a small interface check on random observations. It does not qualify
rank selection, covariance calibration, or whole-brain performance.

## Interpretation

Use the fitted object's public methods, checking current signatures:
`model_patterns()`, `model_importance()`, `pattern_haufe()`, `rotate_patterns()`,
`region_importance()`, and prediction methods. Forward patterns, decoding weights,
Haufe patterns, and conditional model information are distinct quantities. Sparse
nonzero coefficients do not imply significant voxels; a CV-selected rank does not
imply supported population dimensionality.

Local-restricted prediction uses a region's measurements within the shared task
subspace. It is different from an independently fitted regional model or a
locally adapted covariance. Missing retained fits must be reported instead of
reconstructed as if the original fits were available. Keep original units and
distinguish screened features, outside-mask features, and estimated zeros.

Fold-resolved ledgers preserve all assessments; pooled ledgers count each tested
observation once. Report the metric's baseline: predictive R2 is not squared
correlation. Observation weights affect fitting and selection, while the inspected
implementation reports unweighted performance metrics; describe both choices.

## Independent confirmation

`pattern_confirm()` estimates unpenalized loadings on genuinely independent
observations in a frozen discovery basis. Obtain that basis from an eligible fit
or global result with a refit; it is not confirmation of the training sparse map.
Its required provenance includes:

- Globally meaningful unique `observation_ids` for confirmation, and complete
  `discovery_ids` covering selection, tuning, and preprocessing.
- Ordered `feature_ids` and a meaningful `preprocessing_id`, preserving units.
- Independent run/block labels for block-based error models and separately coded
  nuisance regressors. Block labels do not automatically add nuisance intercepts.

IDs detect overlap but cannot establish biological or preprocessing independence.
Renaming training rows, using in-sample residuals, or sharing a data-fitted
normalization does not create an independent confirmation set. If independence is
unavailable, deliver descriptive/predictive outputs and state the missing condition.

Choose `confirmation_plan(error = ...)` for the actual sampling assumptions.
Independent Gaussian homoskedastic errors permit the documented exact tests;
block-robust and sign-flip methods have different, approximate contracts. Verify
support for weights and available covariance. Nonuniform observation-weight
confirmation is refused in the inspected source. Component tests depend on the
frozen basis; omnibus tests and multiplicity families have separate meanings.
Neither `pattern_confirm()` nor `pattern_component_tests()` reports a supported
population rank. An omnibus signal test is not a rank hypothesis test.

## Group analysis

`pattern_group()` takes independent subject confirmations, an independently fixed
reference basis, and compatible feature units. Subject bases must span the same
target subspace. Spatial mappings must be explicit one-to-one correspondences;
arbitrary Procrustes alignment, interpolation of SEs, or many-to-one pooling would
change the contract. Use participant count for group degrees of freedom.

The `random` and `fixed` effects options support different claims. Inspect required
subject count, covariance availability, and returned NA tests. Save complete group
objects with `saveRDS()`. Proposed crossform/state-adapter protocols in planning
documents are not installed rMVPA functions.

Source/help pointers: `pattern_model`, `pattern_control`, `model_targets`,
`pattern_confirm`, `confirmation_plan`, `pattern_component_tests`, `pattern_group`;
vignettes `Pattern_Model`, `Pattern_Confirmation`, `Pattern_Group`.
