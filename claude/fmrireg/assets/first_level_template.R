# Source this reviewed template into a study script; it does not launch jobs.
# Core scientific arguments have no defaults. Supply them from the approved plan.
build_first_level_jobs <- function(bindings, formula, block, baseline, durations,
                                   control, reducer, contrasts = NULL,
                                   compute = NULL, engine = NULL, engine_args = list()) {
  if (!requireNamespace("fmrireg", quietly = TRUE)) stop("fmrireg is required")
  stopifnot(inherits(formula, "formula"), inherits(block, "formula"), is.function(reducer))
  if (missing(control) || is.null(control)) stop("Supply an explicit reviewed fmri_lm_control")
  if (!is.list(bindings) || !length(bindings)) stop("Supply validated nonempty bindings")
  args <- list(formula = formula, block = block, baseline = baseline, durations = durations,
               contrasts = contrasts, control = control, reducer = reducer,
               engine = engine, engine_args = engine_args)
  if (!is.null(compute)) args$compute <- compute
  template <- do.call(fmrireg::fmri_template, args)
  jobs <- fmrireg::instantiate(template, fmrireg::as_manifest(bindings))
  flight <- fmrireg::preflight(jobs)
  if (!isTRUE(flight$ok)) stop("Native preflight failed; inspect the plan and bindings before launch")
  list(template = template, jobs = jobs, preflight = flight)
}
# Call fmrireg::run_jobs(result$jobs) separately only after matching plan approval.
# Censor in noise_spec affects AR estimation/whitening, not GLM row removal.
