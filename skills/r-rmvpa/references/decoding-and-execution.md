# Decoding and execution

Contents: [baseline](#runnable-regional-baseline), [outputs](#choose-the-output),
[execution](#engines-and-parallelism), [debugging](#debugging-and-cli).

## Runnable regional baseline

This checks plumbing on random data, with balanced labels within every run.
It is not a demonstration of decodable signal. `sda` is an optional dependency
needed by the selected classifier.

```r
library(rMVPA)
stopifnot(requireNamespace("sda", quietly = TRUE))
set.seed(105)
sample <- gen_sample_dataset(c(3, 3, 3), 48, blocks = 4, nlevels = 2)
metadata <- data.frame(condition = factor(rep(c("a", "b"), 24)),
                       run = rep(1:4, each = 12))
design <- mvpa_design(metadata, y_train = ~ condition, block_var = ~ run)
spec <- mvpa_model(
  load_model("sda_notune"), sample$dataset, design,
  crossval = blocked_cross_validation(design$block_var),
  tune_grid = data.frame(lambda = 0.1, diagonal = FALSE),
  return_predictions = TRUE
)
report <- validate_analysis(spec, verbose = FALSE)
# A single ROI containing the whole synthetic mask.
roi <- neuroim2::NeuroVol(array(1L, c(3, 3, 3)),
                         neuroim2::space(sample$dataset$mask))
result <- run_regional(spec, roi, backend = "default")
result$performance_table
head(result$prediction_table)
```

For this single-dataset decoding route, `.rownum` identifies the original design
row. Join prediction rows to trial/run metadata through that key; do not assume
the prediction table retains every metadata column or preserves input ordering.

Inspect `load_model()` and the registry for available algorithms and their
dependencies. A named classifier may have its own tuning path. Do not assume a
single universal nested-tuning contract across classifiers. `tune_grid` must have
the parameters expected by that registry entry. For ordinary scalar regression,
use a regression-capable model and `model_type = "regression"`.

## Choose the output

| Need | Runner | Inspect |
|---|---|---|
| Independent fits per atlas region | `run_regional(spec, region_mask)` | `$performance_table`, `$prediction_table`, `$vol_results`, retained `$fits` where supported |
| Local scalar maps | `run_searchlight(spec, radius = ..., method = "standard")` | `names(result$results)`, each metric's structure, failures and spatial coverage |
| One whole-domain classifier with importance | `run_global(spec)` | Actual result class, performance, importance fields and retained fits |

Regional label maps use positive integer IDs; zero is background. Validate their
geometry against the dataset and check which regions survive mask intersection.
Do not treat separate regional fits as restrictions of one global fit.

For volumetric searchlights, radius is in **millimeters**. Surface neighborhoods
have their own geometry semantics: inspect the surface method. A standard
searchlight centers on active features. Randomized/resampled methods change
coverage and aggregation; averaged overlapping-sphere scores are not the same
estimand as a standard center map.

Searchlight results can contain `searchlight_performance` wrappers rather than
bare volumes. Inspect `str(result$results[[metric]], max.level = 1)`; the wrapper's
image is `$data`. Do not assume `$performance` or a particular metric spelling.
Tiny or degenerate regions can produce missing metrics; a nonempty object is not
evidence that every ROI succeeded. Performance and Haufe patterns are descriptive
or predictive quantities, not voxel significance maps.

`save_results(result, dir, level = "standard", overwrite = FALSE)` writes supported
results. Inspect its result-class methods before using it for a new family. Use
`saveRDS()` for complete family objects when required by their documentation.

## Engines and parallelism

Execution has separate controls:

- `method` selects searchlight sampling/aggregation.
- `engine` (where supported) selects a numerical implementation. Use
  `explain_searchlight_engine(spec, method = "standard", engine = "auto")` and
  `searchlight_engines()` to inspect eligibility instead of forcing a fast path.
- `backend` selects data transport: `default`, experimental `shard`, or `auto`.
  Auto may fall back. Record the path that actually ran.
- `future::plan()` selects worker topology for core runners. Use sequential
  execution for a small debugging case. For an authorized parallel run, scope the
  plan in a function, save the prior plan, and restore it with `on.exit()`.

Multisession workers own private model workspaces. Shard reduces source-data
transport, not all copies or fit memory. It requires a compatible optional
`shard` installation and supported data; multibasis support must be checked.
Worker count, batch size, native threads, and retained outputs jointly determine
memory. Set relevant BLAS/OpenMP limits before R starts. Do not infer that rMVPA
uses OpenMP merely because a library links to its runtime.

Benchmark identical rows, regions, folds, seeds, outputs, and numerical settings.
Switching Feature RSA from blocked selection to `max` changes the method; it is
not a speedup of the same analysis.

## Debugging and CLI

First identify the loaded package path, version, failing model class, dimensions,
and smallest failing region. Run that case sequentially and inspect its error
payload. Check geometry, factor levels, optional dependencies, actual model
formals and method dispatch before changing the statistical design or worker count.

For config-driven work, inspect `mvpa_config()` → `build_analysis()` →
`run_analysis()` and `vignette("CommandLine")`. Use the packaged wrappers'
`--help` to verify flags. `install_cli()` copies wrappers onto a chosen path;
do this only when installation is part of the task. Old standalone script names
and archived continuous-decoder APIs are not substitutes for the packaged CLI.

Source/help pointers: `mvpa_model`, `run_regional`, `run_searchlight`,
`run_global`, `save_results`, `explain_searchlight_engine`; vignettes
`Regional_Analysis`, `Searchlight_Analysis`, `Parallelism`, `CommandLine`.
