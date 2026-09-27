# Group model decisions

## Match reducer to the question and input

For a population mean of commensurate subject effects, consider the appropriate
unweighted subject model or a justified precision-aware random-effects model.
The choice depends on effect units, first-level variance quality, heterogeneity,
small-sample behavior and the target population; don't select weighting merely
because SEs are available. Fixed-effects pooling answers a different question.
Meta-regression adds covariates but does not automatically solve dependence,
heteroskedasticity, confounding or uneven missingness.

A signed z or t+df input can support an evidence-combination question; a p-only
input loses direction. Neither reconstructs a unique effect and variance. Do
not invent SE=1 to make an inverse-variance reducer run. Check assay names and
statistic distributions, not filename hints. An unweighted beta-only group model
is a legitimate separate path when supported and scientifically appropriate.

## Repeated measurements

The reviewed restricted Gaussian methods include lmm:ri, lmm:ri_slope1,
lmm:ri_knownvar and lmm:ri_slope1_knownvar. The fast path assumes shared observation
layout/fixed/random design across samples, one grouping factor, and at most the
supported single random slope. It is not an arbitrary lmer parser. Knownvar
methods use diagonal sampling variance plus estimated components; correlated
first-level estimates are not rendered independent by storing a diagonal var assay.
Verify current missing-layout, covariance, fitting and theta-mode contracts.
Do not flatten sessions/conditions/runs into extra participants. A within-person
difference needs its covariance or a justified direct first-level contrast.

## Check the design and missingness

Preserve keyed subject/observation order, cohort flow, factor reference levels,
centering, covariate availability and the estimand vector. Check design rank,
collinearity and effective N per sample. Do not silently vary the model by voxel
when different covariates are missing. Group masks/coverage are part of the
family definition, not chosen after finding activation. Convergence/variance
boundary warnings and heterogeneity estimates must be retained where applicable.

## Multiplicity and interpretation

Specify mask/search domain, contrast/estimand family, sidedness, correction method
and alpha. Verify whether a native posthoc acts per contrast, per coefficient or
across a broader family. Spatial/block streaming must not fragment a prespecified
family into independently corrected chunks. For permutations verify the null
symmetry/exchangeability and repeated-measures blocks; do not promise any particular
max-T/TFCE implementation before locating it in the installed registry.

Keep uncorrected p/statistics, corrected values and rejection mask as distinct
artifacts. A thresholded t/z map plus a minimum extent is not a corrected test.
Finite-sample approximations and model assumptions belong in the methods, not
hidden by attractive figures. Do not conflate population inference and combined
evidence about a fixed collection of subjects.

## Cohort examination, not outcome-driven exclusion

Where supported, `examine_group()` distinguishes data validity, conditional
surprise and influence on a selected estimand. Priority orders review; it does
not classify participants for removal. The documented random-effects examination
uses an initial fixed-heterogeneity approximation with later exact refits for
retained cases; preserve those availability/approximation flags. Exclude only
under approved validity criteria. Report leave-one-out or alternative-model
sensitivity as sensitivity, not a replacement primary result chosen for significance.
