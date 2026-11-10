# First-level scientific decisions and checks

Choose only after defining the estimand. Canonical HRF amplitude, derivative/FIR
basis response, trial-specific effects, and parametric modulations are not
interchangeable questions. For multiple HRF basis columns define a meaningful
linear summary or an appropriate F test; do not call one arbitrary basis weight
the condition response. For modulators document centering, scaling and whether
orthogonalization is performed; never accept hidden order-dependent defaults.
Duration versus amplitude modulation can change meaning even with identical labels.

Run-local onsets and runwise baseline/noise boundaries must remain consistent.
A pooled condition coefficient across runs assumes the chosen run aggregation;
a later random-effects claim does not follow merely from concatenating runs.
Prefer reproducible named contrasts built from tested coefficient names/weights.
Inspect the numeric contrast vectors and sign on known truth. Missing condition
columns can make a contrast unestimable for a subset; do not replace absent data
by a zero estimate or silently alter the contrast to keep those subjects.

When sharing slopes across runs, retain run-specific nuisance/baseline terms,
compatible signal units and explicit centering populations. A common slope is an
assumption, not runwise coefficient averaging; an unrated run adds no direct
rating-interaction information. Preserve full covariance for within-model
differences. See [synthetic design audits](design-audits.md) for timing, modulation
and rank examples before fitting data.

## Drift and task overlap

Resolve the actual drift basis and flexibility separately from HRF choice.
B-spline degree alone is not a generic high-pass cutoff. Inspect the installed
baseline builder and save runwise design columns, rank and parameters. Avoid
unexamined duplication of fMRIPrep cosine columns with a separately generated
drift basis. If filtering/residualizing outside the joint GLM, apply compatible
operations to data and task/nuisance design and account for degrees of freedom.
Low-frequency task regressors can be lost to overly flexible drift removal.

## Temporal noise

Choose an appropriate supported temporal-noise/variance estimator and check
residual autocorrelation by representative voxel/region and run. Run boundaries
must not produce cross-run AR histories. Volume weighting/censoring can change
both design and effective uncertainty; verify compatibility rather than combining
options because each exists separately. OLS is suitable for a controlled iid
smoke test, not an automatic default for BOLD inference. Sketching/low-rank methods
need accuracy and uncertainty checks against a reference on held-out sampled data.

Verify what residuals an accelerated or compressed fit actually returns before
using them to estimate noise. With a fixed whitened design, coefficient/covariance
agreement with independent QR checks algebra conditional on that whitening; it
does not validate the estimated noise model or standard errors. Residuals after
design projection need not have zero expected autocorrelation even under white
errors. Compare diagnostics to the fitted design's projection expectation or
matched simulations, retaining run boundaries and uncertainty.

Check residual-pooling units and weights: low-mean signals can dominate after
percent-signal scaling, and high-variance voxels can dominate raw pooling.
Record invalid/constant series and exclusions. Treat lag-budget sensitivity,
boundary estimates and unstable corrections as evidence to investigate. Reduced
noise-estimation designs or equal-variance pooling introduce different assumptions;
a plausible AR coefficient alone is not evidence of calibration.

## Pre-fit validation

Check nobs and timestamps, missing/nonfinite values, event counts per run, columns
and names, rank, conditioning, nuisance-task correlation and residual degrees of
freedom. Estimability requires a contrast to lie in the row space of the design;
numeric contrast dimension alone is insufficient. Inspect design and timing plots.
A warning is evidence to investigate, not an instruction to drop covariates.
`preflight()` adds native structure checks but does not substitute scientific QC.

## Pilot and output

Pilot distinct acquisition/design strata; inspect coverage/alignment/brain masks,
contrast signs, estimates/SE units, residual behavior, and plausibility without
optimizing for significant activation. Preserve scalar settings and actual design
columns/weights for reproducibility. Check invalid voxels/df/variance and mark
missing outcomes. Export beta plus SE or var and required statistic/df maps.
Use known-truth simulations for implementation verification and a real holdout for
scientific acceptance. Trialwise/LSS or connectivity analyses require a selected
specialist recipe and capability verification, not this GLM recipe relabeled.
For trial patterns and RSA, use the [decision and validation guide](trial-patterns-rsa.md)
before selecting a package-specific implementation.
