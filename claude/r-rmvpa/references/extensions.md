# Custom calculations and model plugins

Use the smallest supported extension surface that fits the task.

## Custom callbacks

`run_custom_regional(dataset, region_mask, custom_func, ...)` calls a function
with `roi_data` (observations × features) and `roi_info` (`id`, `indices`). Return
a named list or one-row data frame of scalar metrics. Inspect the returned table's
`error` and `error_message` columns, not just row count.

`run_custom_searchlight(dataset, custom_func, radius, ...)` uses `sl_data` and
`sl_info`, including center and feature indices. For external test data,
`sl_info$test_data` carries the corresponding test sphere. Caller metadata can be
passed through `user_data` and read as `sl_info$user_data`. All successful spheres
must emit the same named scalar metrics. Randomized aggregation requires metrics
that can meaningfully be averaged over overlapping spheres.

The callback owns its statistical calculation. The wrapper supplies extraction,
iteration, and error handling; it does not automatically add CV, nuisance control,
or valid inference to an arbitrary callback. The `.cores` option belongs to these
wrappers; do not assume all core runners accept it.

## Reusable model family

Build with `create_model_spec()`, define `fit_roi.<class>()`, and declare
`output_schema.<class>()`. `fit_roi` receives structured ROI data and a context;
return a `roi_result` with named metrics, feature indices, and the context ID.
This differs from the raw-matrix custom callback contract.

Use `model$crossval` and model-specific target accessors. If the family fits the
ordinary classification/regression contract, `cv_evaluate_roi()` can manage fold
execution. Matrix targets are retrieved through `model_targets()`, not inferred
from the bookkeeping labels. Declare scalar searchlight output separately from
larger regional payloads and retained fits.

Check `mock_roi_data()`, `mock_context()`, `validate_plugin_model()` and
`validate_model_spec()` on a small example before running the spatial engine.
Register S3 methods correctly for package versus interactive use. Do not forge
private classes or patch namespace internals to bypass a missing contract.
Plugin validation checks interfaces; numerical accuracy needs an independent
reference or invariant appropriate to the new calculation.

For ITEM, inspect `item_design()`, `item_model()` and `vignette("ITEM_Decoding")`;
first-level estimation is delegated to the documented fmrilss integration.
The archived hrfdecoder API is not a current exported continuous-analysis family.

Source/help pointers: `run_custom_regional`, `run_custom_searchlight`,
`create_model_spec`, `fit_roi`, `roi_result`, `output_schema`,
`validate_plugin_model`; vignettes `CustomAnalyses`, `Plugin_Development`,
`ITEM_Decoding`.
