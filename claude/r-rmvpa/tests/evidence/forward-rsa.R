library(rMVPA)
library(neuroim2)

set.seed(1)
sample <- gen_sample_dataset(c(3, 3, 3), 12, blocks = 3, nlevels = 2)
semantic_features <- matrix(rnorm(12 * 3), 12, 3)
visual_features <- matrix(rnorm(12 * 2), 12, 2)
semantic_rdm <- dist(semantic_features)
visual_rdm <- dist(visual_features)
run_rdm <- outer(sample$design$block_var, sample$design$block_var, "!=") * 1

design <- rsa_design(
  ~ semantic + visual,
  data = list(semantic = semantic_rdm, visual = visual_rdm),
  nuisance = list(run = run_rdm),
  block_var = sample$design$block_var,
  keep_intra_run = TRUE
)
print(names(design$model_mat))
print(rsa_design_diagnostics(design))
spec <- rsa_model(sample$dataset, design, regtype = "lm", statistic = "beta")
observed <- run_searchlight(spec, radius = 1)
print(class(observed))
print(names(observed$results))
perm <- run_permutation_searchlight(
  spec, observed = observed, radius = 1,
  perm_ctrl = permutation_control(n_perm = 2, seed = 2, rsa_null = "joint", correction = "none"),
  metric = "semantic"
)
print(class(perm))
print(names(perm))
