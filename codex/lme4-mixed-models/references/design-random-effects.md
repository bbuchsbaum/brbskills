# Design, parameterization, and random effects

## Start with the generative structure

For a Gaussian LMM write `y = X beta + Z b + epsilon`, with `b ~ N(0,G)` and conditional residual covariance specified by the model. For a GLMM specify the conditional response distribution and `g(E[y|b]) = X beta + Z b + offset`. This notation separates fixed-effect hypotheses, random covariance, and residual assumptions. [LMM-PAPER; GLMM]

Record what one row represents; which units were sampled or randomized; whether the claim generalizes to new subjects, items, sites, or occasions; and which predictors vary within each group. Create a support table before choosing slopes. Partial crossing is possible: complete subject-by-item coverage is not required, but confounding and disconnected sampling components need review.

```r
# Illustrations, not formulas to copy without a design audit:
y ~ condition + (1 | subject) + (1 | item)      # crossed intercepts
y ~ time + (1 | site / subject)               # site plus site:subject
y ~ time + (1 + time | subject)               # correlated slope/intercept
```

When subject IDs repeat across sites, use the composite identifier. When they are globally unique, `(1|site)+(1|subject)` can represent the same nesting. Formula notation does not establish the actual design. Do not replace crossed factors with `subject/item` merely because items occur in subjects' records. [FAQ]

## Which slopes?

A condition varying within subjects supports consideration of subject-specific condition slopes. A condition fixed within each item provides no within-item condition comparison from which to interpret an item-specific condition slope. A cross-level interaction may require the within-group component's slope rather than an unidentifiable slope for a between-group predictor. Inspect the relevant random-effect design matrix, not only the variable names. Barr's interaction analysis explains why the slope structure must match the tested interaction. [MAX; INT]

A between-group predictor can sometimes parameterize a model for how group variance changes across groups. That is a deliberate heteroscedasticity model, not evidence of within-group slope information; its identification and constraints need separate review.

Unbalanced data, few independent groups, sparse cells, and repeated measurements with little within-group variation constrain information. There is no universal minimum group count guaranteeing valid variance estimates or inference. A random-vs-fixed decision should reflect the estimand and sampling structure, not a preliminary significance test. [ECO; FAQ]

## Maximality policy

Implement the policy declared in the analysis contract. For the skill's pragmatic simplification policy, identify essential slopes first, fit a design-supported starting structure, diagnose support, and propose a small, recorded set of alternatives. Removing correlations before essential slopes is a possible path, not an invariant theorem. A zero-correlation assumption itself needs interpretation. Never search alternatives by the focal p-value. If a simplification materially changes the scientific conclusion, report that sensitivity rather than promoting the convenient model. [PARS; POWER]

The number of free covariance parameters in a full q-dimensional block is `q*(q+1)/2` (derived by counting the lower triangle). This is separate from q times the number of group levels, which counts latent random coefficients. Many latent coefficients are partially pooled; do not use either count alone as an identifiability proof.

## Correlated versus independent coefficients

```r
# Numeric x:
y ~ x + (1 + x | group)                # free intercept/slope covariance
y ~ x + (1 | group) + (0 + x | group)  # zero covariance
y ~ x + (1 + x || group)               # numeric shorthand; inspect expansion

# Factor f with three levels: explicitly construct two numeric contrasts
# c1, c2 from a stored, named contrast matrix before fitting.
y ~ f + (1 | group) + (0 + c1 | group) + (0 + c2 | group)
```

`(0 + f | group)` is generally a multivariate correlated factor coefficient block, not independent contrast slopes. The lme4 documentation limits its `||` shortcut to numeric design matrices and points to explicit dummy variables or `afex::lmer_alt` for categorical effects. Verify the installed implementation and the intended coefficient basis. [LMM]

## Why centering is not always harmless: a derivation

Let the random contribution be `b0 + b1*x`; set `x_c = x-c`. Then `b0_c = b0+c*b1` and

`Cov(b0_c,b1) = Cov(b0,b1) + c*Var(b1)`.

Even when the original covariance is zero, it will generally not remain zero after centering. A full covariance family can absorb this invertible change of basis; a diagonal covariance restriction generally cannot. The same issue occurs under rotations of categorical contrasts. Therefore an agent must not claim that every recoding is only a numerical optimization or that dropping correlations is parameterization-independent. Store the basis and centering constants.

## Separate within and between effects

For a predictor x measured repeatedly, a useful question-specific decomposition is

```r
d$x_between <- ave(d$x, d$subject, FUN = mean)
d$x_within <- d$x - d$x_between
# Optional centering of x_between around a meaningful population/reference value.
y ~ x_within + x_between + (1 + x_within | subject)
```

Within-person association and between-person association are different targets. Grand-mean centering alone does not separate them. Their interpretation, measurement error in estimated group means, longitudinal dynamics, and informative sampling require additional judgment; the displayed decomposition is not a universal causal adjustment. [CENTER; BLOG-C]

For treatment-coded factors, label the reference level. For sum/custom contrasts, record the actual matrix. Check the model matrix and map each coefficient to its hypothesis. For a binary predictor coded `-0.5,+0.5`, the coefficient is the high-minus-low difference; with `-1,+1`, the difference is twice the coefficient. This follows directly by subtracting the two fitted linear predictors. [CONTR]

## Stop conditions

Hold unsupported claims when a focal contrast is nonestimable, grouping IDs are ambiguous, design information is missing, or the desired effect is confounded with group membership. Numerical convergence is irrelevant to those identification problems. Use the helper's support summaries as prompts for review, not automated slope inclusion/exclusion.
