#!/usr/bin/env Rscript
# Tiny synthetic compatibility/oracle check. No real data or scientific defaults.
# Requires the source-reviewed typed-control/template API. Not run when bundled.
if (any(commandArgs(TRUE) %in% c("--help", "-h"))) {
  cat("Usage: Rscript smoke_first_level.R\n"); quit(status = 0L)
}
if (!requireNamespace("fmrireg", quietly = TRUE)) stop("Install/pin fmrireg in the authorized environment first")
suppressPackageStartupMessages(library(fmrireg))
needed <- c("fmri_template", "instantiate", "preflight", "run_jobs", "batch_values", "batch_errors",
            "fmri_lm_control", "estimation_spec", "noise_spec", "baseline_spec", "reduce_betas")
stopifnot(all(needed %in% getNamespaceExports("fmrireg")))
set.seed(1043)
runs <- c(80L, 80L); TR <- 2
make_events <- function() do.call(rbind, lapply(1:2, function(r) {
  data.frame(onset = seq(4, 140, by = 8), condition = factor(rep(c("A", "B"), length.out = 18)), run = r)
}))
events <- make_events()
sf <- sampling_frame(blocklens = runs, TR = TR)
em <- event_model(onset ~ hrf(condition), block = ~ run, data = events, sampling_frame = sf)
X <- as.matrix(design_matrix(em))
stopifnot(is.matrix(X), nrow(X) == sum(runs), ncol(X) > 0L, !is.null(colnames(X)))
truth <- stats::setNames(seq_len(ncol(X)), colnames(X))
scales <- c(1, 1.5, -0.5)
make_binding <- function(id) {
  signal <- drop(X %*% truth)
  Y <- outer(signal, scales) + matrix(rnorm(sum(runs) * length(scales), sd = 0.001), sum(runs))
  list(id = id, scans = Y, TR = TR, run_length = runs, events = events)
}
bindings <- list(make_binding("synthetic-01"), make_binding("synthetic-02"))
template <- fmri_template(onset ~ hrf(condition), ~ run,
  baseline = baseline_spec(degree = 3, basis = "bs"),
  control = fmri_lm_control(estimation = estimation_spec("joint"), noise = noise_spec("iid")),
  reducer = reduce_betas())
jobs <- instantiate(template, bindings)
flight <- preflight(jobs); stopifnot(isTRUE(flight$ok))
res <- run_jobs(jobs); stopifnot(length(batch_errors(res)) == 0L)
values <- batch_values(res); stopifnot(length(values) == 2L)
for (tab in values) {
  stopifnot(all(c("term", "voxel", "estimate", "se") %in% names(tab)))
  for (nm in names(truth)) {
    z <- tab[tab$term == nm, , drop = FALSE]
    z <- z[order(z$voxel), , drop = FALSE]
    stopifnot(nrow(z) == length(scales), all(is.finite(z$estimate)), all(is.finite(z$se)),
              max(abs(z$estimate - truth[[nm]] * scales)) < 0.05)
  }
}
cat("PASS: native first-level templates/preflight/jobs and synthetic coefficient recovery\n")
