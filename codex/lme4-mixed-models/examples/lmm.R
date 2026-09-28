# Run from the skill directory: Rscript examples/lmm.R
# Demonstration on lme4's sleepstudy; NOT a complete scientific reanalysis.
source("scripts/model_audit.R")
for (p in c("lme4", "emmeans", "lmerTest", "pbkrtest")) need_namespace(p)
set.seed(20260925)
out <- "examples/output/lmm"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
d <- lme4::sleepstudy
d$.row_id <- sprintf("sleep-%03d", seq_len(nrow(d)))
d$Days_c <- d$Days - 4.5
stopifnot(!anyNA(d), !anyDuplicated(d$.row_id))
write.csv(within_group_support(d, "Days_c", "Subject"),
          file.path(out, "slope-support.csv"), row.names = FALSE)

fitlog <- capture_fit(lme4::lmer(Reaction ~ Days_c + (1 + Days_c | Subject),
  data = d, REML = TRUE, na.action = na.fail))
saveRDS(fitlog, file.path(out, "fit-and-conditions.rds"))
if (!is.null(fitlog$error)) stop(fitlog$error)
m <- fitlog$fit
a <- audit_mermod(m, fitlog)
dput(a, file = file.path(out, "audit.R"))
# This is an example pause gate, not an assertion that all flags invalidate inference.
if (length(a$review_flags)) stop("Review audit flags before continuing this example.")

mt <- lmerTest::as_lmerModLmerTest(m)
capture.output(summary(mt, ddf = "Satterthwaite"),
               file = file.path(out, "satterthwaite-summary.txt"))
trend <- emmeans::emtrends(m, ~ 1, var = "Days_c", lmer.df = "kenward-roger")
trend_tab <- as.data.frame(summary(trend, infer = c(TRUE, TRUE), adjust = "none"))
write.csv(trend_tab, file.path(out, "planned-days-slope.csv"), row.names = FALSE)
capture.output(trend, file = file.path(out, "trend-method.txt"))

# A fixed-slope null retains the random slope; the tested mean restriction is explicit.
m1 <- update(m, REML = FALSE)
m0 <- update(m1, . ~ . - Days_c)
assert_comparable(m1, m0, row_ids_a = d$.row_id, row_ids_b = d$.row_id)
capture.output(anova(m0, m1, refit = FALSE), file = file.path(out, "ML-LRT-asymptotic.txt"))

png(file.path(out, "observed-trajectories.png"), width = 1000, height = 700)
plot(d$Days, d$Reaction, xlab = "Days of sleep restriction", ylab = "Reaction time (ms)")
for (idx in split(seq_len(nrow(d)), d$Subject)) lines(d$Days[idx], d$Reaction[idx])
dev.off()

png(file.path(out, "conditional-residuals.png"), width = 1000, height = 700)
plot(fitted(m), residuals(m), xlab = "Conditional fitted value", ylab = "Conditional residual")
abline(h = 0, lty = 2)
dev.off()

# Estimated population mean (identity link); NOT a new-observation prediction interval.
em <- emmeans::emmeans(m, ~ Days_c, at = list(Days_c = seq(0, 9) - 4.5),
                        lmer.df = "kenward-roger")
pr <- as.data.frame(confint(em, adjust = "none"))
write.csv(pr, file.path(out, "mean-prediction-data.csv"), row.names = FALSE)
png(file.path(out, "estimated-mean.png"), width = 1000, height = 700)
plot(pr$Days_c + 4.5, pr$emmean, type = "l", ylim = range(pr$lower.CL, pr$upper.CL),
     xlab = "Days of sleep restriction", ylab = "Estimated mean reaction time (ms)")
arrows(pr$Days_c + 4.5, pr$lower.CL, pr$Days_c + 4.5, pr$upper.CL,
       angle = 90, code = 3, length = 0.05)
mtext("Pointwise 95% confidence intervals; requested Kenward-Roger method")
dev.off()
capture.output(sessionInfo(), file = file.path(out, "sessionInfo.txt"))
message("Example artifacts written. Residual/influence/model-sensitivity review is still required.")
