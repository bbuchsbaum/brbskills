# Model adequacy and GLMM-specific checks

## A diagnostic sequence

First verify data construction, then mean structure and dependence, then distributional fit, then influence and sensitivity. Diagnostic tests complement plots and domain knowledge. They are not a sequence of null hypotheses that must all be nonsignificant.

For Gaussian LMMs examine conditional residual-versus-fitted/predictor plots, Q–Q behavior, heteroscedasticity, nonlinear trends, and residual dependence within groups/time. Raw outcome normality is not the assumption. Random-effect estimates are shrunken, correlated with their estimation error, and not independent observations for a naive normality test. Investigate influential groups as well as rows; dropping a group is a sensitivity analysis unless there is a documented data error. [FAQ; LMM-PAPER]

## Outcome representation

For binomial models use Bernoulli 0/1 observations or `cbind(success, trials-success)` for genuine binomial counts; probabilities without known denominators do not define binomial sampling information. Validate integer nonnegative counts and positive denominators. For rates modeled as counts, an `offset(log(exposure))` expresses a coefficient fixed at one and requires strictly positive, meaningful exposure. Aggregation is not innocuous when covariates, clustering, or independence assumptions change. [GLMM]

For Poisson models, extra-Poisson variation may reflect missing structure, heterogeneity, dependence, or distributional mismatch. Negative binomial, observation-level variation, and zero-inflation models imply different mechanisms. Excess observed zeros relative to a simple model do not establish a separate structural-zero process. For individual Bernoulli data, do not treat an observation-level random effect as a general identifiable extra-binomial dispersion parameter. [FAQ; ECO]

`glmer.nb` estimates a negative-binomial shape parameter, conventionally theta. That is **not** lme4's random-covariance `getME(fit,"theta")`. The documentation identifies limitations of dispersion-parameter inference; report what uncertainty your procedure actually includes. [NB]

## Simulation residuals: do not trust inherited defaults

The DHARMa manual consulted states that version 0.5.0 changed the default to simulations conditional on all fitted random effects and introduced `simulateREs`. Older examples may rely on lme4's `re.form` behavior instead. Check the installed function's formals/help. Use the included version-aware wrapper and record its settings.

```r
# model_audit.R must already be sourced.
diag <- dharma_mermod(g, mode = "conditional", n = 1000L, seed = 20260925L)
plot(diag$residuals)
DHARMa::testDispersion(diag$residuals)
# An additional unconditional simulation can assess other hierarchical features:
# diag_all <- dharma_mermod(g, mode="unconditional", n=1000L, seed=20260925L)
```

In lme4 simulation, `re.form=NULL` conditions on all fitted group effects, whereas `re.form=NA` resimulates them. This differs from interpreting a prediction call as an integral. [SIM]

Conditional and unconditional simulations probe different levels and can have different sensitivity. Do not change mode repeatedly to obtain a preferred diagnostic p-value. Inspect residual patterns, calibration, zeros, and relevant temporal/spatial behavior; record simulation count and seed. [DHARMA]

A zero-inflation test is a discrepancy check against the fitted model, not an automatic command to add a mixture component. Temporal tests require a valid ordering and appropriate handling of repeated time values and independent series; concatenating subjects into a single autocorrelation series is not defensible.

## Separation and weak information

For binary outcomes inspect events/non-events across predictor combinations and groups. Very large coefficients/standard errors, near-perfect fitted classification, Hessian problems, or extreme likelihood surfaces may indicate separation or weak identification. More optimizer iterations do not create a finite unpenalized estimate in a separated problem. Reconsider the design/parameterization, or explicitly adopt a scientifically justified penalized/Bayesian approach and assess prior sensitivity. [TROUBLE]

## Know when lme4 is not the right engine

The ordinary lme4 residual model is not a general interface for arbitrary within-group residual correlations or heterogeneous residual-variance functions. Additional residual covariance, structured dispersion, zero inflation, hurdle components, beta or ordinal responses can require another engine. `nlme` and `glmmTMB` are examples for appropriate supported structures; ordinal/GAM/Bayesian models require their own method-specific guidance. Verify current family and covariance support rather than mechanically translating formulas. [FAQ; COV; TROUBLE]

Switching engines changes more than syntax when the likelihood, covariance, priors, or target predictions change. Record the reason and rerun the relevant diagnostic/inference checks. Do not describe a regularized fit as an unchanged lme4 result.

## Missingness and causal limits

Document which outcomes and predictors are missing, which observations were excluded, and why the chosen analysis is plausible. Likelihood-based use of incomplete repeated outcomes requires assumptions about missingness and model specification; it does not automatically solve missing predictors, informative dropout, or informative cluster size. Escalate those mechanisms explicitly instead of applying automatic complete-case deletion or universal imputation. A random intercept alone cannot remove arbitrary unmeasured confounding. These are scope limits: this skill is not a missing-data or causal-identification procedure.
