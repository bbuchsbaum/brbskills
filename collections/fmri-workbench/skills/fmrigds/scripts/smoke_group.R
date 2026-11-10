#!/usr/bin/env Rscript
# Arithmetic test of fixed pooling only; NOT a recommendation for population inference.
if (any(commandArgs(TRUE) %in% c("--help", "-h"))) {
  cat("Usage: Rscript smoke_group.R\n"); quit(status = 0L)
}
if (!requireNamespace("fmrigds", quietly = TRUE)) stop("Install/pin fmrigds in the authorized environment first")
suppressPackageStartupMessages(library(fmrigds))
# Unequal variances distinguish inverse-variance pooling from an ordinary mean.
fixture <- data.frame(
  sample = rep(c("ROI_1", "ROI_2"), 3),
  subject = rep(sprintf("synthetic-%02d", 1:3), each = 2),
  contrast = "A_minus_B",
  beta = c(.5, .8, 1, 1.2, .7, .9),
  var = c(.04, .09, .16, .04, .09, .16))
expected_ids <- c("ROI_1", "ROI_2")
expected <- vapply(expected_ids, function(id) {
  x <- fixture[fixture$sample == id, ]
  variance <- 1 / sum(1 / x$var)
  beta <- sum(x$beta / x$var) * variance
  c(beta = beta, var = variance, z = beta / sqrt(variance))
}, numeric(3))

check_order <- function(rows) {
  f <- tempfile(fileext = ".csv")
  on.exit(unlink(f))
  write.csv(fixture[rows, ], f, row.names = FALSE)
  r <- compute(reduce(gds(f), method = "fixed"))
  # Sample identity belongs to the public space descriptor; assay dimnames may
  # legitimately be NULL. Do not substitute positional or fabricated labels.
  ids <- fmrigds::space(r)$labels
  stopifnot(is.character(ids), length(ids) == length(expected_ids),
            !anyNA(ids), all(nzchar(ids)), !anyDuplicated(ids),
            setequal(ids, expected_ids))
  ord <- match(expected_ids, ids)
  for (name in rownames(expected)) {
    values <- assay(r, name)
    stopifnot(identical(as.integer(dim(values)), c(length(ids), 1L, 1L)),
              all(is.finite(values)),
              max(abs(as.numeric(values)[ord] - expected[name, ])) < 1e-8)
  }
}
check_order(seq_len(nrow(fixture)))
check_order(rev(seq_len(nrow(fixture))))
cat("PASS: GDS tabular ingestion and inverse-variance fixed-pooling arithmetic\n")
