# lme4-mixed-models v0.1.0-candidate
# Evidence-gathering utilities, NOT an automatic analysis or selection procedure.
# See ../references/sources.md: LMM, CONV, SING, SIM, DHARMA, BOOT.
# No package installation, global options changes, or automatic optimizer loops.

need_namespace <- function(package) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop(sprintf("Package '%s' is required; install it explicitly in your analysis environment.",
                 package), call. = FALSE)
  }
  invisible(TRUE)
}

need_mermod <- function(fit) {
  need_namespace("lme4")
  if (!inherits(fit, "merMod")) stop("Expected an lme4 merMod fit.", call. = FALSE)
  invisible(TRUE)
}

# Capture conditions in a return object. They are retained, not discarded.
# Caller MUST save/review warnings and messages, including when fitting fails.
capture_fit <- function(expr) {
  code <- substitute(expr)
  env <- parent.frame()
  warnings <- messages <- character()
  error <- NULL
  fit <- tryCatch(
    withCallingHandlers(eval(code, envir = env),
      warning = function(w) {
        warnings <<- c(warnings, conditionMessage(w))
        invokeRestart("muffleWarning")
      },
      message = function(m) {
        messages <<- c(messages, conditionMessage(m))
        invokeRestart("muffleMessage")
      }),
    error = function(e) { error <<- conditionMessage(e); NULL })
  list(fit = fit, warnings = warnings, messages = messages, error = error,
       expression = paste(deparse(code), collapse = " "))
}

# Capture the covariance actually supplied to downstream Wald inference. This
# calls vcov, not a derivative calculation or refit. Warnings remain reviewable;
# do not guess a fallback method from version-dependent/localized warning text.
capture_vcov <- function(fit, use.hessian = NULL) {
  need_mermod(fit)
  if (!is.null(use.hessian) &&
      (!is.logical(use.hessian) || length(use.hessian) != 1L || is.na(use.hessian))) {
    stop("use.hessian must be NULL, TRUE, or FALSE.", call. = FALSE)
  }
  h <- methods::slot(fit, "optinfo")$derivs$Hessian
  ntheta <- length(lme4::getME(fit, "theta"))
  joint_hessian <- is.matrix(h) && nrow(h) == ncol(h) && nrow(h) > ntheta
  z <- capture_fit(stats::vcov(fit, use.hessian = use.hessian))
  requested <- if (is.null(use.hessian)) "package_default" else
    if (use.hessian) "finite_difference_Hessian" else "RX"
  method <- if (!is.null(z$error)) "unavailable" else
    if (length(z$warnings) || length(z$messages)) "unresolved_after_condition" else
    if (isTRUE(use.hessian) || (is.null(use.hessian) && joint_hessian))
      "finite_difference_Hessian" else "RX"
  v <- if (is.null(z$fit)) NULL else as.matrix(z$fit)
  finite <- !is.null(v) && all(is.finite(v))
  list(covariance = v, requested = requested, source = method,
       joint_hessian_available = joint_hessian, finite = finite,
       warnings = z$warnings, messages = z$messages, error = z$error,
       lme4_version = as.character(utils::packageVersion("lme4")),
       interpretation = paste("Source follows lme4's documented vcov selection; inspect on upgrades.",
         "Any condition leaves source unresolved; inspect fallback messages before reporting.",
         "RX is approximate for GLMMs. Neither covariance source certifies inferential validity."))
}

