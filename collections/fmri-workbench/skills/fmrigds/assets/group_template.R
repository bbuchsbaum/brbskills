# Source this function into a study script. It constructs a lazy plan, never computes.
# `method`, formula, correction and inclusion semantics must be reviewed first.
build_group_plan <- function(input, method, formula = NULL, col_data = NULL,
                             contrast = NULL, options = NULL, posthoc_method = NULL) {
  if (!requireNamespace("fmrigds", quietly = TRUE)) stop("fmrigds is required")
  if (!is.character(method) || length(method) != 1L || !nzchar(method)) stop("Supply a reviewed registered reducer ID")
  if (!is.null(formula) && !inherits(formula, "formula")) stop("Use a reviewed formula, not a dataset-supplied string")
  args <- list(input)
  if (!is.null(col_data)) args$col_data <- col_data
  plan <- do.call(fmrigds::gds, args)
  if (!is.null(contrast)) plan <- subset(plan, contrast = contrast)
  ra <- list(plan, method = method)
  if (!is.null(formula)) ra$formula <- formula
  if (!is.null(options)) ra$options <- options
  plan <- do.call(fmrigds::reduce, ra)
  if (!is.null(posthoc_method)) plan <- fmrigds::posthoc(plan, posthoc_method)
  plan
}
# Inspect/validate the returned plan and the correction family; compute separately
# after explicit approval. Different reducers produce different named assays.
