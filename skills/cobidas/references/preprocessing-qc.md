# Preprocessing and quality control

COBIDAS Table D.3 is the formal checklist [C1]. This module specifies what to record so those rows can be answered from evidence.

## Record a transformation graph

Represent each transformation as input → operation/settings → output, with its producing receipt. Preserve the actual order or joint implementation: a workflow can estimate transforms in one order and apply their composition in a single interpolation. Report both where material.

For each component retain executed name, version/revision (e.g., SPM12 revision number, not only "SPM12"), method citation and, where available, an RRID. For a container keep the digest, not a mutable tag. Pipeline-generated boilerplate is evidence to verify against the actual version, participants and branches [F1, F2].

## Spatial operations

- **Anatomical:** bias-field correction, brain extraction (method, parameters such as BET's fractional intensity threshold, manual mask edits), tissue segmentation, surface reconstruction (software/version, flags, manual edits).
- **Slice timing:** performed or not; method; reference slice/time; interpolation (e.g., sinc, Fourier, spline); order relative to motion correction. Multiband data need the true `SliceTiming` vector.
- **Motion correction:** software, rigid versus non-rigid, reference volume (first, middle, mean, SBRef), similarity metric, interpolation, and any slice-to-volume or combined STC/motion method.
- **Susceptibility distortion correction:** not performed; field-map-based; reversed-phase-encoding (e.g., FSL topup, AFNI 3dQwarp, SDCFlows); field-map-less (e.g., SyN-based, fMRIPrep's `--use-syn-sdc`); or another verified method. Record per-participant fallbacks. Record gradient-nonlinearity correction separately.
- **Function-to-structure coregistration:** method, degrees of freedom or nonlinear model, cost function (e.g., boundary-based registration, mutual information, correlation ratio), interpolation.
- **Intersubject registration:** software; volume and/or surface; images registered; warp type (affine, B-spline, diffeomorphic/SyN) with resolution and regularization; cost function and masking; interpolation.
- **Output space:** a specific template identifier, cohort and resolution (e.g., TemplateFlow `MNI152NLin2009cAsym` at `res-2`, versus `MNI152NLin6Asym`), or surface space and density (`fsaverage`, `fsaverage5`, `fsLR` 32k), or CIFTI grayordinates (91k). "MNI space" alone is ambiguous. If coordinates are converted (e.g., MNI to Talairach), record the transform used. For volume-to-surface projection record the sampling method (e.g., ribbon-constrained between white and pial surfaces).
- **Smoothing:** performed or not; kernel type and FWHM with units; fixed kernel versus iterative smoothing to a target FWHM; volume versus surface/geodesic; space and stage; mask/boundary handling. Distinguish acquisition resolution, output grid, applied kernel and estimated residual smoothness. Keep unsmoothed decoding and smoothed univariate branches in separate scopes.

For multi-echo data record echo times, discarded echoes, combination method (e.g., T2*-weighted), T2* estimation and fitting method, any ME-ICA/tedana denoising with version and component decisions. Combination is not denoising [F1].

## Intensity operations

Record intensity correction (bias field; odd/even slice intensity differences) and intensity normalization: grand-mean scaling per run (SPM scales the global mean to 100; FSL FEAT scales the in-mask median of the 4D series to 10,000), voxelwise percent-signal scaling (common in AFNI pipelines), or none. The scaling defines the units of every downstream effect estimate.

## Nuisance model

Record exactly which confounds entered which model, their source file and column names, and construction [C1].

- **Motion:** base parameters and expansion. "24 parameters" must specify which set (e.g., 6 + 6 temporal derivatives + squares of both, versus the Friston 24 using one-TR-lagged values) and handling of the undefined first derivative.
- **Tissue signals:** tissue type, mask definition and erosion, signal definition (mean, principal components), and CompCor variant (anatomical/temporal, combined or separate masks), component count or variance criterion per run.
- **Global signal:** whether used, and exactly how computed.
- **Physiology:** recording devices, sampling rate, synchronization, model (e.g., RETROICOR order, respiratory volume per time, heart-rate convolution) and number of regressors.
- **ICA denoising:** method and version (e.g., ICA-AROMA, FSL FIX with its training set), aggressive versus non-aggressive regression, and manual classification decisions.

A confounds table lists candidate regressors; it does not show which were fitted. fMRIPrep writes `desc-confounds_timeseries.tsv` for downstream selection; inspect the actual design or denoising call before saying anything was regressed out [F1]. fMRIPrep high-pass filters before computing CompCor, so its documentation says the matching `cosine_XX` columns belong in the design whenever its CompCor components do; record whether that was done.

## Temporal filtering and joint projection

Record the drift/filter basis and settings: polynomial degree, discrete cosine set and cutoff (SPM's 128 s default is a DCT cutoff), FSL's Gaussian-weighted running-line high-pass (sigma or cutoff), band-pass limits in Hz, implementation, edge handling, run boundaries, and order relative to nuisance regression. When data are filtered, record whether the model regressors were filtered identically; COBIDAS requires this for temporal regression on filtered data. Do not convert a polynomial degree into a fictitious cutoff.

For joint regression keep the combined design and its rank; do not describe it as sequential steps. With `Z` the joint nuisance/filter design, the residual-forming matrix is `M_Z = I - Z Z⁺`; in general `M_A M_B ≠ M_[A B]`, so sequential steps can reintroduce removed variance [L1]. AFNI `3dTproject` performs filtering and regression as one projection and exposes several censor modes [A1]; record the mode that ran.

## Censoring and degrees of freedom

Name the motion metric and formula. Framewise displacement differs by implementation: Power et al. sum absolute derivatives with rotations converted on a 50-mm sphere (fMRIPrep's `framewise_displacement`); Jenkinson's relative RMS (FSL `mcflirt`; fMRIPrep's `rmsd`) and AFNI's Euclidean-norm `enorm` are different quantities, so thresholds do not transfer. Record units, threshold and comparison, DVARS variant (raw or standardized), neighbour expansion, rule combination, minimum retained data and the actual censor vectors. fMRIPrep's `motion_outlier_XX` columns use FD > 0.5 mm or standardized DVARS > 1.5 by default [F1]; verify the values that ran.

Distinguish removing rows, spike regressors, interpolation and weighting; "scrubbing" can mean any of these. If interpolated samples are later filtered, say whether they enter the fit.

Retain raw, discarded, censored and final model rows, column count and rank. For full-rank OLS, residual df = retained rows − rank; with prewhitening, filtering, regularization or resampling, record the estimator's actual df or effective-df convention. Concatenated runs must preserve boundaries and per-run intercept/drift terms as executed.

## Derived resting-state features

For ALFF/fALFF record the frequency band; for ReHo the neighbourhood (e.g., 7, 19 or 27 voxels, i.e., 6-, 18- or 26-connectivity) and similarity measure (Kendall's W) [C1].

## QC is a method plus a result

Where possible specify QC criteria and decision authority before inspecting outcomes. Retain metrics (e.g., mean FD, DVARS, tSNR), images or reports inspected, reviewer type (human, agent, automated threshold), date, findings, decision and rationale. Agent visual review is not "expert manual QC"; a generated report is not proof of review.

Record exclusions and modifications per participant, session, run and echo; separate preplanned thresholds from post hoc judgement. Preserve manual masks and edits with before/after identity. Propagate exclusions into models and result tables, and summarize retained/censored data in the supplement rather than writing "all data were quality checked".

Sources: [C1]; metadata and tool semantics [B1–B3, F1, F2, A1, A2, L1]. The transformation graph and receipt conventions are local extensions.
