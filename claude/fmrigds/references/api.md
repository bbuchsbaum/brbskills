# Source-reviewed fmrigds API card

The core grammar is lazy: `gds` -> subset/derive/reduce/posthoc/write_out ->
`compute`. Realized GDS assays are sample x subject x contrast. Common assays
are beta, var, t, z, p; SE input must be interpreted explicitly. gds supports
multiple native formats; inspect the adapter for each installed version.

```r
library(fmrigds)
# Canonical tiny CSV: sample,subject,contrast,beta,var
plan <- gds("roi_stats.csv") |>
  subset(contrast = "A_minus_B") |>
  reduce(method = "random")
explain(plan)
preview(plan)
# After model/correction/limits are approved:
result <- compute(plan)
```

"random" is an example of a precision-aware reducer, not a universal default.
`reduce(method="fixed")` is useful for arithmetic tests or justified fixed-effect
pooling, not the default for population inference. `one_sample()`, `group_ols()`
and `"perm:onesample"` are mentioned in the current getting-started vignette for
unweighted values; inspect their own installed help before using their arguments.

```r
plan <- gds("roi_stats.csv", col_data = covariates) |>
  reduce(method = "meta:re_reg", formula = ~ group + age)
```

Key covariates by subject; verify rownames/order, missingness, factors and coding.
`with_col_data()` and `model_matrix()` support explicit alignment and designs.
`assay(result,"beta")`, `assays(result)`, `gds_to_tibble()` expose outputs; do
not assume identical assay names for different reducers. Meta-regression can
return named coefficient/SE assays such as `coef:age` and `se_coef:age`.

Posthoc public registry: `register_posthoc`, `list_posthoc`, `get_posthoc`;
`posthoc(plan,"fdr:bh")` / `"fdr:by"` are documented. Confirm family semantics
in the installed method and choose how contrasts/estimands enter the family.
If the package cannot implement the prespecified family, use a tested explicit
correction adapter or report a blocker. Never correct separately by processing chunk.

`write_out(plan,"output.h5",format="h5")` records a lazy export;
`compute(plan,block=list(sample=10000))` supports bounded spatial blocks.
Use `space()` / `assert_compatible_spaces()` and inspect native NIfTI export
contracts rather than inventing a `write_nifti` helper in this package.

`examine_group()` can inspect an unreduced-prefix cohort using the frozen group
model. Its validity/surprise/influence distinction is important; see inference
reference. `write_report(exam,...)` is a cohort review artifact, distinct from
neuromosaic's final spatial reports.
