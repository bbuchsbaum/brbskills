args0 <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args0[grepl("^--file=", args0)]))))
suppressPackageStartupMessages({library(lme4);library(data.table)})
primary <- fread("outputs/planned_contrasts.csv")
paths <- list.files("outputs",pattern="^(lmm|glmm)-(full|quarter)-",full.names=TRUE)
results <- list()
for(path in paths){
  f <- file.path(path,"fit.rds")
  if(!file.exists(f)) next
  parts <- strsplit(basename(path),"-")[[1]]
  oc <- parts[1]; scope <- parts[2]; covariance <- parts[3]; variant <- parts[4]
  p <- primary[primary$outcome==oc]
  if(covariance=="diagonal" && variant=="primary") next
  fit <- readRDS(f)
  cm <- fread(file.path("outputs",paste(oc,p$scope[1],"diagonal-primary",sep="-"),"contrast_matrix.csv"))
  C <- as.matrix(cm[,names(fixef(fit)),with=FALSE])
  est <- as.numeric(C%*%fixef(fit))
  se <- sqrt(diag(C%*%as.matrix(vcov(fit))%*%t(C)))
  audit <- jsonlite::read_json(file.path(path,"audit.json"),simplifyVector=TRUE)
  if(scope!=p$scope[1]){
    baseline<-readRDS(file.path("outputs",paste(oc,scope,"diagonal-primary",sep="-"),"fit.rds"))
    p$estimate<-as.numeric(C%*%fixef(baseline))
    p$se<-sqrt(diag(C%*%as.matrix(vcov(baseline))%*%t(C)))
  }
  same_rows<-identical(readLines(file.path(path,"row_ids.txt")),readLines(file.path("outputs",paste(oc,scope,"diagonal-primary",sep="-"),"row_ids.txt")))
  if(variant!="fixated") stopifnot(same_rows)
  results[[basename(path)]]<-data.table(model=basename(path),reference_model=paste(oc,scope,"diagonal-primary",sep="-"),outcome=oc,contrast=cm$contrast,
                estimate=est,se=se,primary_estimate=p$estimate,
                shift_in_primary_SE=(est-p$estimate)/p$se,singular=isSingular(fit),
                same_rows=same_rows,optimizer_code=audit$optimizer_code,
                numerical_messages=paste(audit$convergence_messages,collapse="; "))
}
if(length(results)){
  r<-rbindlist(results)
  fwrite(r,"outputs/sensitivity_contrasts.csv")
  print(r[,.(model,contrast,estimate,shift_in_primary_SE,singular,same_rows)])
}else cat("No eligible completed sensitivity fits.\n")
