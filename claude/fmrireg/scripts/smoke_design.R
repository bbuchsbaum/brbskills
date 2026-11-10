#!/usr/bin/env Rscript
# Synthetic design checks, not a production model or temporal-noise calibration.
if (any(commandArgs(TRUE) %in% c("--help", "-h"))) {
  cat("Usage: Rscript smoke_design.R\n"); quit(status = 0L)
}
if (!requireNamespace("fmrireg", quietly = TRUE))
  stop("Install/pin fmrireg in the authorized environment first")
suppressPackageStartupMessages(library(fmrireg))

# One synthetic run. Values and timing are fixtures, not analysis defaults.
events <- data.frame(onset = seq(4, by = 12, length.out = 12),
                     duration = rep(c(1, 1.5, 2), 4), run = 1L, main = factor("event"))
score <- c(1, 3, NA, 2, 4, 1, 2, NA, 3, 4, 2, 1)
modulation <- function(score) {
  observed <- is.finite(score)
  available <- sum(observed) >= 2L && length(unique(score[observed])) > 1L
  value <- numeric(length(score))
  if (available) value[observed] <- score[observed] - mean(score[observed])
  list(value = value, missing = as.numeric(!observed), available = available)
}
m <- modulation(score)
stopifnot(m$available, abs(sum(m$value)) < 1e-12,
          all(m$value[is.na(score)] == 0),
          !modulation(rep(NA_real_, 12))$available,
          !modulation(rep(2, 12))$available)
events$mod <- m$value; events$missing <- m$missing
# The example reference is explicit; real data require preprocessing evidence.
sf <- sampling_frame(180L, TR = 1, start_time = .25, precision = .05)
em <- event_model(onset ~ hrf(main) + hrf(mod) + hrf(missing), data = events,
                  block = ~ run, sampling_frame = sf, durations = events$duration,
                  precision = .05, strict = TRUE)
X <- as.matrix(design_matrix(em))
stopifnot(identical(dim(X), c(180L, 3L)), all(is.finite(X)))

# Separately build unit-amplitude trial columns using the same public HRF engine.
# This checks event/amplitude assembly, not the engine's HRF implementation.
trial <- vapply(seq_len(nrow(events)), function(i) {
  one <- event_model(onset ~ hrf(main), data = events[i, ], block = ~ run,
                     sampling_frame = sf, durations = events$duration[i],
                     precision = .05, strict = TRUE)
  z <- as.matrix(design_matrix(one))
  stopifnot(ncol(z) == 1L)
  as.numeric(z)
}, numeric(180))
expected <- trial %*% cbind(1, events$mod, events$missing)
stopifnot(max(abs(X - expected)) < 1e-8)
D <- cbind(intercept = 1, X)
truth <- c(.2, 1.1, -.4, .7)
stopifnot(qr(D)$rank == ncol(D),
          max(abs(qr.coef(qr(D), drop(D %*% truth)) - truth)) < 1e-9)

# Full-rank features do not establish feature-by-ordinal-score support.
set.seed(41)
features <- scale(matrix(rnorm(12 * 4), 12, 4), center = TRUE, scale = FALSE)
rating <- c(rep(2, 10), rep(1, 2)); rating <- rating - mean(rating)
main <- cbind(1, rating, features)
joint <- cbind(main, features * rating)
stopifnot(qr(main)$rank == ncol(main), qr(joint)$rank < ncol(joint))
null <- svd(joint, nv = ncol(joint))$v[, ncol(joint)]
stopifnot(max(abs(joint %*% null)) < 1e-10,
          max(abs((trial %*% joint) %*% null)) < 1e-9)

# Independent continuous HRF calculation for clock/duration/omission examples.
# Integral of a double-gamma kernel makes arbitrary boxcar durations explicit.
times <- seq(0, by = 1, length.out = 180) + .25
box <- function(times, onset, duration, shape = 6) {
  H <- function(t) pgamma(pmax(t, 0), shape) - pgamma(pmax(t, 0), shape + 10) / 6
  h <- function(t) dgamma(pmax(t, 0), shape) - dgamma(pmax(t, 0), shape + 10) / 6
  vapply(seq_along(onset), function(i) {
    dt <- times - onset[i]
    if (duration[i] == 0) h(dt) else H(dt) - H(dt - duration[i])
  }, numeric(length(times)))
}
offset <- .25
stopifnot(max(abs(box(times, events$onset, events$duration) -
                  box(times - offset, events$onset - offset, events$duration))) < 1e-12)
for (shape in c(6, 7)) {
  component <- rowSums(box(times, events$onset, rep(2, 12), shape))
  routine <- rowSums(box(times, events$onset, rep(5, 12), shape))
  adjacent <- rowSums(box(times, events$onset + 2, rep(3, 12), shape))
  response <- rowSums(box(times, events$onset + 3.5, rep(0, 12), shape))
  correct_error <- sum(qr.resid(qr(cbind(1, component)), component)^2)
  routine_error <- sum(qr.resid(qr(cbind(1, routine)), component)^2)
  phase_design <- cbind(1, component, adjacent)
  allocation <- qr.coef(qr(phase_design), response)
  full <- cbind(phase_design, response)
  stopifnot(correct_error < 1e-20, routine_error > 1e-4,
            qr(full)$rank == ncol(full), abs(allocation[3]) > 1e-3,
            max(abs(qr.coef(qr(full), response) - c(0, 0, 0, 1))) < 1e-9)
  cat(sprintf("HRF shape %g: routine SSE %.6f; omitted response -> adjacent coefficient %.6f\n",
              shape, routine_error, allocation[3]))
}
cat("PASS: public design assembly, coefficient recovery, support, timing and omitted-signal checks\n")
