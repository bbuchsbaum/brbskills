# Synthetic first-level design audits

Use these checks when event meaning, missing modulators or interaction support is
uncertain. Run `Rscript scripts/smoke_design.R` from this skill directory for the
small synthetic examples. They use fmrireg's public design API and independent
linear algebra; they neither select a scientific model nor qualify temporal noise.

## Main events, modulation and missingness

The example retains a main event for each trial, centers observed scores within
the synthetic run, uses zero *modulation amplitude* for missing scores and includes
a separate missingness column. Zero amplitude does not mean a zero observed score.
It assumes a common observed-score slope and a separate average missing-trial
response, which may not suit informative missingness. A constant or wholly missing
score makes that run's centered slope unavailable. Sharing a slope across runs
does not create score information in an unrated run; any borrowed estimate relies
on the common-slope assumption. Other missingness models remain possible.

Check the realized columns against the sum of independently constructed per-trial
columns, then recover known coefficients with QR. This distinguishes an intended
amplitude model from formula coding that only looks plausible. An iid recovery
test does not validate an AR estimator or real-data uncertainty.

## Interaction support

The example pairs a full-rank feature matrix with a two-level score having few
nonmodal observations. The joint main-plus-interaction design is rank-deficient:
the small subgroup cannot identify all feature-specific slope differences.
The script checks the null direction and its persistence after a shared linear
HRF convolution. Audit the actual design's singular values, coefficient/contrast
estimability, conditioning and residual degrees of freedom; do not turn this
example's feature count or rating distribution into a cutoff.

## Clock alignment and event meaning

Sampling times are explicit. A synthetic reference offset illustrates equivalent
ways to represent the same event-to-sample timing; derive the real offset from
preprocessing metadata rather than copying the example.

At that fixed clock, a routine boxcar and a shorter component boxcar have different
responses despite identical onset labels. Compare plausible duration models with
matched parameter counts and distinguish an average routine response from a
stimulus-component response. Their fit difference does not establish the true HRF.

The script projects a known response-locked HRF signal into a model omitting that
response event. A nonzero coefficient on an adjacent phase illustrates omitted
signal allocation; it is not the fraction of an observed activation caused by a
button press. Near-zero correlation between included columns cannot rule this out.
Repeat relevant sensitivity checks across plausible HRFs and timings. Adding
response and phase terms can itself make their coefficients poorly estimable;
inspect the combined design instead of calling a remaining effect purified.

## Handoff

Record source-event and derived-event identity, timing reference, centering and
missingness choices, realized columns, rank/conditioning, estimable contrasts and
unsupported terms. Keep beta and SE/statistic maps jointly inspectable. For a
group handoff, combine repeated estimates within participant using an appropriate
covariance model before treating participants as independent units; neither
averaged t maps nor fixed-effects pooling establishes population inference.
