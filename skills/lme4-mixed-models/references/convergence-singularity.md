# Fitting, convergence, and covariance singularity

## Four diagnoses, four responses

| Evidence | Interpretation | Response |
|---|---|---|
| Dropped columns of fixed-effect X | Some requested fixed coefficients are not separately estimable | Audit coding, empty cells, confounding; redefine an estimable claim. |
| `isSingular(fit)` | Estimated random covariance is rank deficient at the chosen tolerance | Inspect `VarCorr`/`rePCA`; apply declared covariance policy and sensitivity. |
| Optimizer/gradient/Hessian message | Numerical reliability needs investigation | Check specification/scale; compare stricter or alternative fits. |
| Residual, calibration, dependence failures | The fitted stochastic model may be inadequate | Revisit distribution, mean structure, correlation, or data generation. |

A model can occupy several rows at once. Fixed rank deficiency and singular covariance are different mathematical objects. [LMM; SING; CONV; TROUBLE]

## Initial fitting

Start with readable formulas and default controls unless there is a documented reason otherwise. Use explicit data and complete-case handling; do not let a comparison silently change its observations. Store the fit call, lme4 version, original warning/message stream, objective, fixed coefficients, covariance, and inference target. The included audit inspects these objects without constructing a dense random-effects design matrix.

For Gaussian estimation, REML is a useful default. For changes to fixed-effect space in a likelihood comparison, refit all candidates with ML. Refit a selected Gaussian estimation model using REML when that matches the declared inference. GLMM fitting integrates over random effects using an approximation: `glmer(..., nAGQ=1)` is Laplace; `nAGQ=0` trades accuracy for speed. Higher adaptive quadrature is supported only for a single scalar random-effect term in the documented lme4 implementation. Do not request it for an arbitrary crossed/random-slope GLMM. [LMM; GLMM]

## Check availability before interpreting silence

Requested controls are not execution evidence. Depending on installed lme4 version,
singularity, model size, and controls, derivative calculations or convergence
checks may be skipped even when optimization succeeds. Inspect the returned
gradient/Hessian and the installed implementation when needed; do not equate
`calc.derivs=TRUE` with completed checks. The helper records derivative availability,
finiteness, dimensions, and Hessian curvature, but leaves check execution unknown
when the saved object cannot establish it. Record actual controls separately;
do not evaluate a saved call's local symbols to guess their values. [CONV; LME4-NEWS]

`DERIVATIVES_UNAVAILABLE` means missing evidence, not demonstrated nonconvergence.
`HESSIAN_REVIEW` records non-positive-definite curvature. At an interior optimum
this is numerical concern; at a covariance boundary use feasible directions and
constrained-optimum reasoning rather than demanding an unconstrained positive-definite
Hessian or zero gradient in every coordinate. Finite differences themselves can
be unreliable. Neither a computed Hessian nor optimizer code zero certifies
scientific validity. Keep singularity, numerical stability, and adequacy separate.
[CONV; SING]

## Bounded numerical rescue

The following is a **skill policy**, not a claim that exactly three attempts is optimal. Budget one specification/scale review, one stricter-control attempt, and one independent optimizer comparison before explicit escalation. A necessary `allFit` comparison can replace the last step. Do not fit every optimizer for every already well-behaved model.

```r
# For an lmer model using nloptwrap:
strict_lmm <- update(m, control = lme4::lmerControl(
  optimizer = "nloptwrap",
  optCtrl = list(xtol_abs = 1e-8, ftol_abs = 1e-8, maxeval = 100000)))

# For a glmer model using bobyqa (a candidate, not a universal improvement):
strict_glmm <- update(g, control = lme4::glmerControl(
  optimizer = "bobyqa", optCtrl = list(maxfun = 200000)))

# Diagnose genuine disagreement, rather than choose the fit with fewer warnings:
# candidates <- lme4::allFit(m)
```

Controls belong to particular optimizers. Inspect comparable objective values, fixed coefficients, scientifically meaningful contrasts, and predictions; covariance coordinates can be unstable near a flat boundary even when a focal contrast is stable. Declare tolerances in the scale of the target, not by an arbitrary warning count. With persistent Hessian concerns, the official guide discusses more accurate derivative evaluation. Large-data gradient warnings require care. [CONV]

Budget post-fit work as well as fitting. A full finite-difference Hessian scales
quadratically in the number of top-level parameters (for Laplace GLMMs, covariance
parameters plus fixed effects), not simply the number of rows. When expensive,
time representative objective evaluations, estimate cost, and choose the next
check for its relevance to the focal uncertainty. An optimizer comparison,
profile, or bootstrap is also work to budget, not an automatic fallback. Save fits
before these checks and checkpoint completed stages. No universal timeout,
subsampling fraction, or requirement to compute a joint Hessian is imposed. [PERF]

If reconstructing an objective, preserve data, offsets, weights, family, coding,
parameter order, and approximation settings; record agreement at the saved fit
before differentiating. Treat internal APIs as version-sensitive. A timeout
establishes incompletion, not which unlogged stage finished or that the model
failed. Retain the last completed stage and any partial evidence; do not silently
modify the original fit or remove slopes merely to make diagnostics affordable.

Rescaling does not resolve duplicated outcomes, misconstructed identifiers, separation, rank loss, or lack of within-group variation. An expert debugging exchange [FORUM-NUM] reinforces checking the data/model before treating an internal matrix error as an optimizer-choice problem. Preserve the original and all revised specifications.

## Singular-fit review

The documented default tolerance for `isSingular` is `1e-4`; record the actual value. It is a numerical threshold, not a p-value or a scientific effect-size threshold. A higher-dimensional covariance can be singular without any displayed variance exactly zero or any pairwise correlation exactly ±1. `rePCA` describes orthogonal covariance directions. [SING]

Review the information available for each coefficient and its covariance partners. A true variance may be near zero, the sample may provide little information, or the requested structure may exceed what this design can estimate. Inspect alternate tolerances diagnostically but never tune the tolerance to produce a desired label. Zero variance does not prove the population variance is zero.

Under a prespecified design-maximal policy, retain a defensible boundary fit only with clear limitations and sensitivity. Under simplification, document each covariance/slopes change and protect the tested design effect. Under regularization, identify the changed likelihood/prior/engine. A proper prior may produce a proper estimate; it does not manufacture missing experimental information. [PARS; MAX; SING]

## No-go shortcuts

Do not zero out convergence checks, delete grouping factors as a blanket fix, use the first optimizer that returns no warning, treat all singular bootstrap replicates as failures, or report a coefficient whose column was silently dropped. Distinguish acceptable expected boundary fits under a null from true refitting failures. [BOOT; PB]

When objectives or focal conclusions remain materially optimizer-dependent, output `NUMERICAL_UNRESOLVED` with the compared fits, not a definitive inferential table.
