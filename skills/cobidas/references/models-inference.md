# Models, contrasts and inference

Report the fitted statistical object, not a package name. COBIDAS Table D.4 lists modelling and inference items and Table D.5 results items; Appendix C gives short model descriptions for specific historical versions (AFNI 2011, FreeSurfer 5.3, FSL 5.0.8, SPM12 r6470) [C1]. Those descriptions are not current defaults; confirm what ran.

## First-level task fMRI

Record the dependent variable and its scaling/units, analysis space and mask, number of time points after exclusions, and actual participant/run/trial membership. Preserve the formula, full column map, contrast vectors and the fitted design matrix (or a reproducible generator plus input hashes).

For each task regressor record condition definition, onset/duration/amplitude mapping (event versus modelled duration; whether block baseline is explicit or implicit), excluded or separately modelled trials, and the HRF basis:

- canonical only; canonical plus temporal derivative; plus dispersion derivative;
- a smooth basis (e.g., SPM informed or Fourier set, FSL FLOBS);
- FIR/TENT windows and bin widths; or another parameterised response (e.g., AFNI `BLOCK`/`GAM`/`SPMG`), with its parameters.

Name the canonical form actually used (SPM's double gamma differs from FSL's gamma or double-gamma options and from AFNI's defaults), the convolution/oversampling grid and time reference (see [design-acquisition.md](design-acquisition.md#time-origin-accounting)). Parametric modulators need source, coding, centring/scaling, missing values, and whether serial orthogonalization was applied and against what; SPM orthogonalizes modulators serially by default in many versions, so verify. Link nuisance and drift regressors to [preprocessing-qc.md](preprocessing-qc.md).

Record estimator and temporal error model, for example: OLS (AFNI `3dDeconvolve`); GLS with a voxelwise ARMA(1,1) model (AFNI `3dREMLfit`); FSL FILM prewhitening with a spatially and temporally regularized autocorrelation estimate; SPM's global approximate AR(1) (plus white noise), estimated by ReML over pooled voxels, or its FAST option; nilearn AR(p) with its order. "Autocorrelation corrected" is insufficient. State how runs are combined (concatenated design versus per-run fits combined by fixed effects) and weights; a within-participant fixed-effects summary is not population inference.

For trialwise models identify least-squares-all, least-squares-separate or another estimator, grouping, nuisance treatment, regularization and trial correspondence. Preserve the covariance/uncertainty object downstream analyses need; do not substitute t maps for beta maps silently.

## Group, longitudinal and repeated measures

Record the lower-level input (contrast estimate with or without its variance, t/z, Fisher z, accuracy, thickness), scaling and harmonization. Record fixed effects and interactions, coding and reference levels, centring, whether covariates are split by group (group × covariate interaction), within/between-person decomposition, and for VBM total grey matter or ICV adjustment.

Name the random- or mixed-effects implementation: unweighted summary-statistic OLS (SPM default; FSL "simple OLS"; AFNI `3dttest++`); weighted/mixed-effects using first-level variances (FSL FLAME1 or FLAME1+2; AFNI `3dMEMA`; SPM MFX); or linear mixed models (AFNI `3dLME`/`3dLMEr`, `3dMVM`, or R/Python LMMs with ML versus REML and df method). A first-level fixed-effects analysis over all participants' data is not random effects.

State the unit of independence and dependence model: unequal group variances (and whether pooled globally, as in SPM's non-sphericity estimate), the repeated-measures covariance (compound symmetry, unstructured), and whether subjects enter as regressors or through covariance. Repeated visits, conditions, trials, families and sites are not independent because they are rows. For longitudinal inference record time coding, scanner changes, attrition and missing-data handling.

Record singular fits, boundary estimates, convergence changes, dropped coefficients, rank-deficient contrasts and voxelwise variation in sample size. "Mixed effects" does not imply random slopes. Preserve all tested contrasts and their direction.

## ROI and search-space definitions

Identify atlas name/version, labels, coordinate space/grid, mask derivation, thresholds, resampling, coverage and voxel/vertex counts. State union/intersection and missing-coverage policy. A functional ROI selected with the tested contrast, or with data not independent of it, is circular [K1]; statistics extracted from it are biased and COBIDAS advises against reporting them as inference. Record the independence argument (separate localizer runs, orthogonal contrast, leave-one-subject-out definition, anatomical atlas) and never rewrite a functional ROI as an anatomical one. Describe every small-volume correction, its mask source and whether that mask is independent of the tested data.

## Inference contract

An inference record answers:

- What effect, statistic, unit and tails were tested? A two-sided test run as two one-sided contrasts ([1 −1] and [−1 1]) needs its p-values doubled (or alpha halved) [C1].
- How was the null or uncertainty obtained (parametric, permutation, sign-flipping, bootstrap, Monte Carlo) and under which assumptions?
- Which family was corrected: voxels, vertices, ROIs, edges, contrasts, outcomes, time bins?

Record:

- **Statistic type:** voxel/peak, cluster extent, cluster mass, or TFCE.
- **Cluster inference:** cluster-forming threshold as both p and statistic value with df; neighbourhood (6, 18 or 26 in volume; surface adjacency); the corrected cluster-level alpha.
- **TFCE:** H, E and connectivity; flag non-default values (FSL `randomise` 3D defaults are H = 2, E = 0.5; 2D/surface settings differ).
- **Correction method:** FWE by random field theory (with smoothness estimate and resel count), permutation (tool, e.g., `randomise`, PALM, SnPM; permutation count; exchangeability blocks; sign flipping; seed), Monte Carlo simulation (e.g., AFNI `3dClustSim` with version, mask, and whether `-acf` spatial autocorrelation was used), or Bonferroni; FDR variant (Benjamini–Hochberg voxelwise, topological/cluster FDR); or none.
- **Search volume** in voxels and mm³ and estimated smoothness (FWHM) when RFT is used [C1].

Parametric cluster inference with a lenient cluster-forming threshold (e.g., p = 0.01) can have inflated familywise error [E1]. Record the threshold that was actually used; raise validity concerns separately rather than changing the threshold during writing. Reporting an uncorrected analysis transparently differs from claiming correction.

For bootstrap intervals record resampling unit, blocking, repetition count, interval type and what was re-estimated. Folds, correlated trials or repeated splits are not independent people.

## Results connection

Retain the complete list of tested and omitted effects, including main effects behind reported differences or interactions. Coordinate tables need the contrast, coordinate system (MNI template or Talairach) and whether peaks or centres of mass, label source (atlas and version), the p-value basis (e.g., voxel FWE or cluster FDR), statistic with df, search volume, cluster size in mm³ (or voxels with voxel size) and the peak-selection rule (e.g., SPM's up to three peaks at least 8 mm apart). Share unthresholded statistic maps (COBIDAS marks this mandatory) and record the repository identifier.

Display thresholds may differ from inference thresholds only if stated. A significant cluster does not license claims about every voxel inside it. Different within-group significance does not establish a group difference; report the interaction or contrast actually tested. When reporting R² or percent change, state how drift and nuisance variance were treated. Keep prespecified, exploratory and sensitivity results labelled.
