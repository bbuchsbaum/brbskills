# From the skill directory: Rscript tests/smoke.R
# Runtime smoke tests, not statistical validation or estimated coverage tests.
source("scripts/model_audit.R")
need_namespace("lme4")
passed <- character()
check <- function(name, expr) { force(expr); passed <<- c(passed, name); cat("PASS:", name, "\n") }
throws <- function(expr) inherits(tryCatch({ force(expr); NULL }, error = identity), "error")

check("invalid model rejected", stopifnot(throws(audit_mermod(1))))
check("capture preserves warning, message, and error", {
  z <- capture_fit({ warning("sentinel-warning"); message("sentinel-message"); stop("sentinel-error") })
  stopifnot(any(grepl("sentinel-warning", z$warnings)),
            any(grepl("sentinel-message", z$messages)), identical(z$error, "sentinel-error"))
})
d <- lme4::sleepstudy
d$id <- sprintf("row-%03d", seq_len(nrow(d)))
m <- lme4::lmer(Reaction ~ Days + (Days | Subject), data = d, REML = TRUE, na.action = na.fail)
check("Gaussian audit records evidence without validity certification", {
  a <- audit_mermod(m)
  stopifnot(a$nobs == nrow(d), isTRUE(a$REML), !a$singular,
            !any(grepl("READY", a$review_flags)))
})
check("disabled derivatives are missing evidence, not a failed optimizer", {
  off <- update(m, control = lme4::lmerControl(calc.derivs = FALSE))
  a <- audit_mermod(off)
  stopifnot(a$optimizer_status == "success",
            a$derivatives$gradient_status == "unavailable",
            a$derivatives$hessian_status == "unavailable",
            "DERIVATIVES_UNAVAILABLE" %in% a$review_flags,
            !"NUMERICAL_UNRESOLVED" %in% a$review_flags,
            a$convergence_check_execution == "not_established_from_saved_object")
})
check("Hessian defects are visible without relying on warning messages", {
  bad <- m
  bad@optinfo$conv$lme4 <- list()
  bad@optinfo$derivs$Hessian <- -diag(length(bad@optinfo$val))
  a <- audit_mermod(bad)
  stopifnot(a$optimizer_status == "success", !a$derivatives$hessian_positive_definite,
            all(c("HESSIAN_REVIEW", "NUMERICAL_UNRESOLVED") %in% a$review_flags))
  bad@optinfo$derivs$Hessian[1, 1] <- NA_real_
  stopifnot(audit_mermod(bad)$derivatives$hessian_status == "nonfinite")
  bad@optinfo$derivs$Hessian <- matrix(1, 2, 3)
  stopifnot(audit_mermod(bad)$derivatives$hessian_status == "malformed")
  bad@optinfo$derivs$gradient[1] <- Inf
  stopifnot(audit_mermod(bad)$derivatives$gradient_status == "nonfinite")
})
check("LMM covariance capture retains the actual RX matrix", {
  v <- capture_vcov(m)
  stopifnot(v$source == "RX", v$finite,
            isTRUE(all.equal(v$covariance, as.matrix(stats::vcov(m)))),
            throws(capture_vcov(m, use.hessian = NA)))
})
check("random slope support counted", {
  s <- within_group_support(d, "Days", "Subject")
  stopifnot(nrow(s) == 18L, all(s$distinct_predictor_values == 10L))
})
check("missing support values require explicit handling", {
  dd <- d; dd$Days[1] <- NA_real_
  stopifnot(throws(within_group_support(dd, "Days", "Subject")))
})
check("REML fixed-effect comparison blocked by default", {
  stopifnot(throws(assert_comparable(m, m, d$id, d$id)))
})
m1 <- update(m, REML = FALSE)
m0 <- update(m1, . ~ . - Days)
check("comparable ML frames pass conservative guard", {
  z <- assert_comparable(m1, m0, d$id, d$id)
  stopifnot(z$checks_passed, length(z$still_required) > 0)
})
check("row identity and ordering mismatch rejected", {
  stopifnot(throws(assert_comparable(m1, m0, d$id, rev(d$id))))
})
check("duplicate IDs rejected", {
  bad <- d$id; bad[2] <- bad[1]
  stopifnot(throws(assert_comparable(m1, m0, bad, bad)))
})
check("rank deficiency distinguished from singular covariance", {
  dd <- d; dd$Days2 <- 2 * dd$Days
  z <- capture_fit(lme4::lmer(Reaction ~ Days + Days2 + (1 | Subject), data = dd))
  stopifnot(is.null(z$error))
  a <- audit_mermod(z$fit, z)
  stopifnot("FIXED_RANK_DEFICIENT" %in% a$review_flags,
            anyNA(a$fixed_effects_including_dropped))
})
check("balanced zero-between-group construction flags singularity", {
  dd <- expand.grid(repeat_id = 1:10, group = factor(1:20))
  dd$x <- rep(seq(-1, 1, length.out = 10), 20)
  dd$y <- 1 + 2 * dd$x + rep(rep(c(-0.4, 0.4), 5), 20)
  z <- capture_fit(lme4::lmer(y ~ x + (1 | group), data = dd))
  stopifnot(is.null(z$error), "SINGULAR_REVIEW" %in% audit_mermod(z$fit)$review_flags)
})
check("centering changes a diagonal covariance constraint", {
  G <- diag(c(4, 1)); center <- 3
  T <- matrix(c(1, 0, center, 1), nrow = 2)
  Gc <- T %*% G %*% t(T)
  stopifnot(Gc[1, 2] == center * G[2, 2])
})
check("logit-normal integration matches zero-variance and symmetry identities", {
  stopifnot(max(abs(logit_normal_mean(c(-2, 0, 2), 0) - plogis(c(-2, 0, 2)))) < 1e-10,
            abs(logit_normal_mean(0, 2) - 0.5) < 1e-7)
})
check("logit-normal integrated mean differs from random effects zero", {
  stopifnot(logit_normal_mean(2, 1) < plogis(2),
            throws(logit_normal_mean(2, -1)), throws(logit_normal_mean(2, c(1, 2))))
})
c <- lme4::cbpp
cg <- capture_fit(lme4::glmer(cbind(incidence, size - incidence) ~ period + (1 | herd),
                             data = c, family = binomial(), nAGQ = 1, na.action = na.fail))
