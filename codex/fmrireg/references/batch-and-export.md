# Native jobs, portable execution, and export

fmrireg already has the workflow abstraction needed by the skill. Use one
`fmri_template` for the scientific invariant and per-subject/unit bindings for
scans, TR, run_length, events, confounds and mask. Real datasets use file paths,
not giant embedded matrices. The binding ID is unique and traceable to original
subject/session/acquisition keys; do not make repeated observations independent.

```r
library(fmrireg)
mani <- as_manifest(bindings)
jobs <- instantiate(template, mani)
flight <- preflight(jobs)
stopifnot(flight$ok)
# After authorized pilot/full launch:
res <- run_jobs(jobs)
errors <- batch_errors(res)
values <- batch_values(res)
```

The reviewed `run_jobs()` isolates per-job failures. Inspect errors and never
count a partial batch as complete. `reduce_betas()` returns compact teaching/ROI
tables; `reduce_contrasts()` returns contrast tables; `reduce_write_results()`
writes maps on the worker and returns paths. Model explicit contrasts to write
both beta and SE as required by downstream group models.

```r
con <- contrast_set(pair_contrast(~ trial_type == "incongruent",
                                 ~ trial_type == "congruent",
                                 name = "incong_gt_cong"))
# This is a structural example, not an approved scientific default.
template <- fmri_template(
  onset ~ hrf(trial_type, contrasts = con), ~ run,
  baseline = baseline_spec(degree = 3, basis = "bs",
                          confounds = bidser::confound_set("motion24")),
  reducer = reduce_write_results(format = "nifti", stats = c("beta", "se"),
                                 path = output_dir))
```

For local parallel work configure `future` then `run_jobs(jobs, parallel=TRUE)`;
sequential is the reference route. For arrays use `export_jobs(jobs, jobs_dir)`
which supplies manifest.rds and run_one.R. Workers need identical package versions,
accessible file paths, masks and output permissions. A serialized job does not
make paths portable. Keep scheduler flags outside the model and respect site
policies. Do not introduce a mandatory daemon, cloud service or job-graph system.

Resume using input/code/environment hashes and per-unit receipts. Stage temporary
outputs and retain failed attempts. Compare actual successes to the approved
cohort; assess whether failures change representativeness or estimability before
group analysis. Never silently discard failed subjects.

The reviewed fmrireg convenience group path is collect_results -> fmri_meta.
The workbench's group target is **fmrigds**, so perform an explicit documented
handoff rather than assuming collect_results returns a GDS. A small table bridge
uses sample/subject/contrast/beta/var; large image/HDF5 routes use validated native
adapters. Preserve covariance and spatial semantics, not just filenames.