# Evidence only: no output state means 'statistically valid'. No derivatives are
# recomputed. Saved derivatives do not prove which package checks were executed.
audit_mermod <- function(fit, captured = NULL, singular_tol = 1e-4) {
  need_mermod(fit)
  if (length(singular_tol) != 1L || !is.finite(singular_tol) || singular_tol <= 0) {
    stop("singular_tol must be a positive finite scalar.", call. = FALSE)
  }
  X <- lme4::getME(fit, "X")
  dropped <- attr(X, "col.dropped")
  flist <- lme4::getME(fit, "flist")
  opt <- methods::slot(fit, "optinfo") # lme4 internal structure; inspect on upgrades
  opt_code <- unlist(opt$conv$opt, use.names = FALSE)
  conv_messages <- as.character(unlist(opt$conv$lme4$messages, use.names = FALSE))
  singular_messages <- grepl("boundary.*singular", conv_messages, ignore.case = TRUE)
  numerical_messages <- conv_messages[!singular_messages]
  singular <- lme4::isSingular(fit, tol = singular_tol)
  grad <- opt$derivs$gradient
  hess <- opt$derivs$Hessian
  nopt <- length(opt$val)
  gradient_status <- if (is.null(grad)) "unavailable" else
    if (!is.numeric(grad) || !length(grad) || (nopt && length(grad) != nopt)) "malformed" else
    if (any(!is.finite(grad))) "nonfinite" else "available"
  hessian_status <- if (is.null(hess)) "unavailable" else
    if (!is.matrix(hess) || !is.numeric(hess) || !nrow(hess) || nrow(hess) != ncol(hess) ||
        (nopt && nrow(hess) != nopt)) "malformed" else
    if (any(!is.finite(hess))) "nonfinite" else
    if (!isSymmetric(unname(hess))) "asymmetric" else "available"
  hessian_eigenvalues <- if (hessian_status == "available")
    eigen(hess, symmetric = TRUE, only.values = TRUE)$values else NULL
  hessian_pd <- if (hessian_status == "available")
    !inherits(tryCatch(chol(hess), error = identity), "error") else NA
  pca <- tryCatch(lme4::rePCA(fit), error = function(e) e)
  dims <- lme4::getME(fit, "devcomp")$dims
  nAGQ <- if ("nAGQ" %in% names(dims)) unname(dims["nAGQ"]) else NA_integer_
  flags <- character()
  if (length(dropped)) flags <- c(flags, "FIXED_RANK_DEFICIENT")
  if (singular) flags <- c(flags, "SINGULAR_REVIEW")
  if (gradient_status == "unavailable" || hessian_status == "unavailable") {
    flags <- c(flags, "DERIVATIVES_UNAVAILABLE")
  }
  if (gradient_status %in% c("malformed", "nonfinite") ||
      hessian_status %in% c("malformed", "nonfinite", "asymmetric")) {
    flags <- c(flags, "NUMERICAL_UNRESOLVED")
  }
  if (identical(hessian_pd, FALSE)) {
    flags <- c(flags, "HESSIAN_REVIEW")
    # An unconstrained positive-definite Hessian is not a universal boundary criterion.
    if (!singular) flags <- c(flags, "NUMERICAL_UNRESOLVED")
  }
  if (length(numerical_messages) || anyNA(opt_code) ||
      (length(opt_code) && any(opt_code != 0))) {
    flags <- c(flags, "NUMERICAL_UNRESOLVED")
  }
  if (!is.finite(as.numeric(stats::logLik(fit)))) {
    flags <- c(flags, "NUMERICAL_UNRESOLVED")
  }
  if (!length(opt_code)) flags <- c(flags, "OPTIMIZER_STATUS_UNKNOWN")
  if (!is.null(captured) &&
      (length(captured$warnings) || length(captured$messages) || !is.null(captured$error))) {
    flags <- c(flags, "CAPTURED_CONDITIONS_REVIEW")
  }
  if (inherits(pca, "error")) flags <- c(flags, "REPCA_UNAVAILABLE")
  group_sizes <- lapply(flist, function(g) {
    n <- as.integer(table(g))
    list(groups = length(n), min = min(n), median = stats::median(n), max = max(n))
  })
  list(
    schema_version = "0.2.0", lme4_version = as.character(utils::packageVersion("lme4")),
    model_call = paste(deparse(stats::getCall(fit)), collapse = " "),
    formula = paste(deparse(stats::formula(fit)), collapse = " "),
    family = stats::family(fit)$family, link = stats::family(fit)$link,
    nobs = stats::nobs(fit), group_sizes = group_sizes,
    REML = lme4::isREML(fit), nAGQ = nAGQ,
    logLik = as.numeric(stats::logLik(fit)),
    fixed_effects_including_dropped = lme4::fixef(fit, add.dropped = TRUE),
    fixed_X_columns_retained = ncol(X), fixed_X_dropped = dropped,
    varcorr = as.data.frame(lme4::VarCorr(fit)),
    singular = singular, singular_tol = singular_tol,
    rePCA = if (inherits(pca, "error")) conditionMessage(pca) else
      lapply(pca, function(z) list(sdev = z$sdev, rotation = z$rotation)),
    optimizer = opt$optimizer, optimizer_code = opt_code,
    optimizer_status = if (!length(opt_code) || anyNA(opt_code)) "unknown" else
      if (all(opt_code == 0)) "success" else "failure",
    convergence_messages = conv_messages,
    convergence_check_execution = "not_established_from_saved_object",
    derivatives = list(gradient_status = gradient_status, hessian_status = hessian_status,
      optimizer_parameter_count = nopt, hessian_eigenvalues = hessian_eigenvalues,
      hessian_positive_definite = hessian_pd),
    raw_max_abs_gradient = if (gradient_status == "available") max(abs(grad)) else NA_real_,
    captured_conditions = if (is.null(captured)) NULL else captured[c("warnings", "messages", "error")],
    review_flags = unique(flags),
    interpretation = paste("Evidence only. Gradient is raw, not a scaled convergence statistic.",
      "Unavailable derivatives are missing evidence, not a demonstrated optimization failure.",
      "Derivative presence and absent warnings do not establish that convergence checks ran.",
      "No assessment of residual adequacy, identifiability of the scientific estimand,",
      "selection bias, missingness, or inferential validity is certified."))
}