if (!is.null(cg$error)) stop(cg$error)
g <- cg$fit
check("GLMM audit identifies family and quadrature", {
  a <- audit_mermod(g)
  stopifnot(a$family == "binomial", a$link == "logit", a$nAGQ == 1)
})
check("GLMM covariance capture identifies Hessian and explicit RX routes", {
  v <- capture_vcov(g)
  rx <- capture_vcov(g, use.hessian = FALSE)
  stopifnot(v$source == "finite_difference_Hessian", v$finite,
            isTRUE(all.equal(v$covariance, as.matrix(stats::vcov(g)))))
  # lme4 may warn when the two methods differ. Preserve that condition.
  reference <- capture_fit(as.matrix(stats::vcov(g, use.hessian = FALSE)))
  stopifnot(isTRUE(all.equal(rx$covariance, reference$fit)),
            identical(rx$warnings, reference$warnings))
})
check("missing GLMM Hessian retains RX inference provenance without inventing a check", {
  missing <- g; missing@optinfo$derivs <- NULL
  a <- audit_mermod(missing); v <- capture_vcov(missing)
  stopifnot("DERIVATIVES_UNAVAILABLE" %in% a$review_flags,
            v$source == "RX", v$finite, !v$joint_hessian_available,
            isTRUE(all.equal(v$covariance, as.matrix(stats::vcov(missing, use.hessian = FALSE)))))
  forced <- capture_vcov(missing, use.hessian = TRUE)
  stopifnot(forced$source == "unavailable", !is.null(forced$error), is.null(forced$covariance))
})
check("covariance fallback conditions remain visible and provenance unresolved", {
  bad <- g; bad@optinfo$derivs$Hessian <- -diag(length(bad@optinfo$val))
  v <- capture_vcov(bad)
  stopifnot(v$source == "unresolved_after_condition", length(v$warnings) > 0,
            v$finite,
            isTRUE(all.equal(v$covariance, as.matrix(stats::vcov(bad, use.hessian = FALSE)))))
})
check("singular binomial fixture cannot hide missing derivatives behind optimizer success", {
  dd <- data.frame(group = factor(seq_len(12)), events = rep(c(9, 11), 6))
  z <- capture_fit(lme4::glmer(cbind(events, 20-events) ~ 1 + (1 | group),
    data = dd, family = binomial(), control = lme4::glmerControl(
      calc.derivs = TRUE, optimizer = "bobyqa")))
  stopifnot(is.null(z$error))
  a <- audit_mermod(z$fit, z)
  stopifnot(a$singular, a$optimizer_status == "success",
            a$convergence_check_execution == "not_established_from_saved_object")
  # lme4 versions differ: test the evidence returned, not a pinned omission policy.
  if (is.null(z$fit@optinfo$derivs)) {
    stopifnot("DERIVATIVES_UNAVAILABLE" %in% a$review_flags,
              capture_vcov(z$fit)$source == "RX")
  } else stopifnot(a$derivatives$gradient_status == "available")
  boundary <- z$fit
  boundary@optinfo$derivs <- list(gradient = rep(0, length(boundary@optinfo$val)),
                                Hessian = matrix(0, length(boundary@optinfo$val), length(boundary@optinfo$val)))
  b <- audit_mermod(boundary)
  stopifnot("HESSIAN_REVIEW" %in% b$review_flags,
            !"NUMERICAL_UNRESOLVED" %in% b$review_flags)
})
check("inconsistent GLMM quadrature comparison rejected", {
  g9 <- update(g, nAGQ = 9)
  ids <- as.character(seq_len(nrow(c)))
  stopifnot(throws(assert_comparable(g, g9, ids, ids)))
})
if (requireNamespace("DHARMa", quietly = TRUE)) {
  check("installed DHARMa explicit conditional and unconditional modes execute", {
    a <- dharma_mermod(g, "conditional", n = 50L, seed = 12L)
    b <- dharma_mermod(g, "unconditional", n = 50L, seed = 12L)
    stopifnot(a$settings$mode == "conditional", b$settings$mode == "unconditional",
              inherits(a$residuals, "DHARMa"), inherits(b$residuals, "DHARMa"))
  })
} else cat("SKIP: DHARMa optional runtime branch (not installed)\n")
if (identical(Sys.getenv("RUN_SLOW"), "true")) {
  check("small bootstrap execution and diagnostic extraction", {
    z <- lme4::bootMer(m, FUN = lme4::fixef, nsim = 20L, seed = 12L,
                       use.u = FALSE, type = "parametric")
    ba <- bootstrap_audit(z)
    stopifnot(ba$requested == 20L, ba$returned_statistic_rows == 20L)
  })
} else cat("SKIP: bootstrap execution; RUN_SLOW=true enables it. B=20 is ONLY a smoke test.\n")
cat(length(passed), "runtime smoke checks passed. This is NOT agent or inferential validation.\n")
print(sessionInfo())
