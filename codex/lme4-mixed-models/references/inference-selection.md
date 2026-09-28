# Inference, model comparison, and selection

## Define what is being tested

A coefficient test, a multi-parameter term test, a simple contrast within an interaction, a variance-component test, and a prediction comparison are not the same question. Write the null as a restriction on model parameters or an explicit contrast. Report the effect and uncertainty in a scientifically interpretable unit.

| Task | Defensible route | Important limitation |
|---|---|---|
| Gaussian LMM fixed coefficient/contrast | `lmerTest` Satterthwaite; `emmeans` with a named df method | Approximate and conditional on model adequacy/selection. |
| Gaussian LMM multi-df fixed-effect test | Supported Kenward–Roger or Satterthwaite F test | KR has supported covariance/model restrictions and adjusts covariance as well as df. |
| Nested fixed-effect likelihood comparison | ML fits, same response/rows; LRT or null parametric bootstrap | Ordinary chi-square calibration is asymptotic. |
| GLMM fixed coefficient/contrast | Named Wald-z approximation; profile or appropriate bootstrap sensitivity | Sparse events, separation, few groups, or boundaries may undermine asymptotics. |
| Null random-effect variance | Test calibrated for that boundary/configuration; supported restricted-LRT method or null bootstrap | Not an automatic ordinary chi-square test or universal 50:50 mixture. |
| Prediction | Held-out target-specific scoring, uncertainty/calibration | A split must reflect whether groups/items are new. |

Sources: [PV; SAT; SAT-API; KR; KR-PAPER; PB; CV].

Luke's comparison supports KR/Satterthwaite over t-as-z under its studied Gaussian designs; it does not prove exact error control for every model. Do not use `abs(t)>2` as a universal significance rule or divide the row count into an improvised denominator df. [LUKE; FORUM-DF]

## Covariance source and multiplicity are separate decisions

For Wald inference, retain the covariance matrix actually used, its source, and
any conditions or fallback. For lme4 GLMMs, a finite-difference Hessian and the
RX-based approximation are distinct routes. Missing derivatives do not make RX
intrinsically invalid; RX may be less accurate when fixed and covariance parameter
estimates are strongly associated, while a numerically unstable Hessian can also
give poor results. Assess numerical and inferential sensitivity rather than
assigning validity from the method name. [VCOV]

`capture_vcov(fit)` in the helper retains the matrix, requested/default method,
source, and conditions without refitting. If a condition occurs it conservatively
leaves the source unresolved: inspect the retained message and installed method
before labelling a fallback. Use the captured matrix in the downstream contrast
calculation (e.g. `emmeans(..., vcov. = v$covariance)`) so the provenance describes
the actual computation. For KR or another method that adjusts covariance, record
that method's final covariance instead; the helper does not audit companion-package
adjustments. A finite matrix does not establish reliable coverage.

Define the comparison family from the scientific questions before inspecting
p-values. Holm adjustment controls family-wise error when its component p-values
are valid; it cannot repair numerical problems or misspecified tests. Unadjusted
95% intervals can accompany adjusted p-values if labelled, but are not simultaneous
intervals and need not agree with adjusted rejection decisions. If simultaneous
coverage is needed, choose and report a supported interval procedure separately.
[PADJUST]

## ML and REML without slogans

Fixed-effect spaces being compared by likelihood must use ML, not incomparable REML criteria. `anova` may automatically refit lmer objects with ML; make this visible rather than relying on unnoticed behavior. Same fixed-effect space is a prerequisite for comparable REML criteria, not a guarantee that an ordinary variance-component LRT has the right null distribution. Valid REML-based KR or restricted-LRT procedures are not prohibited by this rule. [LMM; KR]

```r
# Same analysis data, fixed coding, same random structure:
m_full_ml <- update(m_full, REML = FALSE)
m_null_ml <- update(m_full_ml, . ~ . - focal_term)
# Call assert_comparable(..., row_ids_a=..., row_ids_b=...) from scripts/model_audit.R.
# Confirm fixed-space nesting separately; the helper cannot prove it.
anova(m_null_ml, m_full_ml, refit = FALSE)

# Gaussian REML inference using an explicit wrapper, not search-path masking:
mt <- lmerTest::as_lmerModLmerTest(m_full)
summary(mt, ddf = "Satterthwaite")
# For a supported multi-df question, construct and document the tested restriction.
```

