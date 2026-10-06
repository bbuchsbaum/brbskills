#!/usr/bin/env Rscript
# Synthetic, run-blocked regional decoding example for rMVPA 0.1.3.
# Each row is one beta map; observations in an entire run are held out together.

library(rMVPA)
library(neuroim2)

set.seed(20261006)

# Four runs x 12 beta maps, balanced (6 faces, 6 scenes) within every run.
n_runs <- 4L
trials_per_run <- 12L
n <- n_runs * trials_per_run
dims <- c(3L, 3L, 3L)
run <- rep(seq_len(n_runs), each = trials_per_run)
condition <- factor(rep(rep(c("faces", "scenes"), each = trials_per_run / 2L), n_runs))

# A small regional condition effect: the first eight voxels have a faces > scenes
# mean difference.  Remaining voxels are noise.  This is synthetic signal only.
n_voxels <- prod(dims)
X <- matrix(rnorm(n * n_voxels, sd = 0.8), nrow = n, ncol = n_voxels)
signal_voxels <- seq_len(8L)
X[condition == "faces", signal_voxels] <- X[condition == "faces", signal_voxels] + 0.9
X[condition == "scenes", signal_voxels] <- X[condition == "scenes", signal_voxels] - 0.9

image_space <- NeuroSpace(c(dims, n))
mask_space <- NeuroSpace(dims)
dataset <- mvpa_dataset(
  NeuroVec(array(as.vector(t(X)), c(dims, n)), image_space),
  mask = NeuroVol(array(1L, dims), mask_space)
)
metadata <- data.frame(beta_id = seq_len(n), run = run, condition = condition)
design <- mvpa_design(metadata, y_train = ~ condition, block_var = ~ run)
folds <- blocked_cross_validation(design$block_var)

# This registered model needs the optional sda package.  The fixed tuning grid
# deliberately avoids choosing hyperparameters with held-out outer-fold data.
spec <- mvpa_model(
  load_model("sda_notune"), dataset, design,
  crossval = folds,
  tune_grid = data.frame(lambda = 0.1, diagonal = FALSE),
  return_predictions = TRUE
)

validation <- validate_analysis(spec, verbose = FALSE)
print(validation)

# A positive integer defines one ROI; zero would be background.
roi <- NeuroVol(array(1L, dims), mask_space)
result <- run_regional(spec, roi, backend = "default")

print(result$performance_table)
print(utils::head(result$prediction_table, 12L))

# Save the per-observation ledger so each held-out beta's prediction can be
# inspected, grouped by run, or joined to beta_id/condition downstream.
held_out <- cbind(
  metadata[result$prediction_table$.rownum, c("beta_id", "run", "condition")],
  as.data.frame(result$prediction_table)
)
saveRDS(result, "regional_decoding_result.rds")
utils::write.csv(result$performance_table, "regional_performance.csv", row.names = FALSE)
utils::write.csv(held_out, "held_out_predictions.csv", row.names = FALSE)

# Explicit checks of the estimand and held-out provenance.
stopifnot(nrow(held_out) == n)
stopifnot(setequal(held_out$run, seq_len(n_runs)))
stopifnot(all(table(held_out$run) == trials_per_run))
stopifnot(all(!is.na(result$prediction_table$predicted)))
cat("Held-out prediction rows:", nrow(held_out), "\n")
cat("Output files: regional_decoding_result.rds, regional_performance.csv, held_out_predictions.csv\n")
