#!/usr/bin/env Rscript
# Synthetic compatibility check: fit -> NIfTI beta/SE -> fmrigds -> group OLS.
# No subject data, registration, scientific defaults, or inference calibration.
args <- commandArgs(TRUE)
if (any(args %in% c("--help", "-h"))) {
  cat("Usage: Rscript smoke_nifti_handoff.R [NEW_OUTPUT_DIRECTORY]\n")
  quit(status = 0L)
}
stopifnot(length(args) <= 1L)
for (pkg in c("fmrireg", "fmrigds", "neuroim2", "RNifti", "jsonlite")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop("Install/pin ", pkg, " first")
}
suppressPackageStartupMessages(library(fmrireg))

main <- function() {
  out <- if (length(args)) args[[1]] else tempfile("nifti-handoff-")
  if (file.exists(out)) stop("Output directory must be new: ", out)
  stopifnot(dir.create(out, recursive = TRUE))
  if (!length(args)) on.exit(unlink(out, recursive = TRUE), add = TRUE)
  out <- normalizePath(out)
  set.seed(917)
  dims <- c(3L, 3L, 2L)
  bitmap <- array(FALSE, dims)
  bitmap[c(1, 4, 7, 12, 17)] <- TRUE  # Nonconsecutive spatial indices.
  nvox <- sum(bitmap)
  spatial <- neuroim2::NeuroSpace(dims, spacing = c(2, 2, 3))
  mask <- neuroim2::LogicalNeuroVol(bitmap, spatial)
  mask_path <- file.path(out, "mask.nii.gz")
  neuroim2::write_vol(mask, mask_path)
  runs <- c(80L, 80L)
  TR <- 2
  events <- do.call(rbind, lapply(1:2, function(r) data.frame(
    onset = seq(4, 140, by = 8),
    condition = factor(rep(c("A", "B"), length.out = 18)), run = r)))
  sf <- sampling_frame(runs, TR = TR)
  em <- event_model(onset ~ hrf(condition), ~ run, data = events,
                    sampling_frame = sf, durations = 0)
  X <- as.matrix(design_matrix(em))
  stopifnot(ncol(X) == 2L)
  cons <- contrast_set(
    pair_contrast(~ condition == "A", ~ condition == "B", name = "A_minus_B"),
    unit_contrast(~ condition == "A", name = "A_vs_baseline"))
  ids <- c("03", "01", "02")  # Deliberately not sorted.
  beta_ref <- se_ref <- array(NA_real_, c(nvox, length(ids), 2L))
  records <- vector("list", length(ids))
  contrast_order <- NULL
  float32 <- function(x) readBin(writeBin(as.double(x), raw(), size = 4L),
                                 "double", n = length(x), size = 4L)
  same <- function(x, y, tolerance = 1e-7) {
    stopifnot(isTRUE(all.equal(as.numeric(x), as.numeric(y), tolerance = tolerance)))
  }
  for (i in seq_along(ids)) {
    truth <- rbind(seq(0.5, 1.5, length.out = nvox) + i / 5,
                   seq(-0.4, 0.2, length.out = nvox))
    Y <- X %*% truth + matrix(rnorm(sum(runs) * nvox, sd = 0.1 + i / 20), sum(runs))
    scans <- lapply(1:2, function(r) {
      arr <- matrix(0, prod(dims), runs[r])
      rows <- (sum(runs[seq_len(r - 1L)]) + 1L):sum(runs[seq_len(r)])
      arr[which(bitmap), ] <- t(Y[rows, , drop = FALSE])
      neuroim2::NeuroVec(array(arr, c(dims, runs[r])), neuroim2::add_dim(spatial, runs[r]))
    })
    frame <- neurovec_frame(scans, mask = mask, TR = TR, event_table = events)
    fit <- fmri_lm(onset ~ hrf(condition, contrasts = cons), block = ~ run,
                   dataset = frame, durations = 0,
                   baseline_model = baseline_model(basis = "constant", sframe = sf),
                   control = fmri_lm_control(estimation = estimation_spec("joint"),
                                             noise = noise_spec("iid")),
                   compute = compute_spec(voxel_chunks = 1, progress = FALSE))
    files <- write_results(fit, path = file.path(out, paste0("sub-", ids[i])),
                            subject = ids[i], task = "synthetic", space = "synthetic",
                            format = "nifti", strategy = "by_stat", save_betas = FALSE,
                            contrasts = c("A_minus_B", "A_vs_baseline"), contrast_match = "exact",
                            contrast_stats = c("beta", "se"))
    meta <- jsonlite::read_json(files$beta$json, simplifyVector = TRUE)
    se_meta <- jsonlite::read_json(files$se$json, simplifyVector = TRUE)
    order <- as.character(meta$ContrastOrder)
    stopifnot(identical(order, as.character(se_meta$ContrastOrder)),
              setequal(order, c("A_minus_B", "A_vs_baseline")))
    if (is.null(contrast_order)) contrast_order <- order
    stopifnot(identical(order, contrast_order))
    # Compare disk values against the fitted contrasts, including FLOAT32 rounding.
    b <- as.matrix(coef(fit, type = "contrasts"))[, order, drop = FALSE]
    s <- as.matrix(standard_error(fit, type = "contrasts"))[, order, drop = FALSE]
    beta_ref[, i, ] <- matrix(float32(b), nvox)
    se_ref[, i, ] <- matrix(float32(s), nvox)
    for (stat in c("beta", "se")) {
      header <- neuroim2::read_header(files[[stat]]$nifti)
      stopifnot(identical(as.integer(header@dims[1:3]), dims))
      same(neuroim2::trans(header), neuroim2::trans(spatial))
      img <- RNifti::readNifti(files[[stat]]$nifti)
      values <- matrix(as.numeric(img), prod(dims))
      stopifnot(all(values[!as.vector(bitmap), ] == 0),
                RNifti::niftiHeader(files[[stat]]$nifti)$datatype == 16L)
      same(values[as.vector(bitmap), ], if (stat == "beta") b else s)
    }
    records[[i]] <- data.frame(subject = ids[i], beta = files$beta$nifti,
                               se = files$se$nifti, beta_json = files$beta$json,
                               se_json = files$se$json)
  }
  index <- do.call(rbind, records)
  write.table(index, file.path(out, "subjects.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
  source <- fmrigds::nifti_source(beta = index$beta, se = index$se,
                                 subjects = index$subject, contrasts = contrast_order)
  plan <- fmrigds::gds(source, format = "nifti", mask = mask_path)
  raw <- fmrigds::compute(plan)
  stopifnot(identical(dim(fmrigds::assay(raw, "beta")), dim(beta_ref)),
            identical(fmrigds::subjects(raw), ids),
            identical(fmrigds::contrasts(raw), contrast_order))
  same(fmrigds::assay(raw, "beta"), beta_ref)
  same(fmrigds::assay(raw, "se"), se_ref)
  # A +/- sign pair has identical SEs and cannot detect swapped SE volumes.
  stopifnot(max(abs(se_ref[, , 1] - se_ref[, , 2])) > 1e-5)
  se_img <- neuroim2::read_vec(index$se[1])
  swapped_path <- file.path(out, "swapped-se.nii.gz")
  neuroim2::write_vec(neuroim2::NeuroVec(as.array(se_img)[, , , 2:1], neuroim2::space(se_img)),
                      swapped_path, data_type = "FLOAT")
  swapped_paths <- index$se
  swapped_paths[1] <- swapped_path
  swapped <- fmrigds::compute(fmrigds::gds(
    fmrigds::nifti_source(beta = index$beta, se = swapped_paths,
                          subjects = ids, contrasts = contrast_order),
    format = "nifti", mask = mask_path))
  swap_detected <- tryCatch({
    same(fmrigds::assay(swapped, "se"), se_ref)
    FALSE
  }, error = function(e) TRUE)
  stopifnot(swap_detected)
  # Fixed pooling checks SE->variance conversion only; not a population default.
  fixed <- fmrigds::compute(fmrigds::reduce(plan, method = "fixed"))
  w <- 1 / se_ref^2
  same(fmrigds::assay(fixed, "beta_g"), apply(w * beta_ref, c(1, 3), sum) / apply(w, c(1, 3), sum))
  same(fmrigds::assay(fixed, "se_g"), sqrt(1 / apply(w, c(1, 3), sum)))
  group <- fmrigds::compute(fmrigds::one_sample(plan))
  same(fmrigds::assay(group, "coef:(Intercept)"), apply(beta_ref, c(1, 3), mean))
  same(fmrigds::assay(group, "se_coef:(Intercept)"), apply(beta_ref, c(1, 3), sd) / sqrt(length(ids)))
  stopifnot(all(fmrigds::assay(group, "n_obs") == length(ids)),
            all(fmrigds::assay(group, "df_res") == length(ids) - 1L))

  # Separate derived fixtures: one genuine zero and one unavailable observation.
  # These edits test import/missingness, not the preceding fitted estimates.
  partial <- index
  for (stat in c("beta", "se")) {
    img <- neuroim2::read_vec(index[[stat]][1])
    arr <- as.array(img)
    if (stat == "beta") arr[which(bitmap)[1]] <- 0
    arr[which(bitmap)[2]] <- NA_real_
    path <- file.path(out, paste0("coverage-", stat, ".nii.gz"))
    neuroim2::write_vec(neuroim2::NeuroVec(arr, neuroim2::space(img)), path, data_type = "FLOAT")
    partial[[stat]][1] <- path
  }
  partial_plan <- fmrigds::gds(
    fmrigds::nifti_source(beta = partial$beta, se = partial$se,
                          subjects = ids, contrasts = contrast_order),
    format = "nifti", mask = mask_path)
  partial_group <- fmrigds::compute(fmrigds::one_sample(partial_plan))
  partial_ref <- beta_ref
  partial_ref[1, 1, 1] <- 0
  partial_ref[2, 1, 1] <- NA_real_
  same(fmrigds::assay(partial_group, "coef:(Intercept)"),
       apply(partial_ref, c(1, 3), mean, na.rm = TRUE))
  same(fmrigds::assay(partial_group, "n_obs"),
       apply(is.finite(partial_ref), c(1, 3), sum))
  capture.output(sessionInfo(), file = file.path(out, "session-info.txt"))
  cat("PASS: two contrasts, three subjects, sparse-mask NIfTI beta/SE round trip,\n",
      "grids, subject/contrast order, detection of swapped SE volumes,\n",
      "fixed-pooling variance arithmetic, group OLS mean/SE/N/df,\n",
      "and genuine zero versus missing observation handling.\n")
  if (length(args)) cat("Outputs:", out, "\n")
}
main()
