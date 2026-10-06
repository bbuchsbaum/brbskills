#!/usr/bin/env Rscript
# Read-only public-API inspection. Run with the same R library paths as the analysis.
args <- commandArgs(trailingOnly = TRUE)
if (any(args %in% c("--help", "-h"))) {
  cat("Usage: Rscript --vanilla inspect_runtime.R [exported_symbol ...]\n",
      "Reports the loaded rMVPA installation and requested function signatures.\n",
      "Does not install packages, read data, or evaluate model functions.\n", sep = "")
  quit(status = 0L)
}
if (!requireNamespace("rMVPA", quietly = TRUE)) {
  cat("rMVPA cannot be loaded from this R session's library paths.\n", file = stderr())
  quit(status = 2L)
}
pkg <- utils::packageDescription("rMVPA")
cat(R.version.string, "\n")
cat("Package path:", find.package("rMVPA"), "\n")
for (key in c("Version", "Built", "RemoteRef", "RemoteSha")) {
  value <- pkg[[key]]
  cat(key, ": ", if (is.null(value)) "not recorded" else value, "\n", sep = "")
}
exports <- getNamespaceExports("rMVPA")
if (!length(args)) {
  cat("Supply exported symbols to inspect their signatures.\n")
  quit(status = 0L)
}
missing <- setdiff(args, exports)
for (name in intersect(unique(args), exports)) {
  cat("\n", name, "\n", sep = "")
  object <- getExportedValue("rMVPA", name)
  if (is.function(object)) print(args(object)) else cat("Exported object of class:", class(object), "\n")
}
if (length(missing)) {
  cat("Not exported by this installation: ", paste(missing, collapse = ", "), "\n",
      sep = "", file = stderr())
  quit(status = 2L)
}
