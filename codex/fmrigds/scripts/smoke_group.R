#!/usr/bin/env Rscript
# Arithmetic test of fixed pooling only; NOT a recommendation for population inference.
if (any(commandArgs(TRUE) %in% c("--help", "-h"))) {
  cat("Usage: Rscript smoke_group.R\n"); quit(status = 0L)
}
if (!requireNamespace("fmrigds", quietly = TRUE)) stop("Install/pin fmrigds in the authorized environment first")
suppressPackageStartupMessages(library(fmrigds))
f <- tempfile(fileext = ".csv")
writeLines(c("sample,subject,contrast,beta,var",
  "ROI_1,synthetic-01,A_minus_B,0.5,0.04", "ROI_2,synthetic-01,A_minus_B,0.8,0.09",
  "ROI_1,synthetic-02,A_minus_B,1.0,0.04", "ROI_2,synthetic-02,A_minus_B,1.2,0.09",
  "ROI_1,synthetic-03,A_minus_B,0.7,0.04", "ROI_2,synthetic-03,A_minus_B,0.9,0.09"), f)
r <- compute(reduce(gds(f), method = "fixed"))
b <- assay(r, "beta"); v <- assay(r, "var")
ids <- dimnames(b)[[1]]
stopifnot(length(ids) == 2L, all(c("ROI_1", "ROI_2") %in% ids))
ord <- match(c("ROI_1", "ROI_2"), ids)
stopifnot(max(abs(as.numeric(b)[ord] - c(mean(c(.5, 1, .7)), mean(c(.8, 1.2, .9))))) < 1e-8,
          max(abs(as.numeric(v)[ord] - c(.04/3, .09/3))) < 1e-8)
unlink(f)
cat("PASS: GDS tabular ingestion and inverse-variance fixed-pooling arithmetic\n")
