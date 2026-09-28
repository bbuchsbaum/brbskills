---
name: lme4-mixed-models
description: Plans, fits, diagnoses, and reviews lme4 LMMs and GLMMs in R, including random-effects design, inference, contrasts, and predictions. Applies to lmer/glmer workflows, not generic regression.
---

# Mixed models: evidence before automation

Use `lme4` as the reference engine. This is an evidence-informed protocol, not
universal consensus. Preserve the user's analysis scope; a focused model review
need not become a new analysis. Never select a model for significance or treat a
fitted object as evidence that the analysis is defensible.

## Read for the current decision

Resolve files relative to this skill directory. Read only relevant sections.
Installed package help governs executable syntax; the source register records
dated reviews, not a guarantee about current software.

| Need | Read |
|---|---|
| Plan or run a multi-stage analysis | Relevant stage of [full protocol](references/workflow.md) |
| Crossing/nesting, slopes, centering, covariance policy | [Design and random effects](references/design-random-effects.md) |
| Warnings, rank loss, singularity, optimizer, quadrature | [Numerical triage](references/convergence-singularity.md) |
| ML/REML, tests, selection, bootstrap, predictive validation | [Inference and selection](references/inference-selection.md) |
| Interactions, contrasts, marginal means, plots | [Contrasts and predictions](references/contrasts-predictions.md) |
| Residuals, dispersion, separation, GLMM limitations | [Diagnostics](references/diagnostics-glmm.md) |
| Disputed advice or source verification | [Evidence policy](references/evidence-policy.md) and [source registry](references/sources.md) |
| Final deliverable | [Reporting](references/reporting.md) |

## Preserve the analysis contract

Before fitting, record the question, estimand, outcome scale, analysis purpose,
sampling/randomization units, crossed or nested groups, within-group variation,
missingness, exact row identities, and target population. Use the
[analysis plan](templates/analysis-plan.yml). Missing design facts mean
`NEEDS_DESIGN`, not guessed confirmatory conclusions.

Declare the random-structure policy before examining focal p-values. Protect
scientifically essential slopes and distinguish within/between effects. If no
policy exists, propose design-supported simplification as this skill's pragmatic
choice, with maximal/near-maximal sensitivity where estimable. Preserve the
maximality disagreement; do not silently substitute a regularized/Bayesian engine.

## Fit and assess separate questions

Distinguish fixed-design rank, random-covariance singularity, numerical convergence,
and statistical adequacy. The [audit helper](scripts/model_audit.R) collects
warnings, `isSingular`, `rePCA`, and other evidence; it cannot certify validity.
Record unavailable derivatives separately from failed checks; their presence
does not prove convergence checks ran. Retain the covariance source for Wald inference.
Retain conditions, controls, versions, transformations, contrasts, and seeds.
Bound numerical rescue and compare estimates/predictions as well as objectives;
`maxeval` and `maxfun` are optimizer-specific. For GLMMs record approximation
settings such as Laplace `nAGQ=1` and verify higher-quadrature support.

Use compatible ML fits on identical observations for fixed-effect likelihood
comparisons. Name the inferential method: Satterthwaite and Kenward–Roger are
supported Gaussian approximations, not generic `glmer` corrections. Boundary
tests, bootstrap targets, failed fits, and selection require explicit treatment.
For prediction, split according to new versus observed groups/items and keep
selection inside training folds. Diagnose residual adequacy separately from
optimizer success; do not delete influential observations reflexively.

## Interpret and deliver

Define contrast direction, reference grid, weights, scale, and multiplicity.
Nonestimable contrasts stay nonestimable. In nonlinear models `re.form=NA` sets
random effects to zero; it does not generally integrate over their distribution.
Distinguish conditional, zero-random-effect, and integrated predictions, and mean
confidence intervals from prediction intervals.

Deliver runnable code, estimates/uncertainty, diagnostics, plots, model-change and
sensitivity records, and limitations. Use the [report template](templates/report.md).
Report `NEEDS_DESIGN`, `FIXED_RANK_DEFICIENT`, `NUMERICAL_UNRESOLVED`,
`SINGULAR_REVIEW`, `MISSPECIFIED`, or `READY_WITH_LIMITS` as warranted; several may
coexist. Only documented statistical review can assign `READY_WITH_LIMITS`.
Distinguish source review, executed tests, and scientific or agent validation.
