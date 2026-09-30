# Integration contracts

## Contents

- One factual source of truth
- Existing workflow and provenance systems
- BIDS and dataset discovery
- fMRIPrep and other NiPreps
- AFNI, FSL, SPM and custom workflows
- Agent contribution and privacy
- Project reminder

## One factual source of truth

This skill is a reporting consumer and checkpoint protocol. It does not submit MRI jobs, choose contrasts or motion thresholds, or replace a working provenance system. When a pipeline already writes structured plans, receipts or manifests, map them to facts with precise pointers; do not keep a second hand-copied parameter store that can disagree with them.

An adapter needs three kinds of information: actual scientific parameters; activity identity with inputs, outputs and validation; and decisions or deviations. The adapters below are contracts to implement with existing tools, not bundled parsers.

## Existing workflow and provenance systems

Any pipeline works: this skill assumes no particular workflow manager, lab convention or companion skill. Map whatever already records execution, for example Nipype provenance and crash files, Snakemake or Nextflow run reports, DataLad `run` records, BIDS derivative `dataset_description.json`, CI logs, or a lab's own plan and receipt files. Use each system's own documentation for file names and schemas; this skill does not define them. If an existing record and this ledger disagree, inspect the producing artifact and record a conflict rather than choosing one.

## BIDS and dataset discovery

Use a BIDS-aware resolver (e.g., pybids or an equivalent). Preserve each target file, resolved fields, inherited sources and overrides, BIDS version and validator version/results, and `dataset_description.json` including derivative `GeneratedBy` and `SourceDatasets` [B1–B3]. Resolve actual files rather than hard-coding paths from one example.

Group acquisition signatures only after scanning the selected cohort; store signature fields, member manifest and exceptions. Do not infer an acquisition matrix from a resampled derivative, or protocol facts from `participants.tsv` columns without their definitions.

## fMRIPrep and other NiPreps

Link each run attempt to its logs, fMRIPrep version and container digest, command line and resolved configuration, generated methods, HTML reports, and derivative `dataset_description.json`. Check which participants and runs succeeded, which fallbacks differed (e.g., field-map-less SDC, `--fallback-total-readout-time`, skipped surface reconstruction), and which derivative version reached downstream models.

Verified output conventions [F1]; recheck against the executed version:

- Since 21.0 the default layout writes derivatives directly in the output directory (`--output-layout bids`); earlier versions and `--output-layout legacy` nest them under `fmriprep/`. The `logs/` directory holds the citation boilerplate (`CITATION.md` with HTML, LaTeX and BibTeX variants in recent versions). Locate these files rather than assume a path.
- Confounds are in `*_desc-confounds_timeseries.tsv` with a JSON sidecar (older versions: `desc-confounds_regressors`). Columns include `trans_*`/`rot_*` with `_derivative1`, `_power2` and `_derivative1_power2` expansions, `framewise_displacement` (Power), `rmsd` (Jenkinson), `dvars`, `std_dvars`, `global_signal`, `csf`, `white_matter`, `a_comp_cor_*`, `t_comp_cor_*`, `cosine_*`, `non_steady_state_outlier_*` and `motion_outlier_*`. The sidecar records CompCor masks, variance explained and retention.
- CompCor is computed after DCT high-pass filtering; the documentation says to include the matching `cosine_*` regressors when CompCor components are used.
- Nonsteady-state volumes are flagged, not removed, from the preprocessed BOLD series.
- Output spaces are TemplateFlow identifiers (e.g., `MNI152NLin2009cAsym` default, `MNI152NLin6Asym` for CIFTI grayordinates, `fsaverage`, `fsLR`) with resolution or density entities.

fMRIPrep does not choose or apply the downstream confound model, temporal filter, censoring or smoothing; those belong to downstream records. Treat its boilerplate as runtime evidence to verify, not a complete methods section [F2].

## AFNI, FSL, SPM and custom workflows

For AFNI keep the generated `proc` script, `afni_proc.py` command, run output, executed version, X-matrix (`X.xmat.1D`), censor files, `3dREMLfit` or `3dDeconvolve` outputs, `3dClustSim`/`3dFWHMx` outputs where used, and QC (e.g., APQC HTML). Joint projection and censor mode must reflect what ran, not the presence of an option [A1, A2].

For FSL keep the executed `design.fsf`, `design.mat`/`design.con`, FEAT/FLAME logs, `randomise` commands and outputs. For SPM keep `SPM.mat` (design, filter, `xVi` autocorrelation settings, contrasts) and the batch job. For any pipeline, a package name and version without the fitted specification is incomplete evidence. Do not import COBIDAS Appendix C descriptions as current defaults.

For R, Python or other custom stages save the resolved model specification, ordered column names, matrix dimensions and rank, events/confounds/censor membership, contrasts, estimator and covariance settings, scaling and output manifest. For multivariate work save sample and feature identities, split manifest, fit boundaries of each transform, fitted hyperparameters, metrics and inference. Verify installed APIs; do not invent export functions. A provider-neutral stage handoff can be as small as:

```json
{
  "analysis_revision": "primary-v3",
  "scope_id": "analysis-main",
  "inputs_manifest": "analysis/primary-v3/inputs.json",
  "resolved_specification": "analysis/primary-v3/specification.json",
  "execution_receipt": "analysis/primary-v3/receipt.json",
  "outputs_manifest": "analysis/primary-v3/outputs.json",
  "qc_decisions": "analysis/primary-v3/qc-decisions.json"
}
```

These names are a proposal; map existing equivalents instead of renaming them.

## Agent contribution and privacy

Record the tool surface and the model identifier the host exposes, skill/code version, delegated task, code generation versus direct decisions, material human review and consequential choices. Never substitute a marketed model name for an exact version. Keep summaries and approved artifacts, not private reasoning.

Separate local execution from remote model context. Record the approved data boundary and any permitted outbound material at an aggregate level; keep secrets and identifiers out of the ledger. This skill does not grant data-processing authorization; the project's policy and approvals do.

## Project reminder

Skills are selected by task matching, not by lifecycle hooks. A short project instruction keeps checkpoints durable across sessions; the skill's [README](../README.md) supplies one. Do not paste this skill's checklists into project instruction files.
