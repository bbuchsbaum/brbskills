#!/usr/bin/env Rscript
# Usage: Rscript probe_capabilities.R OUTPUT.json [package ...]
# No installation, network access, or image data reads.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1L || args[1] %in% c("-h", "--help")) {
  cat("Usage: Rscript probe_capabilities.R OUTPUT.json [bidser fmrireg fmrigds neuromosaic]\n")
  quit(status = if (length(args)) 0L else 2L)
}
if (!requireNamespace("jsonlite", quietly = TRUE)) stop("jsonlite is required; no packages were installed.")
out <- args[1]
if (file.exists(out)) stop("Refusing to overwrite: ", out)
packages <- if (length(args) > 1L) unique(args[-1]) else c("bidser", "fmrireg", "fmrigds", "neuromosaic")
focus <- c("bids_project", "query_files", "get_metadata", "read_events", "read_confounds", "confound_set",
           "matrix_frame", "event_model", "baseline_model", "baseline_spec", "fmri_model", "fmri_lm",
           "fmri_lm_control", "fmri_template", "from_bids", "as_manifest", "instantiate", "preflight",
           "run_jobs", "reduce_write_results", "gds", "as_gds", "reduce", "compute", "validate",
           "preview", "posthoc", "write_out", "one_sample", "group_ols", "examine_group",
           "render_montage_report", "montage_interactive")
probe <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) return(list(package = pkg, installed = FALSE))
  d <- utils::packageDescription(pkg)
  ex <- sort(getNamespaceExports(pkg))
  fs <- lapply(intersect(ex, focus), function(nm) {
    x <- getExportedValue(pkg, nm)
    if (!is.function(x)) return(NULL)
    f <- formals(x)
    list(name = nm, arguments = names(f), signature = paste(deparse(base::args(x)), collapse = " "))
  })
  list(package = pkg, installed = TRUE, version = as.character(utils::packageVersion(pkg)),
       remote_sha = if (is.null(d$RemoteSha)) NULL else d$RemoteSha,
       remote_ref = if (is.null(d$RemoteRef)) NULL else d$RemoteRef,
       exports = ex, selected_functions = fs)
}
result <- list(schema_version = "1.0", generated_at = format(Sys.time(), tz = "UTC", usetz = TRUE),
               R = R.version.string, platform = R.version$platform, packages = lapply(packages, probe),
               note = "Read installed S3 method help for generic-specific arguments. This is not an environment lock.")
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- tempfile(pattern = ".capabilities-", tmpdir = dirname(out))
jsonlite::write_json(result, tmp, pretty = TRUE, auto_unbox = TRUE, null = "null", na = "null")
if (!file.rename(tmp, out)) { unlink(tmp); stop("Could not finalize output") }
cat(jsonlite::toJSON(list(output = out, packages = length(packages),
                         missing = packages[!vapply(result$packages, function(x) x$installed, logical(1))]),
                     auto_unbox = TRUE), "\n")
