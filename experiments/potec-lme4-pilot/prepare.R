args <- commandArgs(FALSE)
setwd(dirname(normalizePath(sub("^--file=", "", args[grepl("^--file=", args)]))))
suppressPackageStartupMessages(library(data.table))
dir.create("outputs", showWarnings=FALSE)
cols <- c("reader_id", "text_id", "word_index_in_text", "FPRT", "FPF", "FPReg",
          "reader_discipline_numeric", "level_of_studies_numeric", "text_domain_numeric",
          "word_length", "lemma_frequency_normalized", "text_surprisal_gpt2-large", "trial")
files <- sort(list.files("data/reading_measures_merged", "\\.tsv$", full.names=TRUE))
stopifnot(length(files)==900L)
d <- rbindlist(lapply(files, fread, select=cols, na.strings=c("NA","nan","")))
setnames(d, "text_surprisal_gpt2-large", "surprisal_merged")
d[, row_id := paste(reader_id,text_id,word_index_in_text,sep=":")]
d[, item_id := paste(text_id,word_index_in_text,sep=":")]
stopifnot(!anyDuplicated(d$row_id), nrow(d)==142125L,
          uniqueN(d$reader_id)==75L, uniqueN(d$item_id)==1895L,
          all(d$FPF %in% 0:1),all(d$FPReg %in% 0:1),all(d$FPRT >= 0),
          all((d$FPRT>0)==(d$FPF==1)), all(d$FPReg[d$FPF==0]==0))
wf <- rbindlist(lapply(sort(list.files("data/source/stimuli/word_features", "tsv$", full.names=TRUE)),
                      fread, select=c("text_id","word_index_in_text","lemma_frequency_normalized",
                                      "text_surprisal_gpt2-large"),na.strings=c("NA","nan","")))
setnames(wf,c("lemma_frequency_normalized","text_surprisal_gpt2-large"),c("frequency_source","surprisal_source"))
stopifnot(!anyDuplicated(wf[,.(text_id,word_index_in_text)]))
d <- merge(d,wf,by=c("text_id","word_index_in_text"),sort=FALSE,all.x=TRUE)
stopifnot(nrow(d)==142125L,!anyNA(d$surprisal_source),
          max(abs(d$surprisal_merged-d$surprisal_source))<1e-10,
          all(d$lemma_frequency_normalized[is.na(d$frequency_source)]==0))
setorder(d,reader_id,text_id,word_index_in_text)
groups <- unique(d[,.(reader_id,reader_discipline_numeric,level_of_studies_numeric)])
missing <- d[,.(rows=.N,missing_frequency=sum(is.na(frequency_source)),
                skipped=sum(FPF==0),first_pass_fixated=sum(FPF==1),regressions=sum(FPReg==1))]
fwrite(groups[,.(readers=.N),by=.(reader_discipline_numeric,level_of_studies_numeric)],"outputs/reader_groups.csv")
fwrite(missing,"outputs/data_counts.csv")
fwrite(d[,.(rows=.N,missing_frequency=sum(is.na(frequency_source)),fixated=sum(FPF==1),regressions=sum(FPReg)),by=text_id],
       "outputs/text_counts.csv")
# Primary analysis excludes unavailable lexical frequencies, not zero-millisecond skips.
# The upstream merged files replace missing lexical features by zero. Restore source missingness.
d[, included := is.finite(frequency_source) & frequency_source>0 & is.finite(surprisal_source)]
fwrite(d[,.(row_id,included,FPF)],"outputs/row_eligibility.csv")
a <- d[included==TRUE]
u <- unique(a[,.(item_id,word_length,frequency_source,surprisal_source)])
constants <- data.table(variable=c("W","F","S"),
                       center=c(mean(u$word_length),mean(log(u$frequency_source)),mean(u$surprisal_source)),
                       scale=c(sd(u$word_length),sd(log(u$frequency_source)),sd(u$surprisal_source)))
fwrite(constants,"outputs/scaling.csv")
a[, `:=`(D=reader_discipline_numeric-0.5,L=level_of_studies_numeric-0.5,T=text_domain_numeric-0.5)]
a[, `:=`(W=(word_length-constants$center[1])/constants$scale[1],
         F=(log(frequency_source)-constants$center[2])/constants$scale[2],
         S=(surprisal_source-constants$center[3])/constants$scale[3])]
a[, `:=`(DL=D*L, TS=T*S, log_FPRT=ifelse(FPRT>0,log(pmax(FPRT,1)),NA_real_),
         reader=factor(reader_id),item=factor(item_id),text=factor(text_id),
         reader_text=interaction(reader_id,text_id,drop=TRUE),
         match=ifelse(D==T,"own","other"))]
support <- rbindlist(lapply(c("reader","item","text","reader_text"),function(g)
  rbindlist(lapply(c("D","L","T","S","F","W","TS","DL"),function(v){
    x<-a[,uniqueN(get(v)),by=g]$V1
    data.table(group=g,predictor=v,groups=length(x),min_distinct=min(x),max_distinct=max(x))
  }))))
fwrite(support,"outputs/design_support.csv")
set.seed(20260927)
sample_items <- unique(a[,.(item,text)])[,.SD[sample.int(.N,max(1L,ceiling(.N/4)))],by=text]$item
a[, pilot_subset := item %in% sample_items]
saveRDS(a,"outputs/analysis_data.rds")
writeLines(capture.output(sessionInfo()),"outputs/sessionInfo.txt")
cat("Unique rows:",nrow(d),"; readers:",uniqueN(d$reader_id),"; items:",uniqueN(d$item_id),"\n")
print(missing)
cat("Primary GLMM rows:",nrow(a),"; LMM rows:",sum(a$FPF==1),"\n")
cat("Timing subset GLMM rows:",sum(a$pilot_subset),"; LMM rows:",sum(a$pilot_subset & a$FPF==1),"\n")
print(constants)