# Simple design-support summary: it cannot prove full random-design rank.
within_group_support <- function(data, predictor, group) {
  if (!is.data.frame(data) || !all(c(predictor, group) %in% names(data))) {
    stop("Supply a data.frame and existing predictor/group column names.", call. = FALSE)
  }
  if (anyNA(data[[predictor]]) || anyNA(data[[group]])) {
    stop("Resolve missingness explicitly before assessing support.", call. = FALSE)
  }
  parts <- split(data[[predictor]], data[[group]], drop = TRUE)
  if (!length(parts)) stop("No observed groups.", call. = FALSE)
  data.frame(group = names(parts), n = lengths(parts),
             distinct_predictor_values = vapply(parts, function(x) length(unique(x)), integer(1)),
             row.names = NULL, stringsAsFactors = FALSE)
}

# Conservative guard, not a proof of model nesting or data provenance.
# Supply immutable IDs IN THE EXACT ORDER of each fitted model's observations.
assert_comparable <- function(a, b, row_ids_a, row_ids_b, require_ml = TRUE) {
  need_mermod(a); need_mermod(b)
  fa <- stats::model.frame(a); fb <- stats::model.frame(b)
  valid_ids <- function(ids, n) length(ids) == n && !anyNA(ids) && !anyDuplicated(ids)
  if (!valid_ids(row_ids_a, nrow(fa)) || !valid_ids(row_ids_b, nrow(fb))) {
    stop("Supply complete, unique, correctly ordered immutable IDs for both fits.", call. = FALSE)
  }
  if (!identical(as.character(row_ids_a), as.character(row_ids_b))) {
    stop("Different analyzed rows or order: comparison blocked.", call. = FALSE)
  }
  same <- function(x, y) isTRUE(all.equal(x, y, check.attributes = TRUE, tolerance = 0))
  if (!same(stats::model.response(fa), stats::model.response(fb))) {
    stop("Different analyzed responses: comparison blocked.", call. = FALSE)
  }
  common <- intersect(names(fa), names(fb))
  if (!all(vapply(common, function(nm) same(fa[[nm]], fb[[nm]]), logical(1)))) {
    stop("Shared model-frame columns/coding differ: comparison blocked.", call. = FALSE)
  }
  get_w <- function(f) { w <- stats::model.weights(f); if (is.null(w)) rep(1, nrow(f)) else w }
  get_o <- function(f) { o <- stats::model.offset(f); if (is.null(o)) rep(0, nrow(f)) else o }
  if (!same(get_w(fa), get_w(fb)) || !same(get_o(fa), get_o(fb))) {
    stop("Weights or offsets differ: comparison blocked.", call. = FALSE)
  }
  fam_a <- stats::family(a); fam_b <- stats::family(b)
  if (!identical(fam_a$family, fam_b$family) || !identical(fam_a$link, fam_b$link)) {
    stop("Families or links differ: manual comparison review required.", call. = FALSE)
  }
  if (!identical(lme4::isREML(a), lme4::isREML(b))) {
    stop("ML/REML modes differ.", call. = FALSE)
  }
  if (isTRUE(require_ml) && (lme4::isREML(a) || lme4::isREML(b))) {
    stop("This comparison requires explicit ML fits.", call. = FALSE)
  }
  qa <- lme4::getME(a, "devcomp")$dims["nAGQ"]
  qb <- lme4::getME(b, "devcomp")$dims["nAGQ"]
  if (!same(qa, qb)) stop("GLMM approximation settings differ.", call. = FALSE)
  invisible(list(checks_passed = TRUE,
    still_required = c("Verify model-space nesting for an LRT.",
      "Verify response transformation/likelihood comparability and ID provenance.",
      "Choose a calibrated reference distribution, especially at boundaries.",
      "When require_ml=FALSE, separately verify REML comparability.")))
}

