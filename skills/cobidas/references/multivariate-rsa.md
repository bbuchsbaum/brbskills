# Prediction, decoding, encoding, RSA and naturalistic analyses

COBIDAS D.4/D.5 already cover multivariate and predictive models and name RSA [C1]. This module adds finer records for fitted pipelines and agent-driven workflows; these additions are not an OHBM update.

## Target, features and generalization claim

Declare the model type in COBIDAS terms (local multivariate/searchlight, intra-subject predictive, inter-subject predictive, RSA, classical multivariate such as MANOVA with its covariance assumption and test statistic). Record observation and independent sampling units, target type, class proportions or target distribution, and population stratification relevant to the target (e.g., age or sex by class) and how it was handled.

Record feature dimension before and after every selection or reduction step. For searchlights record shape, radius and the exact voxel/vertex count per sphere (not only the radius), edge handling and the statistic mapped. State the intended generalization: new trials, runs, stimuli, participants, sites or time periods. Training and testing on different trials from the same person does not establish generalization to new people.

## Splits and fit boundaries

Persist the actual fold-assignment manifest: outer and inner splits, grouping, stratification, repetitions, temporal gaps and external test sets. Record seed and implementation version, but keep the assignments. Within-run trials share temporal autocorrelation and drift; if train and test trials come from the same run, record it as a leakage risk rather than calling folds independent (leave-one-run-out is the usual guard). Freeze held-out data and log every time its outcomes influenced later choices.

For each learned transform record **which samples fitted it**, its artifact and where it was applied: feature selection, scaling, nuisance residualization, PCA/SVD, parcellation, hyperalignment or shared-response alignment, harmonization (e.g., ComBat), target transforms and hyperparameter search. Fitting any of these with test data leaks information even when the final estimator is cross-validated [M1]. A Pipeline object does not guarantee that nothing outside it was fitted globally. Record transductive procedures explicitly.

Record estimator and objective (e.g., linear SVM, logistic regression, LDA, ridge), kernel and its parameters, penalty, fitted rank, hyperparameter grid and search budget, selection criterion, nesting, convergence monitoring, random starts, ensembling and final refit. Record all model families and feature spaces tried; agent-driven search is analytic flexibility.

## Evaluation and uncertainty

For discrete targets report accuracy and, with unequal classes, balanced accuracy; for binary problems precision, recall, false-positive rate, F1 and ROC AUC as used; for three or more classes the confusion matrix [C1]. For continuous targets, prediction R² = 1 − (prediction sum of squares / total sum of squares) and is not the squared correlation between predicted and true values [C1]; record which mean (training or test) defines the total sum of squares. Record chance level, per-fold versus pooled aggregation and test-set size. Separate performance used for selection from outer-test performance.

For permutation or bootstrap tests record the resampling unit, dependence structure and whether the whole pipeline was refitted per resample. A second-level t-test of accuracies against chance tests a mean above chance, not that the effect is present in most participants; state which question the group test answers. Searchlights and multiple decoders add multiplicity. Repeated splits are not independent participants.

## Pattern interpretation

Decoder weights are not activation patterns. For transformed patterns (e.g., Haufe-style forward models) record the formula, covariance estimate, scaling and which data fitted them. Record components, sign conventions and back-projection. A pattern computed on all data for description is not an out-of-sample estimate.

## RSA and encoding–retrieval similarity

Record condition/trial/item identities and order, pattern estimator (betas, t values, prewhitened estimates), noise normalization or whitening, dissimilarity measure (correlation distance, Euclidean, crossnobis or other crossvalidated distance) and whether estimates are crossvalidated across runs. Do not truncate negative crossvalidated distances silently.

For model comparison record model RDM construction, the comparison statistic actually used (COBIDAS listed Kendall's τ; record the variant, e.g., τ-a, or Spearman, Pearson, or regression weights), nuisance models, noise ceiling and the inference unit (participants, stimuli, or both). RDM cells share items and are not independent observations.

For encoding–retrieval similarity record paired-item and off-diagonal comparisons, baseline correction, item matching, trial exclusions, memory measure definitions and within/between-person centring, and how multiple memory measures were modelled and corrected. A conditional association is not a causal claim about a representational dimension.

## Naturalistic features and learned models

Record the exact feature model and checkpoint identity (not only a public model name), layers, preprocessing/tokenization, reduction, sampling/binning and hemodynamic alignment (e.g., FIR delays or HRF convolution). Preserve stimulus/frame/transcript hashes and crop/time-origin mappings. Record whether features were extracted with a cloud service and the approved data boundary. Use splits that respect temporal autocorrelation, and state stimulus and participant overlap across training, tuning and testing.
