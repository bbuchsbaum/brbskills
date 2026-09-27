# Source-reviewed fmrireg API card

Reviewed 2026-09-27. Verify installed signatures; examples are not a package lock.
Current frames are fmridataset `fmri_frame` objects via fmrireg's public exports:
`matrix_frame`, `neurovec_frame`, `nifti_frame`, `latent_frame`.

```r
library(fmrireg)
ds <- matrix_frame(Y, TR = TR, run_length = run_lengths, event_table = events)
sf <- sampling_frame(blocklens = run_lengths, TR = TR)
con <- pair_contrast(~ condition == "A", ~ condition == "B", name = "A_minus_B")
ev <- event_model(onset ~ hrf(condition, contrasts = con), block = ~ run,
                  data = events, sampling_frame = sf)
base <- baseline_model(basis = "bs", degree = 3, sframe = sf)
model <- fmri_model(ev, base, dataset = ds)
fit <- fmri_lm(model)
```

This example supplies no nuisance/noise policy: add the **approved** supported
configuration. Explicit duration/amplitude/basis options require installed help;
never assume onset~hrf(condition) automatically uses every events column.
For a formula shortcut:

```r
fit <- fmri_lm(onset ~ hrf(condition, contrasts = con), block = ~ run, dataset = ds)
b <- coef(fit, type = "contrasts")$A_minus_B
s <- standard_error(fit, type = "contrasts")$A_minus_B
t <- stats(fit, type = "contrasts")$A_minus_B
p <- p_values(fit, type = "contrasts")$A_minus_B
```

Design matrices are time x coefficient. The overview's coefficient matrix is
voxel x coefficient; assert orientation/dimnames rather than transposing by habit.
`event_model`, `baseline_model`, HRF/design helpers may be reexports from
fmridesign/fmrihrf. Public reexports are supported, not a reason to use internals.

The reviewed template baseline signature:

```r
baseline_spec(degree = 3, basis = c("bs", "poly", "ns", "constant"),
              confounds = NULL, intercept = c("runwise", "global", "none"),
              nuisance_check = c("warn", "error", "drop", "none"))
```

Freeze all actual values. Prefer nuisance_check="error" during plan development
until any legitimate constant/redundant-column handling has been reviewed. Do not
invent a `knots` argument to baseline_spec; inspect lower-level baseline support
when the analysis needs exact flexibility unavailable in the template wrapper.

`fmri_lm_control()` exposes engine/noise/variance controls, but inspect its current
help and relevant fitting method before choosing arguments. Robust weights,
autoregression and accelerated engines have distinct contracts. Production code
must explicitly use the selected configuration, not trust a package default from
a synthetic example. Use a small numerical oracle and residual diagnostics.

The reviewed typed boundary is `fmri_lm_control(estimation, noise, robust,
variance, weights, projection, na_action)`. Statistical runwise/joint fitting
belongs to `estimation_spec(scope="joint" or "runwise_meta")`; resource partitioning
belongs to `compute_spec()`. The template's default is runwise_meta, unlike the
estimation_spec default joint: set the scope explicitly. Runwise pooling currently
supports fixed_effect only (within subject, not a population assertion).

**Critical censor semantics:** `noise_spec(censor=...)` feeds AR estimation and
whitening only. It does NOT remove observations from the regression and has no
effect for `struct="iid"`. Do not describe it as scrubbing or infer that contaminated
volumes no longer affect beta estimates. Choose and test an actual regression-level
spike/weight/removal route when that is the intended policy. `noise_spec` supports
iid, ar1, ar2, arp, with q>0 requesting a more restricted ARMA path. Voxelwise AR,
ARMA, censoring, robust options and weights are not freely composable; inspect
installed help before combining them.

Existing source references: README; vignettes/fmrireg.Rmd;
vignettes/a_09_linear_model.Rmd; vignettes/a_05_contrasts.Rmd;
vignettes/multisubject_fanout.Rmd. Inspect the latter two only when needed.
