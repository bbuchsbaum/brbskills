args0 <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args0[grepl("^--file=", args0)]))))
suppressPackageStartupMessages({library(lme4);library(data.table)})
d <- readRDS("outputs/analysis_data.rds")
stopifnot(nrow(d)==133500L,!anyDuplicated(d$row_id),all(d$frequency_source>0))
ct <- fread("outputs/planned_contrasts.csv")
stopifnot(nrow(ct)==12,all(is.finite(ct$estimate)),all(ct$se>0),
          max(abs(ct$p_holm-p.adjust(ct$p,"holm")))<1e-12)
for(oc in c("lmm","glmm")){
  scope<-if(oc=="lmm") "full" else "quarter"
  p<-file.path("outputs",paste(oc,scope,"diagonal-primary",sep="-"))
  fit<-readRDS(file.path(p,"fit.rds")); mf<-model.frame(fit)
  ids<-readLines(file.path(p,"row_ids.txt"))
  stopifnot(identical(ids,rownames(mf)),!anyDuplicated(ids))
  rows<-d[match(ids,d$row_id)]
  stopifnot(!anyNA(rows$row_id),uniqueN(rows$reader)==75L,uniqueN(rows$text)==12L,
            qr(getME(fit,"X"))$rank==24L)
  y<-model.response(mf)
  if(oc=="lmm") stopifnot(nrow(rows)==95683,all(rows$FPF==1),max(abs(y-log(rows$FPRT)))<1e-12,isREML(fit))
  else stopifnot(nrow(rows)==33600,all(rows$pilot_subset),identical(as.numeric(y),as.numeric(rows$FPReg)),
                 getME(fit,"devcomp")$dims["nAGQ"]==1)
  cm<-fread(file.path(p,"contrast_matrix.csv"))
  C<-as.matrix(cm[,names(fixef(fit)),with=FALSE])
  tab<-ct[ct$outcome==oc]
  stopifnot(max(abs(as.numeric(C%*%fixef(fit))-tab$estimate))<1e-12)
  # Independent factorial identities for the two focal between-level contrasts.
  stopifnot(abs(tab$estimate[3]-.5*fixef(fit)["D:L:T"])<1e-12,
            abs(tab$estimate[6]-.5*fixef(fit)["D:L:T:S"])<1e-12)
}
pred<-fread("outputs/response_predictions.csv")
stopifnot(all(is.finite(pred$integrated)),all(is.finite(pred$zero_RE)),
          all(pred$integrated[pred$outcome=="lmm"]>0),
          all(pred$integrated[pred$outcome=="glmm"]>0 & pred$integrated[pred$outcome=="glmm"]<1))
result<-list(artifact_checks="passed",checks=c("row identities and counts","outcome filtering and units",
  "fixed-design rank","REML and Laplace settings","contrast algebra","Holm family","prediction ranges"),
  scientific_status="NUMERICAL_UNRESOLVED; SINGULAR_REVIEW; LMM residual adequacy concerns",
  note="Artifact consistency is not a model-validity or skill-effectiveness certificate.")
jsonlite::write_json(result,"verification.json",pretty=TRUE,auto_unbox=TRUE)
cat("Artifact consistency checks passed; scientific qualification remains unresolved.\n")
