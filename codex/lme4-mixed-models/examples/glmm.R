# Run from the skill directory: Rscript examples/glmm.R
# cbpp demonstration, not a causal or fully validated reanalysis.
source("scripts/model_audit.R")
for (p in c("lme4", "emmeans")) need_namespace(p)
out <- "examples/output/glmm"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
d <- lme4::cbpp
d$.row_id <- sprintf("cbpp-%03d", seq_len(nrow(d)))
stopifnot(!anyNA(d), all(d$size > 0), all(d$incidence >= 0), all(d$incidence <= d$size))
stopifnot(identical(levels(d$period), as.character(1:4)))
log <- capture_fit(lme4::glmer(cbind(incidence, size - incidence) ~ period + (1 | herd),
  data = d, family = binomial(link = "logit"), nAGQ = 1, na.action = na.fail))
saveRDS(log, file.path(out, "fit-and-conditions.rds"))
if (!is.null(log$error)) stop(log$error)
g <- log$fit
a <- audit_mermod(g, log)
dput(a, file = file.path(out, "audit.R"))
if (length(a$review_flags)) stop("Review audit flags before continuing this example.")

# Single scalar random intercept permits quadrature sensitivity in documented lme4.
g9 <- update(g, nAGQ = 9)
# Compare estimates; do NOT treat AIC differences across nAGQ modes as a model test.
write.csv(data.frame(term = names(lme4::fixef(g)), Laplace = lme4::fixef(g),
                     nAGQ9 = lme4::fixef(g9)), file.path(out, "quadrature-sensitivity.csv"), row.names = FALSE)
dput(audit_mermod(g9), file = file.path(out, "quadrature-audit.R"))

# Prespecified family: period 2, 3, 4 against period 1.
v <- capture_vcov(g)
saveRDS(v, file.path(out, "covariance-and-conditions.rds"))
if (!v$finite || v$source %in% c("unavailable", "unresolved_after_condition"))
  stop("Review covariance evidence before continuing this example.")
e <- emmeans::emmeans(g, ~ period, vcov. = v$covariance)
cm <- list("2 / 1" = c(-1, 1, 0, 0), "3 / 1" = c(-1, 0, 1, 0), "4 / 1" = c(-1, 0, 0, 1))
lor <- emmeans::contrast(e, cm)
write.csv(as.data.frame(summary(lor, type = "response", infer = c(TRUE, TRUE), adjust = "holm")),
          file.path(out, "odds-ratios.csv"), row.names = FALSE)
response_e <- emmeans::regrid(e, transform = "response")
rd <- emmeans::contrast(response_e, setNames(cm, c("2 - 1", "3 - 1", "4 - 1")))
write.csv(as.data.frame(summary(rd, infer = c(TRUE, TRUE), adjust = "holm")),
          file.path(out, "risk-differences-at-zero-RE.csv"), row.names = FALSE)
# Inspect the actual CI adjustment; Holm is a p-value adjustment, not a generic simultaneous-CI method.
capture.output(summary(rd, infer = c(TRUE, TRUE), adjust = "holm"),
               file = file.path(out, "contrast-method-details.txt"))

# Correct only for this simple random-intercept model: estimated Var(b_herd).
nd <- data.frame(period = factor(1:4, levels = levels(d$period)))
eta <- predict(g, newdata = nd, re.form = NA, type = "link")
v <- as.numeric(lme4::VarCorr(g)$herd[1, 1])
pred <- data.frame(period = nd$period, at_random_effect_zero = plogis(eta),
                   integrated_new_herd_mean = logit_normal_mean(eta, v))
write.csv(pred, file.path(out, "two-distinct-prediction-targets.csv"), row.names = FALSE)
png(file.path(out, "prediction-targets.png"), width = 1000, height = 700)
matplot(1:4, as.matrix(pred[-1]), type = "b", lty = c(1, 2), pch = c(1, 2),
        xlab = "Period", ylab = "Estimated probability", ylim = c(0, 1))
legend("topright", legend = c("Random effects zero", "Integrated over new herds"),
       lty = c(1, 2), pch = c(1, 2))
mtext("Plug-in means only; no uncertainty intervals included")
dev.off()

if (requireNamespace("DHARMa", quietly = TRUE)) {
  dg <- dharma_mermod(g, mode = "conditional", n = 1000L, seed = 20260925L)
  saveRDS(dg, file.path(out, "DHARMa-conditional.rds"))
  png(file.path(out, "DHARMa.png"), width = 1100, height = 700)
  plot(dg$residuals)
  dev.off()
  capture.output(DHARMa::testDispersion(dg$residuals, plot = FALSE),
                 file = file.path(out, "dispersion-diagnostic.txt"))
} else {
  writeLines("DHARMa not installed: simulation residuals NOT RUN.",
             file.path(out, "diagnostic-NOT-RUN.txt"))
}
capture.output(sessionInfo(), file = file.path(out, "sessionInfo.txt"))
message("Example artifacts written; significance/model adequacy are not automatically certified.")
