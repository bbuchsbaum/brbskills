#!/usr/bin/env Rscript
# First pass only: joins, BIDS validator, preprocessing QC and readiness stay unchecked.
argv <- commandArgs(trailingOnly = TRUE)
if (length(argv) != 2L || any(argv %in% c("-h", "--help"))) {
  cat("Usage: Rscript discover_bids.R BIDS_ROOT NEW_INVENTORY.json\n")
  quit(status = if (any(argv %in% c("-h", "--help"))) 0L else 2L)
}
for (p in c("bidser", "jsonlite")) if (!requireNamespace(p, quietly = TRUE)) stop("Missing package: ", p)
root <- normalizePath(argv[1], mustWork = TRUE); out <- argv[2]
if (!dir.exists(root)) stop("Root must be a directory")
if (file.exists(out)) stop("Refusing to overwrite inventory")
proj <- bidser::bids_project(root, fmriprep = TRUE)
query_scope <- function(scope) {
  z <- bidser::query_files(proj, scope = scope, return = "tibble", full_path = TRUE,
                          match_mode = "exact", refresh = TRUE)
  if (is.null(z) || !nrow(z)) return(data.frame())
  z <- as.data.frame(z)
  if (!"path" %in% names(z)) stop("Installed query_files lacks 'path'; inspect adapter")
  z$.scope <- scope; z
}
tables <- list(query_scope("raw"), query_scope("derivatives"))
files <- unlist(lapply(tables, function(t) if (nrow(t)) as.character(t$path) else character()), use.names = FALSE)
scopes <- unlist(lapply(tables, function(t) if (nrow(t)) t$.scope else character()), use.names = FALSE)
keep <- !duplicated(files); files <- files[keep]; scopes <- scopes[keep]
is_bold <- grepl("_bold\\.(nii(\\.gz)?|dtseries\\.nii)$", basename(files))
entity <- function(path, key) {
  fields <- strsplit(basename(path), "_", fixed = TRUE)[[1]]
  hit <- fields[startsWith(fields, paste0(key, "-"))]
  if (length(hit) == 1L) substring(hit, nchar(key) + 2L) else NULL
}
read_one <- function(path, scope) {
  resolved <- tryCatch(bidser::get_metadata(proj, path, inherit = TRUE, scope = "auto", provenance = TRUE),
                       error = function(e) list(error = conditionMessage(e)))
  md <- resolved$metadata
  header <- NULL; header_error <- NULL
  is_cifti <- grepl("\\.dtseries\\.nii$", path)
  if (!is_cifti && requireNamespace("RNifti", quietly = TRUE)) {
    header <- tryCatch(as.list(RNifti::niftiHeader(path)), error = function(e) {header_error <<- conditionMessage(e); NULL})
  } else header_error <- if (is_cifti) "CIFTI needs its own space/timing adapter" else "RNifti missing"
  tr <- md$RepetitionTime
  if (!is.numeric(tr) || length(tr) != 1L || !is.finite(tr) || tr <= 0) tr <- NULL
  if (!is.null(md$VolumeTiming)) tr <- NULL
  n <- if (!is.null(header$dim) && length(header$dim) >= 5L) as.integer(header$dim[5]) else NULL
  keys <- c("dim", "pixdim", "xyzt_units", "qform_code", "sform_code", "srow_x", "srow_y", "srow_z",
            "quatern_b", "quatern_c", "quatern_d", "qoffset_x", "qoffset_y", "qoffset_z")
  snapshot <- if (is.null(header)) NULL else header[intersect(names(header), keys)]
  tr_check <- NULL
  if (!is.null(header$pixdim) && length(header$pixdim) >= 5L && is.numeric(header$xyzt_units) && length(header$xyzt_units) == 1L) {
    unit <- bitwAnd(as.integer(header$xyzt_units), 56L)
    scale <- switch(as.character(unit), "8" = 1, "16" = 1e-3, "24" = 1e-6, NA_real_)
    if (!is.null(tr) && is.finite(scale)) tr_check <- abs(header$pixdim[5] * scale - tr) <= max(1e-6, tr * 1e-5)
  }
  info <- file.info(path)
  list(subject = entity(path, "sub"), session = entity(path, "ses"), task = entity(path, "task"),
       run = entity(path, "run"), acquisition = entity(path, "acq"), direction = entity(path, "dir"),
       echo = entity(path, "echo"), part = entity(path, "part"), recording = entity(path, "recording"),
       space = entity(path, "space"), resolution = entity(path, "res"), density = entity(path, "den"),
       description = entity(path, "desc"), pipeline = NULL,
       path = path, scope = scope, selected = FALSE, tr = tr, nvols = n,
       metadata = resolved, header = snapshot, header_error = header_error,
       metadata_header_tr_consistent = tr_check, event_file = NULL, confound_file = NULL,
       confound_rows = NULL, mask = NULL, grid_id = NULL, timing_origin = NULL,
       index_fingerprint = list(size = unname(info$size), mtime = as.character(info$mtime)))
}
runs <- lapply(which(is_bold), function(i) read_one(files[i], scopes[i]))
result <- list(schema_version = "1.0", generated_at = format(Sys.time(), tz = "UTC", usetz = TRUE),
               root = root, bidser_version = as.character(utils::packageVersion("bidser")),
               files = lapply(seq_along(files), function(i) list(path = files[i], scope = scopes[i])), runs = runs,
               validation = list(enumeration = "completed", metadata_resolution = "attempted_per_run",
                 header_read = "attempted_for_nifti", metadata_header_consistency = "partial",
                 event_confounds_matching = "not_checked", pipeline_identity = "not_checked",
                 spatial_compatibility = "not_checked", bids_validator = "not_run",
                 preprocessing_qc = "not_checked", analysis_readiness = "not_certified"),
               note = "Finish provenance, keyed joins, selections and scientific checks. Size/mtime is not a content hash.")
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- tempfile(pattern = ".inventory-", tmpdir = dirname(out))
jsonlite::write_json(result, tmp, pretty = TRUE, auto_unbox = TRUE, null = "null", na = "null")
if (!file.rename(tmp, out)) { unlink(tmp); stop("Could not finalize inventory") }
cat(jsonlite::toJSON(list(output = out, indexed_files = length(files), bold_candidates = length(runs),
                         readiness = "not_certified"), auto_unbox = TRUE), "\n")
