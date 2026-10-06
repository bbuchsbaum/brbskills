#!/usr/bin/env Rscript
# Execute the actual fenced examples so documentation and checks cannot drift.
# Usage: Rscript --vanilla tests/run_examples.R (from any working directory).
script_arg <- grep("^--file=", commandArgs(), value = TRUE)
if (length(script_arg) != 1L) stop("Run this file with Rscript.")
skill <- dirname(dirname(normalizePath(sub("^--file=", "", script_arg))))
required <- c("rMVPA", "neuroim2", "sda")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing example dependencies: ", paste(missing, collapse = ", "))
cat("rMVPA", as.character(utils::packageVersion("rMVPA")), "at", find.package("rMVPA"), "\n")
extract_r <- function(path) {
  lines <- readLines(path, warn = FALSE)
  active <- FALSE
  code <- character()
  for (line in lines) {
    if (!active && identical(line, "```r")) {
      active <- TRUE
    } else if (active && identical(line, "```")) {
      active <- FALSE
      code <- c(code, "")
    } else if (active) code <- c(code, line)
  }
  if (active || !length(code)) stop("Missing or unclosed R example: ", path)
  parse(text = code)
}
routes <- c("data-and-validation", "decoding-and-execution", "rsa", "encoding", "pattern-models")
for (route in routes) {
  env <- new.env(parent = globalenv())
  eval(extract_r(file.path(skill, "references", paste0(route, ".md"))), env)
  if (route == "data-and-validation") {
    stopifnot(identical(rMVPA::y_train(env$design), seq_len(env$n)))
  } else if (route == "encoding") {
    stopifnot(inherits(env$result, "banded_ridge_result"),
              identical(dim(env$result$predictions), dim(env$brain)),
              all(is.finite(env$result$predictions)),
              nrow(env$result$metrics) == prod(env$dims))
  } else {
    stopifnot(is.data.frame(env$result$performance_table),
              nrow(env$result$performance_table) == 1L)
    metrics <- env$result$performance_table
    numeric_metrics <- metrics[vapply(metrics, is.numeric, logical(1))]
    stopifnot(length(numeric_metrics) > 0L, all(is.finite(as.matrix(numeric_metrics))))
    if (route == "decoding-and-execution") {
      stopifnot(nrow(env$result$prediction_table) == 48L)
    }
    if (route == "pattern-models") {
      stopifnot(inherits(env$result, "pattern_global_result"),
                length(env$result$fold_fits) == 4L,
                inherits(env$result$refit, "pattern_fit"))
    }
  }
  cat("PASS example:", route, "\n")
}
cat("PASS all five public-API examples. These are smoke checks, not scientific qualification.\n")
