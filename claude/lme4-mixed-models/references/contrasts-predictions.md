# Contrasts, predictions, and plots

## A contrast is an estimand, not a menu option

Specify the population, factor levels and order, direction, covariate values, averaging weights, scale, and multiplicity family. Planned contrasts can express the scientific hypothesis more precisely than a generic omnibus test followed by all pairwise comparisons. Coding determines coefficient meaning, while an explicitly constructed estimable contrast can express the intended comparison directly. [CONTR]

With an interaction, `emmeans(m, ~ condition | moderator)` and `emtrends(m, ~ condition, var="x")` answer different questions from averaging over the moderator. A main effect is not forbidden, but its averaging population must be meaningful. Do not interpret a Type-III table or default coding without writing its hypotheses. Type-II/III labels alone are not sufficient specifications. [EINT]

```r
# Illustrative: ensure factor order is c("control", "treatment").
e <- emmeans::emmeans(m, ~ condition | context,
                       at = list(x_c = 0), weights = "equal",
                       lmer.df = "kenward-roger")
diff <- emmeans::contrast(e,
  method = list("treatment - control" = c(-1, 1)), adjust = "none")
# Combine contexts into ONE planned family if that is the scientific family:
summary(diff, by = NULL, infer = c(TRUE, TRUE), adjust = "holm")
# Holm governs adjusted p-values; inspect output for the actual CI adjustment.
```

Use this LMM example only for a supported Gaussian model. `emmeans` can fall back to other df methods when dependencies or size limits apply: inspect the printed method and output instead of claiming KR merely because it was requested. [ESOPH]

Equal weighting of factor combinations and weighting by observed frequencies are different target populations in unbalanced data. Inspect the reference grid and explicitly choose `weights="equal"`, `"proportional"`, or another justified scheme. Empty/confounded cells can yield nonestimability; averaging does not create information. [EBASIC; EMESSY]

## Link scale versus response scale

For a logit GLMM, a linear contrast of logits is a log odds ratio; exponentiating produces an odds ratio. A difference of response probabilities is a risk difference. These are not interchangeable.

```r
# g is a binomial/logit glmer model; two levels in the declared order.
elink <- emmeans::emmeans(g, ~ condition, at = list(x_c = 0),
                          weights = "equal")
logor <- emmeans::contrast(elink, list("treatment / control" = c(-1, 1)))
summary(logor, infer = c(TRUE, TRUE), type = "response") # odds ratio

# Transform the grid BEFORE contrasting for a probability difference:
eresponse <- emmeans::regrid(elink, transform = "response")
rd <- emmeans::contrast(eresponse,
                       list("treatment - control" = c(-1, 1)))
summary(rd, infer = c(TRUE, TRUE))
```

Merely asking for `type="response"` after a link-scale contrast does not change the contrast into a risk difference. Back-transforming an average linear predictor also differs from averaging response-scale predictions. Choose whether transformation happens before or after averaging; regridding an already averaged object cannot undo an earlier averaging choice. [ETRANS]

## Three prediction targets

**Existing-group conditional:** use the fitted random-effect modes for specified observed groups, normally `re.form=NULL`. This estimates a conditional mean and involves shrinkage; treating estimated group effects as observed error-free attributes is inappropriate.

**At random effects zero:** `predict(g, newdata, re.form=NA, type="response")` sets group contributions to zero. Labels such as “population-level” in software can refer to this convention; explicitly say what was computed. [PRED]

**Integrated over new-group heterogeneity:** for a GLMM, calculate

`mu(x,z) = integral inverse_link(x beta + z b) p(b; G) db`.

This is generally not `inverse_link(x beta)`. For a Gaussian identity-link model the two means coincide because E[b]=0, but uncertainty for a new observation/group is still different. A prediction interval includes relevant new random-effect and observation variation; a confidence interval for a mean does not.

A useful derived special case is a Poisson/log-link model with Gaussian linear random contribution variance v: `E[Y|x] = exp(eta + v/2)`, not `exp(eta)`. For a logit-normal mean there is no corresponding general elementary formula. The helper `logit_normal_mean(eta, random_variance)` uses numerical integration for a supplied variance `z G z'`; it is a point-estimate utility, not an uncertainty procedure or a general extractor of crossed covariance structures.

For covariate-standardized population means, integrate at each target covariate profile and then average using declared target weights. Existing-group effects, new-group draws, and averaging over observed covariates are separate choices. Propagate uncertainty in beta and G when constructing intervals; a fixed-G plug-in calculation does not do that. [ETRANS; PRED; BOOT]

## Plotting contract

Pair a descriptive view with an estimand view. Show observed observations/trajectories or rates with denominators, and model-based means, slopes, or contrasts with labeled uncertainty. For interactions, plot conditional curves or simple contrasts at meaningful covariate values. Distinguish link from response scale, observed from new groups, and a mean interval from a prediction interval. Use a zero reference for differences and one for ratios.

A forest plot of planned contrasts is often more informative than a table of stars. A random-effects caterpillar plot visualizes shrinkage estimates and uncertainty, not a definitive ranking of intrinsic group quality. Avoid inventing a universal standardized mixed-model effect size; residual-SD, total-variation, and design-specific standardization answer different questions. A recent standardized-effect-size paper explicitly makes a proposal [ESIZE], not a universally agreed rule.

Multiplicity belongs to the scientific claim family. `emmeans` may adjust separately within each `by` group; combining results across groups changes that family. Name both the p-value and interval adjustment, and verify what the software actually returned. Do not infer “different effects” from one significant and one nonsignificant simple effect; directly test their difference. [ECOMP]
