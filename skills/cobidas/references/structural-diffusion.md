# Structural, surface, segmentation and diffusion analyses

COBIDAS Table D.3 includes diffusion and perfusion processing rows; D.4 covers group models for morphometry [C1].

## Structural and surface measures

Record source sequences, image quality, bias correction, brain extraction, segmentation or reconstruction software and version (e.g., FreeSurfer version and `recon-all` flags, CAT12, FSL FAST/FIRST, ANTs), template/atlas and transforms, and manual edits. Identify the analysed quantity with units: volume, cortical thickness, surface area, grey-matter probability or density, shape. For VBM record the spatial normalization (e.g., DARTEL or Shooting templates), whether modulation (Jacobian scaling) was applied, and the smoothing kernel; modulated volumes and unmodulated concentrations answer different questions. Record the intracranial-volume or total-grey-matter measure and how it was adjusted (covariate, proportion, residualization).

For surfaces record topology and mesh density (e.g., fsaverage, fsaverage5, fsLR 32k), registration to the template (e.g., spherical folding-based or MSM), hemisphere conventions, medial-wall handling, sampling depth, and smoothing as geodesic FWHM on the surface. Link labels to the exact atlas version. Record the grid of masks and the image they were defined on.

For longitudinal processing record within-subject template construction and symmetry, time-point inclusion, cross-sectional versus longitudinal streams, and handling of missing visits or scanner changes. Longitudinal data processed cross-sectionally should be described that way.

## Manual or agent-assisted segmentation

Record the anatomical protocol and version, image contrast and resolution, landmarks, uncertainty policy, labels and boundary conventions. Describe manual, automated and hybrid steps accurately. Record raters or agents, training, blinding, adjudication, edits and reliability (e.g., inter-rater Dice or ICC) when measured. Human approval of an algorithm's output is not expert tracing.

For agent-assisted work retain the skill/model identity the environment exposes, tools and code, input views, consequential decisions, human review and validation-set separation. Store masks with geometry and label definitions. A high-resolution label does not show the boundary was visible in the input contrast.

## Diffusion processing

Record in actual order: denoising (e.g., MP-PCA), Gibbs-ringing correction, susceptibility correction (e.g., reversed phase-encoding with topup), eddy-current and motion correction (software; integrated with motion correction or not; cost function; transform and whether constrained along phase encoding; Jacobian intensity modulation; slice-outlier replacement), gradient-nonlinearity correction, b-vector rotation, bias correction, registration and interpolation [C1]. Preserve the final gradient table and its coordinate convention; rotating images without rotating b-vectors changes the model inputs.

For model fitting record the model (tensor, kurtosis, multi-compartment, constrained spherical deconvolution or other ODF), parameterization and number of free parameters, constraints, shells used, estimation method (e.g., OLS, WLS, nonlinear), outlier handling, response-function estimation (from the data, how, or simulated) and fit-quality evidence (residual maps, sample slices) [C1]. Distinguish ODF from fibre orientation distribution outputs, and scanner-derived maps from locally fitted ones. Record derived measures (FA, MD, AD, RD, MK and so on) with units.

For tractography record software, deterministic or probabilistic algorithm, seeding strategy and count, step size, angle threshold, stopping and length criteria, anatomical constraints, inclusion/exclusion ROIs and how they were drawn, filtering or weighting (e.g., SIFT), and connectome assignment. Define the edge quantity precisely; streamline count is not axon count or connection probability.

For TBSS or other skeleton analyses record the FA threshold, skeleton construction, projection, and whether a standard or study-specific target and atlas were used and from which participants. Report failed fits, missing tracts and affected membership.

## Scope limit

COBIDAS includes basic ASL and DSC perfusion acquisition and processing rows, but this skill's local catalogue does not model them, nor MR spectroscopy, susceptibility mapping or other quantitative MRI. Use the official rows plus current modality-specific consensus guidance, add local fields deliberately, and keep the limitation in the audit until reviewed. Local extensions here include agent-assisted segmentation provenance and mask correspondence.