# Version-aware simulation-residual call for lme4 fits only. Does not refit.
dharma_mermod <- function(fit, mode = c("conditional", "unconditional"),
                          n = 1000L, seed = 20260925L) {
  need_mermod(fit); need_namespace("DHARMa")
  mode <- match.arg(mode)
  if (length(n) != 1L || !is.finite(n) || n < 2 || n > .Machine$integer.max || n != floor(n)) {
    stop("n must be an integer >= 2.", call. = FALSE)
  }
  if (length(seed) != 1L || !is.finite(seed) || seed < 0 || seed > .Machine$integer.max || seed != floor(seed)) {
    stop("Supply a valid nonnegative integer seed.", call. = FALSE)
  }
  args <- list(fittedModel = fit, n = as.integer(n), seed = as.integer(seed), refit = FALSE)
  fml <- names(formals(DHARMa::simulateResiduals))
  if ("simulateREs" %in% fml) {
    args$simulateREs <- mode
    api <- "simulateREs"
  } else {
    if (!("..." %in% fml)) stop("Unrecognized DHARMa API; inspect installed help.", call. = FALSE)
    # Preserve an explicit NULL list member; args$re.form <- NULL would delete it.
    args["re.form"] <- list(if (mode == "conditional") NULL else NA)
    api <- "legacy re.form forwarding"
  }
  out <- do.call(DHARMa::simulateResiduals, args)
  list(residuals = out, settings = list(mode = mode, n = as.integer(n), seed = as.integer(seed),
    refit = FALSE, api = api, DHARMa_version = as.character(utils::packageVersion("DHARMa")),
    lme4_version = as.character(utils::packageVersion("lme4"))))
}

bootstrap_audit <- function(x) {
  if (!inherits(x, "boot") || is.null(x$t)) stop("Expected a boot/bootMer result.", call. = FALSE)
  bad <- apply(as.matrix(x$t), 1L, function(z) any(!is.finite(z)))
  list(requested = x$R, returned_statistic_rows = nrow(x$t),
       rows_with_nonfinite_statistics = sum(bad), nonfinite_rows = which(bad),
       bootFail = attr(x, "bootFail"),
       boot_fail_messages = attr(x, "boot.fail.msgs"),
       boot_all_messages = attr(x, "boot.all.msgs"),
       note = "Counts can overlap. Inspect messages; expected singularity is not automatically refit failure.")
}

# Derived integral for a Gaussian linear random contribution of supplied variance.
# Not an automatic G extractor, population standardization, or uncertainty method.
logit_normal_mean <- function(eta, random_variance, rel.tol = 1e-8) {
  if (!is.numeric(eta) || !length(eta) || any(!is.finite(eta))) {
    stop("eta must be a nonempty finite numeric vector.", call. = FALSE)
  }
  if (!is.numeric(random_variance) || !length(random_variance) ||
      any(!is.finite(random_variance)) || any(random_variance < 0) ||
      !(length(random_variance) %in% c(1L, length(eta)))) {
    stop("random_variance must be nonnegative, scalar or the length of eta.", call. = FALSE)
  }
  if (length(rel.tol) != 1L || !is.finite(rel.tol) || rel.tol <= 0) {
    stop("rel.tol must be positive and finite.", call. = FALSE)
  }
  vv <- rep(random_variance, length.out = length(eta))
  vapply(seq_along(eta), function(i) {
    if (vv[i] == 0) return(stats::plogis(eta[i]))
    stats::integrate(function(u) stats::plogis(eta[i] + sqrt(vv[i]) * u) * stats::dnorm(u),
                     lower = -Inf, upper = Inf, rel.tol = rel.tol)$value
  }, numeric(1))
}
