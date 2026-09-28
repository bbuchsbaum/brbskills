# Mixed-model skill: research synthesis and policy decisions

**Version 0.1.0-candidate · 2026-09-25**

## Executive conclusion

The appropriate product is not a long list of tips and not an automated stepwise fitter. It is a compact decision protocol that makes an agent establish the design and target, represent justified dependence, separate numerical diagnostics from statistical adequacy, choose an appropriate inferential or predictive procedure, and leave an inspectable record.

The consulted literature supports many common principles, but it does **not** provide a single community-approved recipe for random-effects complexity. The lme4 authors themselves describe competing approaches to singularity and random-effects selection. A trustworthy skill should preserve that disagreement and clearly label any default chosen by its author. [SING]

The bundle therefore provides a short executable workflow in `SKILL.md`, specific topic references, a source registry, small audit utilities, examples, templates, and adversarial evaluation specifications. Evidence collection and analysis validity are deliberately separate: a helper can expose a warning or a covariance boundary, but cannot pronounce the scientific analysis correct.

## Scope and source selection

The registry contains **44 selected entries**, including primary methods/simulation papers, official lme4 and companion-package documentation, an expert FAQ, original named-expert mailing-list replies, authored blog discussions, and the two official installation references. Sources span psycholinguistic/psychological crossed designs, ecological mixed-model practice, and statistical-software inference. This is a broad targeted canvass, not an exhaustive systematic review or a vote among the entire community.

Original authors and implementers were preferred for methodological and API claims. In particular, the collection draws on Bates and lme4 collaborators, Barr and collaborators, Matuschek and collaborators, Bolker's technical guidance, lmerTest/pbkrtest authors, Lenth's emmeans documentation, Hartig's DHARMa documentation, Schad and collaborators on contrasts, and other explicitly identified sources. Abstract-only or excerpt-only access is recorded rather than silently upgraded to full-paper review.

Blogs and forum posts are used for original explanation and practical interpretation, not as independent evidence that a test controls error rates. Morey's discussion supplies an authored perspective on p-value-centered practice; the corresponding simulation claim belongs to Luke's paper. Bolker's archived replies clarify software differences and debugging context. Gelman's centering discussion and its attributed comments provide additional routes to the underlying issue. [BLOG-P; LUKE; FORUM-DF; FORUM-NUM; BLOG-C]

## 1. Begin with the estimand and sampling design

A model formula is not a sufficient description of an analysis. The protocol first records the target population and quantity, row unit, sampling/randomization units, grouping structure, within-group variation, observation distribution, and missingness policy. This prevents an agent from mistaking a convenient long-format table for evidence about the design.

Crossed subject/item sampling is a particularly important case: a claim intended to generalize across subjects and items must address both sources of variability. Relevant random slopes depend on how conditions vary within grouping factors and on the hypothesis, including interactions. A maximality slogan is not permission to include uninterpretable or unsupported slopes. [MAX; INT]

Centering and contrasts are also substantive decisions. A within-person association is not automatically the same target as a between-person association. The skill includes a within/between decomposition and an explicit warning that longitudinal dynamics, group-mean measurement error, and causal identification may require additional methods. [CENTER; CONTR]

## 2. Preserve the maximality disagreement

The design-maximal position emphasizes protection against unmodeled subject/item variation in confirmatory tests. The parsimonious position emphasizes covariance dimensions that the data actually support. The power/error tradeoff depends on the design, true covariance, sample information, and fitting procedure. These are substantive methodological differences, not merely different optimizer preferences. [MAX; PARS; POWER]

The skill supports three declared policies: design-maximal with a fallback; design-supported simplification with protected essential slopes and sensitivity; or an explicitly different regularized estimator. When an analyst has supplied no policy, the skill proposes the second as a pragmatic default, not as universal consensus.

Two design decisions follow. First, focal p-values never choose the random structure. Second, an agent must disclose when a plausible alternative changes the conclusion. A selection threshold from one Gaussian simulation study is not imported as a universal criterion for GLMMs or all experiments. [POWER]

## 3. Separate rank, singularity, convergence, and adequacy

The core diagnostic distinction has four parts. Fixed-design rank deficiency concerns estimability of fixed coefficients. Singularity concerns the rank of estimated random covariance. Convergence warnings concern numerical reliability. Residual/calibration/dependence failures concern the statistical model. More than one may occur together.

A singular covariance can be a legitimate boundary optimum and need not produce a zero displayed variance or an extreme pairwise correlation in a larger block. Conversely, a warning-free fit does not establish the adequacy of its distribution, dependence assumptions, or scientific target. The skill routes these cases to different responses rather than one optimizer loop. [SING; CONV]