Comparability requires identical analyzed observations and responses, weights/offsets with the same meaning, compatible families/links, and comparable approximation settings. AIC values from different response transformations or differing GLMM likelihood approximations are not automatically comparable. For nested LRTs, a worse full-model likelihood is numerical evidence to investigate, not a negative test statistic to blindly accept. [PB; GLMM]

## Confidence intervals and special boundary tests

`confint.merMod` offers profile, Wald, and bootstrap routes. Its Wald intervals apply to fixed effects, not covariance parameters; covariance intervals use SD/correlation parameterization. Profile failures/nonmonotonicity require investigation. Do not request unsupported BCa or studentized options from its bootstrap interface. [CI]

`RLRsim::exactRLRT` is a specialized finite-sample route with assumptions about the tested correlation structure, iid errors, and supported nuisance components. Read its exact contract before calling it; its name does not make it an exact test for arbitrary crossed covariance hypotheses. [RLR]

## Bootstrap correctly

For a **null hypothesis test**, simulate from the fitted null, refit both null and alternative on each simulated response, and compare the observed statistic to its reference distribution. `pbkrtest::PBmodcomp` supports relevant lmer/glmer comparisons and handles ML refitting, but inspect the returned sample counts and reference distribution. Its documentation discusses negative simulated likelihood ratios and their numerical implications. [PB]

For a **confidence interval**, `bootMer` can simulate under the fitted model and refit it. With `use.u=FALSE`, new random effects are generated; conditioning choices answer different questions. Capture `bootFail`, `boot.fail.msgs`, and `boot.all.msgs`, plus nonfinite statistic counts. An interval bootstrap is not a null-calibrated p-value merely because its interval excludes zero. [BOOT]

Declare simulation count B and seed. For an ordinary fixed-B exceedance estimate, approximate Monte Carlo standard error is `sqrt(p*(1-p)/B)` (binomial variance). For example, p≈0.05 with B=1000 gives about 0.0069; B=10000 gives about 0.0022. This is simulation noise, not the sampling uncertainty of the scientific estimate. Near zero exceedances, report resolution or a binomial interval; do not report p=0 or use the zero plug-in standard error as proof of precision. Adaptive stopping needs an appropriate sequential procedure, not arbitrary stopping when significance appears.

Define refit success in advance. Expected singular fits under a boundary null need not be failures. Nonconvergence, nonfinite statistics, materially negative LRs, or changed row sets require investigation. Do not silently discard failures and pretend the surviving distribution is unbiased. If selection is part of the advertised procedure, calibrating that whole procedure may require repeating selection inside simulation; a final-model bootstrap alone does not generally account for selection.

## Finding an appropriate model

For confirmatory analysis, preserve the scientific hypothesis, necessary adjustment variables, and declared random-structure policy. Use a small, motivated candidate set and preserve hierarchy unless a deliberate, interpretable parameterization justifies otherwise. Report the selection process. Post-selection standard errors/p-values are conditional on the chosen model, not automatically calibrated for the preceding search.

For explanatory comparison, information criteria can weigh fit against complexity among scientifically meaningful candidates. Avoid all-subsets dredging and treating Akaike weights as probabilities that a scientific explanation is true. Marginal versus conditional information criteria target different forms of generalization; name the criterion. Do not insert the row count into a mixed-model AICc formula without justifying its correction and effective sample size. [ECO]

For prediction, first specify the deployment target. Holding out rows from an already observed subject evaluates a different problem from holding out subjects. For crossed designs, state whether held-out predictions involve new subjects, new items, or both; design a corresponding split rather than allowing both grouping identities to leak. Time-forward prediction needs time-respecting splits. Preprocessing, centering estimates, feature selection, and covariance tuning must be learned inside training folds. These are operational applications of structured-validation principles, not a claim that one split is universally best. [CV]

The skill deliberately provides **no automatic best-model search function**. Its job is to make the inferential target, candidate space, comparison criterion, and sensitivity explicit.
