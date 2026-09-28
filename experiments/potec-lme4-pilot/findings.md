The clearest pattern in this specification is a modest own-discipline reading-time
advantage among graduate readers. At the reference lexical profile, the equally
discipline-weighted own-minus-other contrast is **−0.0299 log milliseconds**
(unadjusted 95% interval −0.0424 to −0.0174; twelve-test Holm-adjusted
*p* = 0.00034). Exponentiating this log-scale contrast gives a geometric-mean
ratio of about **0.971**, or **2.95% lower** first-pass reading time given fixation.
This ratio is not an unqualified population arithmetic-mean effect.

For undergraduates, the corresponding estimate is −0.00785 log milliseconds
(95% interval −0.0234 to 0.00773). The graduate-minus-undergraduate difference
in domain-match contrasts is −0.0220 (95% interval −0.0427 to −0.00139), but its
Holm-adjusted *p* is **0.379**. The result therefore does not establish that the
domain-match advantage differs by study level under the declared comparison family.
One individually small p-value and one individually large p-value would not
establish that difference either.

The graduate own-minus-other difference in surprisal slope is −0.0149 log
milliseconds per surprisal SD (95% interval −0.0256 to −0.00423), with adjusted
*p* = **0.073**. The graduate-versus-undergraduate difference in this slope contrast
has adjusted *p* = 1. These results do not establish study-level moderation of
the expertise–surprisal association. They are also not equivalence tests.

None of the sampled-word FPReg model's six exploratory Wald contrasts has a small
adjusted p-value. However, the joint derivative check timed out; these approximate
inferences are **numerically unqualified**, so this is not a validated negative
finding. Its outcome is regression per eligible
word opportunity, not regression conditional on fixation. The response curves
illustrate a substantial distinction between zero-random-effect and integrated
probabilities, but their point differences should not be interpreted without
the uncertainty and sampling limits.

**Adequacy limits matter here.** The log-FPRT residual Q–Q plot has heavier tails
than a Gaussian distribution, and standardized residual SD varies from about
0.89 to 1.17 across fitted-value deciles. Adjacent-word residual correlation is
small (0.0145 over 63,931 eligible pairs), but that alone does not validate
the residual model. The GLMM's conditional simulation checks place its observed
adjacent residual correlation and reader–text rate spread inside the simulated
95% ranges; these limited in-sample checks do not establish overall adequacy.

All fitted covariance specifications were singular. The same-row correlated
reader/item LMM sensitivity, evaluated on the quarter-word sample, changed the
six focal point estimates by less than 0.19 baseline standard errors, but its
Hessian is indefinite. That is limited evidence of point-estimate stability,
not a clean robustness pass. It does not replace a full-data covariance sensitivity.
The stricter full-data LMM changed the focal contrasts by less than 0.00001
standard errors. Additional numerical audit results are shown below.

The explicit GLMM derivative calculation reached its 900-second limit without
returning a Hessian. The warm-start alternative LMM optimizer reached its
600-second limit without returning a fit. These are recorded incomplete checks,
not successes. The GLMM's reported exploratory standard errors use lme4's
RX/PIRLS approximation, not the unavailable joint Hessian. The full LMM's strict
refit supports point-estimate stability but retains some scaled-gradient concerns.

The appropriate conclusion is an **exploratory own-domain reading-time association
among graduate readers, with unresolved covariance/adequacy qualifications**.
This is not a causal effect of training, a validated population prediction, or a
confirmatory result about how expertise changes surprisal processing. The LMM
remains under `SINGULAR_REVIEW` with Gaussian adequacy concerns; full numerical
qualification remains `NUMERICAL_UNRESOLVED` for the LMM, GLMM and covariance
sensitivity. This run is not assigned `READY_WITH_LIMITS`.

This bounded trial did not complete a full-corpus GLMM, a GLMM covariance
sensitivity, a fixation-conditioned FPReg sensitivity, leave-text-out influence
fits, or refit-based intervals propagating variance-component uncertainty.
Those omissions limit the scientific claims made here.
