args0 <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args0[grepl("^--file=", args0)]))))
suppressPackageStartupMessages(library(lme4))
path <- "outputs/glmm-quarter-diagonal-primary"
fit <- readRDS(file.path(path,"fit.rds"))
cat("Starting explicit GLMM derivative check at",format(Sys.time()),"\n");flush.console()
start <- proc.time()[3]
dfun <- glmer(formula(fit),data=model.frame(fit),family=binomial(),nAGQ=1,
              start=list(theta=getME(fit,"theta"),fixef=fixef(fit)),devFunOnly=TRUE,
              control=glmerControl(nAGQ0initStep=FALSE))
par <- c(getME(fit,"theta"),fixef(fit))
value <- dfun(par)
stopifnot(abs(value-(-2*as.numeric(logLik(fit))))<1e-5)
# Pinned installed lme4 2.0.1: glmer omits force.calc.derivs when singular,
# whereas lmer forwards it. Recompute its documented finite-difference evidence.
derivs <- getFromNamespace("deriv12","lme4")(dfun,par,fx=value)
saveRDS(derivs,file.path(path,"explicit_derivatives.rds"))
eig <- eigen(derivs$Hessian,symmetric=TRUE,only.values=TRUE)$values
scaled <- tryCatch(as.numeric(solve(chol(derivs$Hessian),derivs$gradient)),error=function(e) conditionMessage(e))
lower <- c(getME(fit,"lower"),rep(-Inf,length(fixef(fit))))
free <- par>lower+1e-4
result <- list(elapsed_seconds=unname(proc.time()[3]-start),objective=value,
               gradient=derivs$gradient,hessian_eigenvalues=eig,scaled_gradient=scaled,
               free_coordinates=free,
               max_abs_free_gradient=max(abs(derivs$gradient[free])),
               max_abs_free_scaled_gradient=if(is.numeric(scaled)) max(abs(scaled[free])) else NULL,
               minimum_boundary_gradient=if(any(!free)) min(derivs$gradient[!free]) else NULL,
               explanation="Boundary SD parameters use one-sided KKT interpretation; a positive derivative at a lower bound is not by itself a violation.")
jsonlite::write_json(result,file.path(path,"explicit_derivatives.json"),pretty=TRUE,auto_unbox=TRUE,digits=12)
cat("Derivative check finished; elapsed",result$elapsed_seconds,"minimum eigenvalue",min(eig),"\n")
print(result[c("max_abs_free_gradient","max_abs_free_scaled_gradient","minimum_boundary_gradient")])
