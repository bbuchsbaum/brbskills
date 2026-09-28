# Full analysis protocol

Read the section relevant to the current analysis decision. This preserves the
original v0.1.0-candidate protocol; source IDs resolve in [sources.md](sources.md).

## Contents

- [1. Establish the analysis contract before fitting](#1-establish-the-analysis-contract-before-fitting)
- [2. Build the model from design and estimand](#2-build-the-model-from-design-and-estimand)
- [3. Fit reproducibly, then separate four questions](#3-fit-reproducibly-then-separate-four-questions)
- [4. Diagnose the fitted stochastic model](#4-diagnose-the-fitted-stochastic-model)
- [5. Match inference and selection to purpose](#5-match-inference-and-selection-to-purpose)
- [6. Construct contrasts and plots deliberately](#6-construct-contrasts-and-plots-deliberately)
- [7. Finish with an auditable result or a specific limitation](#7-finish-with-an-auditable-result-or-a-specific-limitation)

## 1. Establish the analysis contract before fitting

Write the scientific question, estimand, outcome scale, confirmatory/exploratory/predictive purpose, independent sampling or randomization units, grouping factors, repeated measures, candidate predictors, missingness policy, and intended generalization. Use [analysis-plan.yml](../templates/analysis-plan.yml). Distinguish inference about named levels from generalization to a population of levels. A random intercept does not establish causal identification.

Inspect rows and identifiers, duplicates, observations per group, event counts/denominators, within-group variation, empty cells, missingness, and temporal/spatial dependence. Group counts matter independently of row counts. Record an immutable row ID and the exact analysis subset; prefer explicit preprocessing and `na.action = na.fail`. Do not silently aggregate, impute, delete outliers, or change the target. If design facts are unavailable, mark `NEEDS_DESIGN`, state assumptions, and withhold unsupported confirmatory conclusions. [LMM; FAQ; REPORT]

Check source variable definitions and consequential merge/recode steps: row counts
may describe a different unit, and zero can mean a measured value, a structural
non-event, or a missing-value placeholder. Resolve these meanings before choosing
transformations, denominators, or an analysis population.

## 2. Build the model from design and estimand

Use `lmer` for Gaussian conditional errors; `glmer` for a justified family/link, with correct binomial trials or count exposure. The raw outcome need not be normally distributed for an LMM. Do not choose a family solely to make a residual test nonsignificant.

Represent crossed sampling units separately; represent actual nesting explicitly. Include design-supported random slopes for within-group effects relevant to the tested claim. A predictor constant within a group supplies no within-group slope information; do not invent that interpretation. Consider interaction slopes rather than reflexively using random intercepts only. [MAX; INT]

Specify meaningful centering, factor levels, contrasts, and within/between decompositions before fitting. Centering can change the estimand; zero-correlation covariance constraints can change under recoding. Numeric `||` is not a reliable shortcut for independent categorical contrast slopes: inspect its expansion or build explicit numeric contrast columns. [CENTER; CONTR; LMM]

Select and record a **random-structure policy** before examining focal p-values:
- **Design-maximal:** all justified, estimable slopes and covariances, with a declared fallback.
- **Design-supported simplification:** a defensible starting structure and a bounded, documented simplification policy; protect scientifically essential slopes and compare sensitivity.
- **Regularized alternative:** a deliberate different estimator/engine with explicit priors and checks, never a silent lme4 repair.

There is no universal winner. Without an existing policy, propose design-supported simplification as this skill's pragmatic default, label it a policy choice, and retain a maximal/near-maximal sensitivity fit where estimable. Do not copy a simulation paper's selection cutoff as a universal rule. [SING; MAX; PARS; POWER]

## 3. Fit reproducibly, then separate four questions

Supply `data=`, explicit formula/family, and stored controls. Keep `sessionInfo()`, package versions, contrasts, transformations, warnings, and seed. Fit Gaussian final estimation models with REML unless the inferential method calls for ML. Use ML for fixed-effect likelihood comparisons on identical observations. For GLMMs record likelihood approximation: normally Laplace (`nAGQ=1`); higher quadrature has structural limitations. [LMM; GLMM; PB]

Ask separately: (a) is the fixed design estimable, (b) is random covariance singular, (c) is numerical optimization trustworthy, (d) is the statistical model adequate? Use [model_audit.R](../scripts/model_audit.R) to collect evidence, not to certify validity.

Inspect which checks actually ran and budget expensive post-fit diagnostics as
described in [numerical triage](convergence-singularity.md). Save completed stages
before long checks; unavailable derivatives are different from failed checks.

For convergence problems, examine specification and scale first; then use appropriate stricter controls, a restart or alternative optimizer, and `allFit` when needed. Compare objective values **and focal estimates/predictions**, retaining disagreements. `maxeval` and `maxfun` belong to different optimizers. Limit numerical rescue to a declared budget; do not cycle indefinitely. [CONV]

For singularity, inspect `isSingular`, `VarCorr`, and `rePCA`. A boundary fit can be a legitimate optimum. It is not synonymous with nonconvergence or harmlessness. Review structural support, implement the declared policy, and evaluate inference sensitivity. Do not suppress warnings or remove terms solely to obtain smaller p-values. [SING; PARS]

## 4. Diagnose the fitted stochastic model

For LMMs inspect conditional residuals, functional form, unequal spread, group influence, and residual dependence. For GLMMs examine simulation residuals, calibration, dispersion, sparsity/separation, and unexpected zeros. Record simulation conditioning explicitly; DHARMa APIs/defaults vary by version. Diagnostic p-values are evidence, not automatic model-selection commands. [DHARMA; TROUBLE]

Investigate influential observations without reflex deletion. If residual correlation, zero inflation, an unsupported family, or weak identification requires another engine, explain the limitation and obtain a scientifically defensible model specification. Optimizer success cannot repair misspecification. [FAQ; COV]

## 5. Match inference and selection to purpose

Report the estimate, uncertainty, estimand, and assumptions before emphasizing p-values. For supported Gaussian LMM tests/contrasts, use a named Satterthwaite or Kenward–Roger approximation, or a justified parametric bootstrap. These are not exact universal solutions; KR/Satterthwaite are not generic `glmer` methods. GLMM Wald z tests are asymptotic. Sparse groups/events and boundary fits warrant additional care. [PV; SAT; KR; LUKE]

For likelihood comparisons require the same outcome, rows, weights, offsets, family, comparable likelihood approximation, and genuinely nested models when using an LRT. Zero-variance nulls are boundary tests: do not automatically use ordinary chi-square degrees of freedom or halve a p-value. Bootstrap tests simulate under the null; bootstrap intervals usually simulate under the fitted model. Record failed fits and Monte Carlo precision. [PB; BOOT]

Do not run blind stepwise significance searches. For explanation use scientific candidate models and disclose selection-conditioned inference. For prediction define whether groups/items are new or previously observed, then split data accordingly; perform tuning and selection inside training folds. Information criteria answer specific predictive questions, not scientific truth. [ECO; CV]

## 6. Construct contrasts and plots deliberately

Name the contrast, direction, reference grid, covariate values, averaging weights, response/link scale, and multiplicity family. Use `emmeans` for explicit comparisons and `emtrends` for slopes. With interactions, avoid unqualified averaged main-effect conclusions. Do not report nonestimable contrasts as estimates. [CONTR; EINT; EBASIC; EMESSY]

In nonlinear models, distinguish existing-group conditional predictions, predictions at random effects zero, and predictions integrated over the random-effects distribution. `re.form=NA` gives the second, not generally the third. Inverse-link transformation and averaging do not commute. Label confidence intervals versus prediction intervals; use plots of observed data and model-derived contrasts, not significance stars alone. [PRED; ETRANS; ECOMP]

## 7. Finish with an auditable result or a specific limitation

Deliver the analysis contract, runnable code, model/contrast tables, plots, diagnostic evidence, model-change log, sensitivity results, and source-backed rationale. Report all material warnings, singularity, missingness, exclusions, sample/group counts, inference approximation, and multiplicity adjustment.

Use statuses `NEEDS_DESIGN`, `FIXED_RANK_DEFICIENT`, `NUMERICAL_UNRESOLVED`, `SINGULAR_REVIEW`, `MISSPECIFIED`, or `READY_WITH_LIMITS`. Several may coexist. Only a documented statistical review—not the helper script—can assign `READY_WITH_LIMITS`. State what remains uncertain and which conclusions survive reasonable alternatives. Never fabricate output, a convergence fix, expert agreement, or a completed validation. [REPORT]
