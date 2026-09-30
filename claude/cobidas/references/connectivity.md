# Resting-state and connectivity

Use [preprocessing-qc.md](preprocessing-qc.md) for nuisance, filtering and censoring records and [models-inference.md](models-inference.md) for inference. This module covers the remaining objects in COBIDAS D.4/D.5 functional-connectivity rows [C1]; it does not recommend a denoising strategy.

## Signals and dependence measure

For seed analyses record each seed's definition and the rationale for choosing it. For region-based analyses record the parcellation name, version and resolution (e.g., number of parcels and network assignment), number of ROIs, overlap, transform into analysis space, extraction rule (mean, weighted mean, first eigenvariate/singular vector), coverage and absent-region handling, bilateral merging or homotopic-only restrictions, and label-to-column order. Record whether nuisance removal was voxelwise or after extraction.

Name the dependence estimator: full or partial correlation (with the partial-correlation or precision estimator and regularization, e.g., graphical lasso, Ledoit–Wolf shrinkage), covariance, mutual information (estimator), tangent-space or other embeddings. Record Fisher transformation and, if values are standardized, the effective sample size used for the standard error given filtering and autocorrelation [C1]; a Fisher z is not a test statistic. Record self-edge, sign and missing-data handling, and whether runs were concatenated or estimated separately and combined.

For task connectivity distinguish background/residual connectivity, beta-series correlation, PPI or generalized PPI (psychological coding, deconvolution, interaction construction) and effective connectivity. For effective connectivity (e.g., DCM, Granger-type models) record the model space, fitting algorithm, model comparison method and how per-subject models generalize to the population. Undirected functional connectivity is not causal influence.

## ICA and network models

Record data reduction, ICA algorithm and implementation, number of components (fixed or estimated, and how), multi-run/multi-subject strategy (e.g., temporal concatenation group ICA), repeated starts or stability analysis and seeds, back-reconstruction or dual regression, component sorting, and the exact rules and people or classifiers used to select components for analysis. Report the total component count and why the analysed subset was chosen. Separate component discovery from testing selected components.

For graphs record weighted versus binarized analysis, thresholding (absolute, proportional density, statistical) and sensitivity to it, negative-edge treatment, disconnected components, metric definitions, whether metrics are global, nodal or edgewise, and whether they were computed on individual or group networks. State the null hypothesis and how the null distribution was generated (e.g., degree-preserving rewiring, permutation of labels) [C1]. Record whether thresholds were fixed before results were seen and whether comparisons control for density or mean connectivity.

For dynamic measures record window shape, length and step, state estimation and number of states, temporal-dependence handling and the null model. For intersubject correlation or ISFC record stimulus alignment, leave-one-out versus pairwise construction, and the resampling scheme; participant pairs are not independent observations.

## Motion and connectivity

Link the actual confound design and censor vectors, global-signal handling, retained time points per participant and analysis, and group differences in motion. If motion–connectivity benchmarks (e.g., QC-FC correlations, distance dependence) or motion-matched sensitivity analyses were computed, record them; do not imply they were checked when only a threshold was applied.

COBIDAS addresses functional connectivity, effective connectivity, ICA and graph analyses directly [C1]. Ledger scopes, fit artifacts and branch linkage are local additions.
