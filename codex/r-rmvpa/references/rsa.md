# RSA and pair relationships

Contents: [model choice](#choose-the-measurement-and-statistic),
[example](#runnable-rsa), [pairs](#pairs-modulation-and-connectivity),
[inference](#inference-boundaries).

## Choose the measurement and statistic

`rsa_design()` specifies model RDMs; `rsa_model()` measures neural relationships
and compares them with those predictors. These are distinct choices:

- `distmethod` chooses Pearson or Spearman neural pattern correlation.
- `measure = "distance"` uses correlation distance; `"similarity"` uses correlation.
- `regtype = "pearson"` or `"spearman"` tests marginal correspondence. `"lm"`
  performs multiple regression; by default its outputs are t statistics.
- `statistic = "beta"` with ordinary unconstrained `regtype = "lm"` returns raw
  coefficients. Named coefficient `contrasts` require this mode. Inspect the
  sanitized names in `design$model_mat` before constructing weights.
- `pattern_center = "stimulus_mean"` changes the measured patterns. It does not
  merely relabel a correlation distance or make it crossvalidated.

Declare item order and whether within-run pairs are eligible. RDM axes must
correspond to observations actually used; matching matrix dimensions alone is
insufficient. Do not silently substitute correlation distance for crossnobis or
squared Euclidean distance. Where crossvalidated contrasts are the question,
consult `msreve_design()`/`contrast_rsa_model()` and their centering, whitening,
and normalization contracts.

Inspect nuisance variation **after pair filtering**. A same-run/different-run RDM
is constant if only cross-run pairs remain, so adding it can make the regression
rank deficient. Reconcile pair eligibility with the intended nuisance adjustment;
do not automatically reintroduce within-run pairs just to make a fit succeed.

## Runnable RSA

```r
library(rMVPA)
set.seed(106)
sample <- gen_sample_dataset(c(3, 3, 3), 48, blocks = 4, nlevels = 2)
item_features <- matrix(rnorm(48 * 3), 48, 3)
rdm <- stats::dist(item_features)
design <- rsa_design(~ semantic, list(semantic = rdm),
                      block_var = sample$design$block_var,
                      keep_intra_run = FALSE)
spec <- rsa_model(sample$dataset, design,
                   distmethod = "pearson", regtype = "spearman")
roi <- neuroim2::NeuroVol(array(1L, c(3, 3, 3)),
                         neuroim2::space(sample$dataset$mask))
result <- run_regional(spec, roi)
result$performance_table
```

This is a descriptive single-RDM association on random data, not an inference
example. An ordinary RSA fit does not acquire predictive cross-validation just
because within-run pairs were excluded.

## Pairs, modulation, and connectivity

Use `pair_rsa_design()` for explicit pair geometry: within-domain lower triangles
or rectangular between-domain pairs. Between-domain designs require `row_idx_a`
and `row_idx_b` mapping the domains into the neural dataset; do not concatenate
and then discard the mapping. Repeated item IDs can remain distinct observations.

The `model` list contains relationship templates; `nuisance` adds background
terms. For relational modulation, `modulation = list(item = ~ b.precision *
b.vividness)` multiplies the `item` template by retrieval attributes from
`features_b`. Pair metadata exposes `a.row`, `b.row`, `a.item`, `b.item` and
prefixed feature columns. Use symmetric formulas for within-domain relationships.
To standardize at the observation level, transform feature columns before pair
expansion; formula transformations otherwise act on pair metadata.

For similarity coefficients, use `rsa_model(..., measure = "similarity",
regtype = "lm", statistic = "beta")`. Retrieval-observation intercepts can be
expressed as `nuisance = ~ factor(b.row)`. Check estimability on complete eligible
pairs. These are participant-level relational effects; they do not correct bias
in first-level measurements or provide calibrated population standard errors.

Use `vector_rsa_model()` for observation-level RDM profiles; it has its own design
and output. For model-space connectivity, request `return_fingerprint = TRUE`
before fitting RSA and consult `model_space_connectivity()`. Fingerprints exclude
declared nuisance predictors. Geometry sharing is not directed or causal coupling.

## Inference boundaries

- RDM cells share items. Pair-count t-test degrees of freedom are not valid
  independent-observation degrees of freedom. `rsa_design_diagnostics()` screens
  rank, collinearity, and effective item support; it is a heuristic, not inference.
- `run_permutation_searchlight()` permutes item labels for RSA. For multiple
  regression predictors, including nuisance terms, it requires explicit
  `permutation_control(rsa_null = "joint")`. This tests joint no-association.
  Selecting one `metric` does **not** turn it into a conditional coefficient test.
  Raw item permutations destroy nuisance associations; conditional individual
  coefficient inference is not implemented by that route.
- Single-predictor regression and marginal correlation routes have different
  null scope. State the actual null, statistic, exchangeability scheme, spatial
  sampling, and correction family rather than calling every output a unique effect.
- Defaults pool null values from subsampled centers (`perm_strategy = "iterate"`)
  with covariate adjustment. `"searchlight"` computes whole searchlights but still
  feeds the pooled-null pipeline. Neither is automatically a per-center permutation
  test or a max-statistic FWER procedure. Five default permutations are not a
  universal adequate inference budget; choose and validate calibration for the design.
- `correction = "fdr"` adjusts within each metric's spatial map, not across
  multiple metrics. Within-block shuffling, circular shifts, and global shuffling
  impose different exchangeability assumptions. Do not select the fastest scheme
  without checking those assumptions.

Source/help pointers: `rsa_design`, `pair_rsa_design`, `rsa_model`,
`rsa_design_diagnostics`, `permutation_control`, `run_permutation_searchlight`;
vignettes `RSA`, `Contrast_RSA`, `Temporal_Confounds_in_RSA`,
`Model_Space_Connectivity`.
