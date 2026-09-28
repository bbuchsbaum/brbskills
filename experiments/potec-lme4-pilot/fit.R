args0 <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args0[grepl("^--file=", args0)]))))
args <- commandArgs(TRUE)
stopifnot(length(args)>=3L)
outcome <- args[1]; scope <- args[2]; covariance <- args[3]
variant <- if(length(args)>=4L) args[4] else "primary"
stopifnot(outcome %in% c("lmm","glmm"),scope %in% c("quarter","full"),
          covariance %in% c("diagonal","correlated"),variant %in% c("primary","fixated","strict","alternate"))
suppressPackageStartupMessages({library(lme4);library(data.table)})
source("../../skills/lme4-mixed-models/scripts/model_audit.R")
d <- readRDS("outputs/analysis_data.rds")
if(scope=="quarter") d <- d[pilot_subset==TRUE]
if(outcome=="lmm" || variant=="fixated") d <- d[FPF==1]
d <- droplevels(as.data.frame(d))
rownames(d) <- d$row_id
op <- if(covariance=="correlated") "|" else "||"
random <- paste0("(1+T+S+TS+W+F",op,"reader)+(1+D+L+DL",op,"item)+",
                 "(1+D+L+DL||text)+(1|reader_text)")
formula <- as.formula(paste(if(outcome=="lmm") "log_FPRT" else "FPReg", "~ D*L*T*S + (D*T)*(F+W) +",random))
name <- paste(outcome,scope,covariance,variant,sep="-")
path <- file.path("outputs",name)
dir.create(path,showWarnings=FALSE)
writeLines(d$row_id,file.path(path,"row_ids.txt"))
writeLines(paste(deparse(formula),collapse=" "),file.path(path,"formula.txt"))
writeLines(capture.output(sessionInfo()),file.path(path,"sessionInfo.txt"))
cat("Starting",name,"at",format(Sys.time()),"rows",nrow(d),"\n"); flush.console()
start <- proc.time()[3]
control <- if(outcome=="lmm") lmerControl(calc.derivs=TRUE,check.rankX="stop.deficient") else
  glmerControl(calc.derivs=TRUE,check.rankX="stop.deficient",optimizer="bobyqa",optCtrl=list(maxfun=30000))
if(variant=="strict") control <- if(outcome=="lmm")
  lmerControl(calc.derivs=TRUE,check.rankX="stop.deficient",optCtrl=list(xtol_abs=1e-8,ftol_abs=1e-8,maxeval=10000)) else
  glmerControl(calc.derivs=TRUE,check.rankX="stop.deficient",optimizer="bobyqa",optCtrl=list(maxfun=100000,rhoend=1e-8))
if(variant=="alternate") control <- if(outcome=="lmm")
  lmerControl(calc.derivs=TRUE,check.rankX="stop.deficient",optimizer="bobyqa",optCtrl=list(maxfun=30000)) else
  glmerControl(calc.derivs=TRUE,check.rankX="stop.deficient",optimizer="nloptwrap",optCtrl=list(maxeval=10000))
initial <- NULL
if(variant %in% c("strict","alternate")){
  prior <- readRDS(file.path("outputs",paste(outcome,scope,covariance,"primary",sep="-"),"fit.rds"))
  initial <- if(outcome=="lmm") getME(prior,"theta") else list(theta=getME(prior,"theta"),fixef=fixef(prior))
}
captured <- capture_fit(if(outcome=="lmm") lmer(formula,data=d,REML=TRUE,control=control,na.action=na.fail,start=initial)
                        else glmer(formula,data=d,family=binomial(),nAGQ=1,control=control,na.action=na.fail,start=initial))
elapsed <- unname(proc.time()[3]-start)
saveRDS(captured,file.path(path,"captured.rds"))
jsonlite::write_json(list(elapsed_seconds=elapsed,warnings=captured$warnings,messages=captured$messages,error=captured$error),
                     file.path(path,"conditions.json"),pretty=TRUE,auto_unbox=TRUE,null="null")
if(is.null(captured$fit)) stop(captured$error)
fit <- captured$fit
saveRDS(fit,file.path(path,"fit.rds"))
audit <- audit_mermod(fit,captured)
# Independently inspect derivative availability and scaled gradient/Hessian.
derivs <- fit@optinfo$derivs
audit$derivatives_available <- !is.null(derivs$gradient) && !is.null(derivs$Hessian)
if(audit$derivatives_available){
  audit$hessian_eigenvalues <- eigen(derivs$Hessian,symmetric=TRUE,only.values=TRUE)$values
  audit$scaled_gradient <- tryCatch(as.numeric(solve(chol(derivs$Hessian),derivs$gradient)),error=function(e) conditionMessage(e))
}
audit$elapsed_seconds <- elapsed
jsonlite::write_json(audit,file.path(path,"audit.json"),pretty=TRUE,auto_unbox=TRUE,null="null",digits=12)
fwrite(as.data.table(as.data.frame(VarCorr(fit))),file.path(path,"variance_components.csv"))
cat("Completed",name,"elapsed",elapsed,"logLik",as.numeric(logLik(fit)),"singular",isSingular(fit),"\n")
print(captured[c("warnings","messages","error")])
cat("Review flags:",paste(audit$review_flags,collapse=", "),"\n")