The audit records original warnings, optimizer codes, fixed columns lost, `isSingular`, `rePCA`, group sizes, approximation settings, and relevant parameters. It does not generate a “valid model” badge. Numerical rescue is bounded and judged by substantive estimate/prediction stability as well as objective values; a fixed budget is an engineering policy, not a statistical theorem.

## 4. Make inference method-specific

Gaussian mixed-model tests do not have one universal exact denominator df. Satterthwaite and Kenward–Roger are useful named approximations in supported settings; KR is more than simply substituting a df because covariance adjustment also matters. A GLMM's default Wald z approximation is a different procedure. The skill prohibits portraying Gaussian corrections as a generic exact solution for glmer. [PV; SAT; KR]

For fixed-effect likelihood comparisons, the agent must use compatible ML fits on identical observations—not merely equal row counts. For variance-component hypotheses, boundary calibration matters. The specialized scope of restricted likelihood-ratio methods is preserved instead of replacing every null by a one-df chi-square or halving p-values. [PB; RLR]

Bootstrap operation is also split into targets: null-generated testing, fitted-model intervals, and prediction uncertainty. The protocol records simulation count, seed, failures, and Monte Carlo precision. Repeating only the final fit does not by itself account for a preceding model search. These requirements are intended to prevent plausible-looking but incorrectly calibrated output. [BOOT; PB]

## 5. Reject a universal “best model” button

The skill distinguishes confirmatory inference, exploratory explanation, and prediction. It preserves scientific adjustment choices and a declared covariance policy in confirmatory work. It permits motivated candidate comparisons with disclosure in exploratory work. For prediction, it defines the deployment population and a corresponding held-out design before scoring models.

A random row split among repeated observations from the same people does not automatically estimate new-person performance. Crossed designs additionally distinguish new subjects, new items, or both. The relevant principles come from structured validation; the exact split is an application-specific policy. Model selection and preprocessing belong inside training folds. [CV]

Information criteria are not banned, but they must answer a stated comparison question among compatible likelihoods. The skill does not treat a small AIC, a large pseudo-R-squared, or the smallest p-value as proof of scientific truth. The ecological perspective in the collection helps avoid treating confirmatory experimental conventions as the only use of mixed models. [ECO]

## 6. Make contrasts and nonlinear predictions explicit

Contrast weights, direction, reference-grid values, averaging weights, and multiplicity define the scientific question. In an interaction, simple effects or trends can be more interpretable than an unqualified average. Nonestimable contrasts remain nonestimable; a generated grid does not supply missing information. [EINT; EBASIC; EMESSY]

The most consequential prediction guardrail is the distinction between a conditional prediction for a known group, a prediction at random effects zero, and a prediction integrated over new-group heterogeneity. They are not generally the same under a nonlinear link. Similarly, exponentiating a logit contrast gives an odds ratio, not a risk difference. The skill records the order of averaging and transformation. [PRED; ETRANS]

The plotting policy follows those distinctions: show observed data and model-derived estimands, label scales and target populations, and distinguish mean confidence intervals from prediction intervals. Multiplicity families must be defined scientifically rather than inherited accidentally from software grouping defaults. [ECOMP]

## 7. Treat current software behavior as a moving implementation layer

Two examples justify checking implementation contracts. Traditional lme4 double-bar syntax is limited to numeric predictor design matrices; it should not be assumed to create independent categorical contrast slopes. DHARMa's consulted documentation describes a default change at version 0.5.0, so residual-simulation conditioning should be explicit and recorded. [LMM; DHARMA]

The bundle supplies a formals-based DHARMa compatibility branch but does not claim that branch has been runtime-tested in this environment. Likewise, it distinguishes negative-binomial dispersion theta from lme4's covariance theta and limits higher glmer quadrature to supported structures. [NB; GLMM]

## Validation and remaining release gates

Fourteen static/algebra check groups passed: registry/schema checks, source and file routing, YAML contracts, R delimiter checks, and independent numerical demonstrations of several mathematical distinctions. These checks are useful but narrow. A balanced-delimiter scan is not an R syntax parser or an execution test.

R and the example analyses were not executed here. Twenty-four adversarial agent cases are specified, not scored. No independent statistical review, full-policy error-rate/coverage study, or Codex-versus-Claude comparison has been performed. The bundle is therefore a **source-grounded release candidate**. A validated release should report those results separately rather than using polished writing as a substitute for evidence.
