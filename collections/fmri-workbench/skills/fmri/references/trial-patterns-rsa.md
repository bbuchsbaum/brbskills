# Trial patterns and representational comparisons

Read for trialwise GLMs, decoding or representational similarity analysis (RSA).
This guide supports choosing and validating a specialist implementation; it does
not supply a default model, package installation or qualified end-to-end pipeline.
For an rMVPA implementation, use the independent `r-rmvpa` skill if installed;
its RSA and extension references cover package-specific routes and limitations.

## Define patterns and independent repetitions

Specify whether each pattern represents an item, trial, condition or repetition.
Keep stable IDs through event sorting, design columns, exported betas, behavioral
joins and representational dissimilarity matrices (RDMs). Verify repetitions and
run/session assignment before choosing crossvalidation. Distinct observations in
one fit need not have independent estimation errors. Select partitions that meet
the estimator's independence assumptions; preserve held-out boundaries in feature
selection, scaling, noise estimation and model tuning.

For least-squares-all versus least-squares-separate (LSS), state which coefficients
are estimated jointly and which non-target trials are pooled in each target fit.
Grouping by condition/phase, retaining separate non-target regressors, intercepts
and regularization all affect the estimate. Verify the installed public API, and
compare target coefficients on a small synthetic design with an independent fit
of the exact same model, whitening and penalty. A successful pilot's grouping or
ridge setting is not a general default. When appropriate, check that trial columns
sum to the corresponding aggregate design before changing the grouping.

## Qualify signal support and noise

Record preprocessing, smoothing, units and valid sample support. A mask does not
guarantee finite, varying time series or valid denominators for percent-signal
scaling. Save excluded sample IDs/counts and the criterion. Separate temporal
whitening of observations from spatial whitening of patterns; record whether the
spatial precision is identity, diagonal or a regularized full estimate.

Check full versus compressed residual semantics and residual-pooling weights.
Compare temporal diagnostics with the design-projection expectation or matched
simulations. Conditional agreement with whitened QR verifies coefficient arithmetic,
not the adequacy of whitening. A smaller noise-estimation design may leave trial
variation in its residuals; equal-variance pooling changes weights. Treat these
as explicit choices needing evidence, not repairs justified by a plausible AR value.

## Distances and explanatory models

Choose the distance to match the question and available independent repetitions.
Crossvalidated squared-distance estimates can legitimately be negative; do not
clip them or take their square roots. State normalization and spatial metric.
Audit additive run offsets: comparisons across unmatched runs can mix run effects
with item differences. Exclude, balance or explicitly model them with a justified
design; a run label alone does not remove every confound.

Define each predictor at the item-pair level. For a behavioral variable, the
*difference between pair members* and the *mean of their values* answer different
moderation questions. Include the corresponding lower-order terms with an
interaction; centering does not replace them. Specify how repeated measurements
map to the sessions contributing to each neural distance. Keep pair IDs, complete-
pair masks, centering/scaling populations and support differences between models.
Joint RDM regression estimates conditional associations, not an orthogonal variance
partition or a causal effect.

## Validate computation and inference separately

Compare a small ROI/searchlight against independent matrix calculations. Check
session-exchange symmetry for a symmetric estimator, consistent item relabeling,
negative estimates, known synthetic effects, and rejection of insufficient support.
Specify searchlight geometry, units, boundary handling, minimum support and the
denominator of any support fraction; these are analysis choices, not fixed values.

RDM pairs share items and are dependent. Ordinary independent-row regression
P values do not establish RSA inference. Choose a method whose resampling/model
assumptions match the intended generalization to participants, items or both, and
account for the spatial/model comparison family. Univariate fixed-effects Z
pooling is not automatically valid for RSA correlations or regression coefficients.
See [Schütt et al. (2023)](https://elifesciences.org/articles/82566) for inference
on representational geometries and [Diedrichsen et al.](https://arxiv.org/abs/1607.01371)
for crossvalidated Mahalanobis distance distributions.

These decision checks generalize workflow observations in
[brbskills #6](https://github.com/bbuchsbaum/brbskills/issues/6). That report is
evidence from a particular implementation, not a calibration guarantee for a new
dataset, distance estimator or temporal-noise model.
