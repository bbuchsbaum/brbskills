args0 <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args0[grepl("^--file=", args0)]))))
args <- commandArgs(TRUE)
scopes <- list(lmm=if(length(args)) args[1] else "quarter",
               glmm=if(length(args)>=2) args[2] else if(length(args)) args[1] else "quarter")
suppressPackageStartupMessages({library(lme4);library(data.table);library(ggplot2)})
source("../../skills/lme4-mixed-models/scripts/model_audit.R")
dir.create("outputs/figures",showWarnings=FALSE)
data <- readRDS("outputs/analysis_data.rds")
theme_set(theme_minimal(base_size=12)+theme(panel.grid.minor=element_blank(),plot.title.position="plot"))
palette <- c(own="#007A87",other="#B65332")

grid_x <- function(fit,g){
  g$DL <- g$D*g$L; g$TS <- g$T*g$S
  model.matrix(delete.response(terms(reformulas::nobars(formula(fit)))),g)[,names(fixef(fit)),drop=FALSE]
}
new_variance <- function(fit,g){
  g$DL <- g$D*g$L; g$TS <- g$T*g$S
  result <- numeric(nrow(g))
  for(G in VarCorr(fit)){
    Z <- do.call(cbind,lapply(colnames(G),function(nm) if(nm=="(Intercept)") rep(1,nrow(g)) else g[[nm]]))
    result <- result+rowSums((Z %*% as.matrix(G))*Z)
  }
  result
}
integrated_probability <- function(eta,v,n=40L){
  gh <- statmod::gauss.quad.prob(n,dist="normal")
  as.numeric(plogis(outer(sqrt(v),gh$nodes)+eta) %*% gh$weights)
}
base_grid <- expand.grid(D=c(-.5,.5),L=c(-.5,.5),T=c(-.5,.5),S=0,F=0,W=0)
contrast_matrix <- function(fit){
  X <- grid_x(fit,base_grid)
  g1 <- base_grid; g1$S <- 1
  slopeX <- grid_x(fit,g1)-X
  at_level <- function(X,l) colSums(X*(ifelse(base_grid$D==base_grid$T,.5,-.5)*(base_grid$L==l)))
  u <- at_level(X,-.5); g <- at_level(X,.5)
  su <- at_level(slopeX,-.5); sg <- at_level(slopeX,.5)
  C <- rbind(u,g,g-u,su,sg,sg-su)
  # Independent factorial-algebra check for +/-0.5 coding.
  expected <- matrix(0,nrow=6,ncol=ncol(C),dimnames=list(NULL,colnames(C)))
  expected[1:2,"D:T"] <- .5
  expected[1:3,"D:L:T"] <- c(-.25,.25,.5)
  expected[4:5,"D:T:S"] <- .5
  expected[4:6,"D:L:T:S"] <- c(-.25,.25,.5)
  stopifnot(max(abs(C-expected))<1e-12)
  rownames(C)<-c("Own - other: undergraduate","Own - other: graduate","Domain match: graduate - undergraduate",
                "Surprisal slope, own - other: undergraduate","Surprisal slope, own - other: graduate",
                "Surprisal domain match: graduate - undergraduate")
  C
}
fits <- list(); all_contrasts <- list(); all_predictions <- list(); diag_summaries <- list()
for(outcome in c("lmm","glmm")){
  scope <- scopes[[outcome]]
  path <- file.path("outputs",paste(outcome,scope,"diagonal-primary",sep="-"))
  fit <- readRDS(file.path(path,"fit.rds")); fits[[outcome]]<-fit
  if(outcome=="glmm" && file.exists(file.path(path,"explicit_derivatives.rds"))){
    fit@optinfo$derivs <- readRDS(file.path(path,"explicit_derivatives.rds"))
    stopifnot(min(eigen(fit@optinfo$derivs$Hessian,symmetric=TRUE,only.values=TRUE)$values)>0)
    saveRDS(fit,file.path(path,"fit_derivative_checked.rds"))
  }
  C <- contrast_matrix(fit)
  fwrite(data.table(contrast=rownames(C),as.data.table(C)),file.path(path,"contrast_matrix.csv"))
  if(outcome=="lmm"){
    cat("Computing Satterthwaite derivatives",scope,"\n"); flush.console()
    # The serialized fit call names the original local formula/data/control.
    # Rebind the exact stored model frame when reconstructing its deviance.
    cache <- file.path(path,"fit_satterthwaite.rds")
    ft <- if(file.exists(cache)) readRDS(cache) else local({
      d <- model.frame(fit)
      formula <- formula(fit)
      control <- lmerControl(calc.derivs=TRUE,check.rankX="stop.deficient")
      initial <- getME(fit,"theta")
      lmerTest::as_lmerModLmerTest(fit)
    })
    stopifnot(identical(fixef(ft),fixef(fit)),identical(getME(ft,"theta"),getME(fit,"theta")))
    saveRDS(ft,file.path(path,"fit_satterthwaite.rds"))
    ct <- rbindlist(lapply(seq_len(nrow(C)),function(i){
      x<-lmerTest::contest1D(ft,C[i,],confint=TRUE)
      data.table(contrast=rownames(C)[i],estimate=x$Estimate,se=x$`Std. Error`,df=x$df,
                 lower=x$lower,upper=x$upper,p=x$`Pr(>|t|)`,method="Satterthwaite t")
    }))
  } else {
    est<-as.numeric(C%*%fixef(fit)); se<-sqrt(diag(C%*%as.matrix(vcov(fit))%*%t(C)))
    ct<-data.table(contrast=rownames(C),estimate=est,se=se,df=Inf,
                   lower=est-qnorm(.975)*se,upper=est+qnorm(.975)*se,
                   p=2*pnorm(-abs(est/se)),method=if(is.null(fit@optinfo$derivs))
                     "Exploratory Wald z; RX/PIRLS covariance; numerical check incomplete" else "Asymptotic Wald z; Hessian covariance")
  }
  ct[,`:=`(outcome=outcome,scope=scope)]; all_contrasts[[outcome]]<-ct
  # Point predictions at a declared lexical reference profile; no variance-uncertainty intervals.
  pg <- as.data.table(expand.grid(D=c(-.5,.5),L=c(-.5,.5),T=c(-.5,.5),S=seq(-1,2,length.out=61),F=0,W=0))
  eta <- as.numeric(grid_x(fit,pg)%*%fixef(fit)); v<-new_variance(fit,pg)
  stopifnot(max(abs(eta-predict(fit,newdata=as.data.frame(transform(pg,DL=D*L,TS=T*S)),re.form=NA,type="link")))<1e-8)
  if(outcome=="lmm"){
    zero <- exp(eta+sigma(fit)^2/2)
    integrated <- exp(eta+(v+sigma(fit)^2)/2)
  } else {
    zero <- plogis(eta); integrated<-integrated_probability(eta,v)
    stopifnot(max(abs(integrated-integrated_probability(eta,v,80)))<1e-7,
              max(abs(integrated[c(1,100,300)]-logit_normal_mean(eta[c(1,100,300)],v[c(1,100,300)])))<1e-7)
  }
  pg[,`:=`(zero_RE=zero,integrated=integrated,random_variance=v,
           match=ifelse(D==T,"own","other"),level=ifelse(L==-.5,"Undergraduate","Graduate"),outcome=outcome)]
  pg[,level:=factor(level,levels=c("Undergraduate","Graduate"))]
  avg <- pg[,.(zero_RE=mean(zero_RE),integrated=mean(integrated)),by=.(level,match,S,outcome)]
  all_predictions[[outcome]]<-avg
  p<-ggplot(avg,aes(S,integrated,color=match))+geom_line(linewidth=.9)+
    geom_line(aes(y=zero_RE),linetype="dashed",linewidth=.7)+facet_wrap(~level)+scale_color_manual(values=palette)+
    labs(x="GPT-2-large surprisal (SD units)",
         y=if(outcome=="lmm") "Mean FPRT given fixation (ms)" else "First-pass regression probability",
         color="Text domain",title=if(outcome=="lmm") "Reading time and surprisal" else "First-pass regressions and surprisal",
         subtitle="Solid: integrated new-group mean.\nDashed: random effects set to zero.",
         caption="Equal discipline weights; length and log frequency at reference means.\nPlug-in point estimates; parameter uncertainty is not shown.")
  ggsave(file.path("outputs/figures",paste0(outcome,"-predictions.png")),p,width=9,height=5.4,dpi=150)
  ids <- rownames(model.frame(fit)); d<-copy(data[match(ids,data$row_id)])
  stopifnot(identical(d$row_id,ids))
  fitted <- predict(fit,type="response")
  residual <- if(outcome=="lmm") residuals(fit)/sigma(fit) else (d$FPReg-fitted)/sqrt(fitted*(1-fitted))
  d[,`:=`(fitted_value=as.numeric(fitted),residual_value=as.numeric(residual))]
  setorder(d,reader,text,word_index_in_text)
  lag <- d[,.(r=residual_value,lagr=shift(residual_value),adjacent=word_index_in_text-shift(word_index_in_text)==1),by=.(reader,text)]
  adjacent_cor<-with(lag[adjacent==TRUE],cor(r,lagr,use="complete.obs"))
  d[,bin:=pmin(10L,ceiling(frank(fitted_value,ties.method="average")/.N*10))]
  bin <- d[,.(fitted=mean(fitted_value),observed=if(outcome=="lmm") mean(log_FPRT) else mean(FPReg),
              residual_mean=mean(residual_value),residual_sd=sd(residual_value),n=.N),by=bin]
  fwrite(bin,file.path(path,"calibration_bins.csv"))
  diag_summaries[[outcome]]<-data.table(outcome=outcome,adjacent_pairs=sum(lag$adjacent,na.rm=TRUE),
      adjacent_residual_correlation=adjacent_cor,residual_sd_min=min(bin$residual_sd),residual_sd_max=max(bin$residual_sd),
      min_conditional_prediction=min(fitted),max_conditional_prediction=max(fitted))
  if(outcome=="lmm"){
    set.seed(20260927); small<-d[sample.int(nrow(d),min(5000,nrow(d)))]
    p<-ggplot(small,aes(sample=residual_value))+stat_qq(alpha=.25,size=.6)+stat_qq_line(color="#B65332")+
      labs(title="LMM conditional residual Q-Q plot",x="Normal theoretical quantile",y="Standardized residual")
    ggsave("outputs/figures/lmm-qq.png",p,width=7,height=4.5,dpi=150)
    p<-ggplot(small,aes(fitted_value,residual_value))+geom_point(alpha=.1,size=.6)+
      geom_smooth(method="loess",se=FALSE,color="#B65332")+
      labs(title="LMM conditional residuals",x="Fitted log milliseconds",y="Standardized residual")
    ggsave("outputs/figures/lmm-residuals.png",p,width=7,height=4.5,dpi=150)
  } else {
    events <- d[,.(words=.N,regressions=sum(FPReg),non_regressions=sum(FPReg==0),readers=uniqueN(reader)),by=.(D,L,T)]
    events[,`:=`(reader_discipline=ifelse(D<0,"Biology","Physics"),study_level=ifelse(L<0,"Undergraduate","Graduate"),
                 text_domain=ifelse(T<0,"Biology","Physics"))]
    fwrite(events[,.(reader_discipline,study_level,text_domain,readers,words,regressions,non_regressions)],
           "outputs/glmm_event_counts.csv")
    stopifnot(all(events$regressions>0),all(events$non_regressions>0))
    p<-ggplot(bin,aes(fitted,observed))+geom_abline(slope=1,intercept=0,color="grey60")+geom_point(size=2,color="#007A87")+
      coord_equal()+labs(title="GLMM conditional calibration",subtitle="In-sample deciles; descriptive, not held-out validation",
                         x="Mean predicted probability",y="Observed regression rate")
    ggsave("outputs/figures/glmm-calibration.png",p,width=7,height=4.5,dpi=150)
    # Conditional Bernoulli simulations: group aggregation and adjacent-word dependence.
    # No refitting, fixed beta and fitted random effects; this does not assess parameter uncertainty.
    set.seed(20260928)
    group<-interaction(d$reader,d$text,drop=TRUE)
    pair_idx<-which(as.character(group[-1])==as.character(group[-nrow(d)]) & diff(d$word_index_in_text)==1)+1L
    prob<-as.numeric(predict(fit,newdata=as.data.frame(d),type="response"))
    s<-replicate(200,{
      y<-rbinom(length(prob),1,prob)
      r<-(y-prob)/sqrt(prob*(1-prob))
      c(adjacent=cor(r[pair_idx],r[pair_idx-1L]),group_rate_sd=sd(tapply(y,group,mean)))
    })
    obs<-c(adjacent=cor(d$residual_value[pair_idx],d$residual_value[pair_idx-1L]),group_rate_sd=sd(tapply(d$FPReg,group,mean)))
    sim<-data.table(statistic=names(obs),observed=as.numeric(obs),
                    simulated_lower=apply(s,1,quantile,.025),simulated_upper=apply(s,1,quantile,.975),
                    nsim=200,mode="Conditional on beta and all fitted random effects; no refitting")
    fwrite(sim,file.path(path,"conditional_simulation_checks.csv"))
  }
  raw<-d[,.(FPRT_mean=mean(FPRT),FPReg_rate=mean(FPReg),n=.N),by=.(reader,D,L,match)]
  raw[,level:=factor(ifelse(L==-.5,"Undergraduate","Graduate"),levels=c("Undergraduate","Graduate"))]
  fwrite(raw,file.path(path,"reader_descriptives.csv"))
  p<-ggplot(raw,aes(match,if(outcome=="lmm") FPRT_mean else FPReg_rate,color=match))+
    geom_line(aes(group=reader),color="grey70",alpha=.5)+geom_point(alpha=.65,size=1.7)+
    facet_wrap(~level)+scale_color_manual(values=palette)+
    labs(x="Text relative to reader's discipline",y=if(outcome=="lmm") "Reader mean FPRT (ms), given fixation" else "Reader first-pass regression rate",
         title="Observed reader summaries",subtitle="Each point summarizes one reader and domain-match condition; denominators retained in CSV")+
    guides(color="none")
  ggsave(file.path("outputs/figures",paste0(outcome,"-raw.png")),p,width=9,height=4.8,dpi=150)
}
contrasts <- rbindlist(all_contrasts)
contrasts[,p_holm:=p.adjust(p,method="holm")]
fwrite(contrasts,"outputs/planned_contrasts.csv")
fwrite(rbindlist(all_predictions),"outputs/response_predictions.csv")
fwrite(rbindlist(diag_summaries),"outputs/diagnostic_summary.csv")
for(oc in c("lmm","glmm")){
  ct<-contrasts[contrasts$outcome==oc]
  ct[,contrast:=factor(contrast,levels=rev(unique(contrast)))]
  p<-ggplot(ct,aes(estimate,contrast))+geom_vline(xintercept=0,color="grey65")+
    geom_errorbar(aes(xmin=lower,xmax=upper),orientation="y",width=.15,color="#007A87")+
    geom_point(color="#007A87",size=2)+labs(x=if(oc=="lmm") "Log-ms contrast (surprisal contrasts per SD)" else "Log-odds contrast (surprisal contrasts per SD)",
       y=NULL,title="Planned domain-match contrasts",subtitle="Unadjusted 95% intervals; 12-test Holm-adjusted p-values in the table")
  ggsave(file.path("outputs/figures",paste0(oc,"-contrasts.png")),p,width=10,height=5,dpi=150)
}
cat("Summary complete for LMM",scopes$lmm,"and GLMM",scopes$glmm,"\n")
print(contrasts)
