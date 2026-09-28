# Preparing fMRIPrep: what your GLM plans change, and what I need next

## Your GLM choices leave the preprocessing recipe as it is

Motion24 and a B-spline baseline are first-level modelling choices. They do not
change any fMRIPrep option, so the fMRIPrep recipe stays the same.

- **Motion24.** fMRIPrep writes a per-run confounds file (`*_desc-confounds_timeseries.tsv`
  and its `.json`) by default. That file should contain the six rigid-body
  parameters plus their temporal derivatives, their squares and the squares of the
  derivatives: the 24 columns motion24 uses. You don't need a special flag for
  this. The one requirement is to keep the confounds TSV/JSON as a required
  product. Once a pilot runs, I will check that those columns are actually present
  in the version you use. I have not checked that yet.
- **B-spline baseline.** This happens entirely in the GLM, so it needs nothing from
  preprocessing. One point for later: fMRIPrep also writes `cosine_XX` high-pass
  regressors to the confounds file. If you model drift with a B-spline basis, you
  would usually leave the cosine columns out so drift isn't modelled twice. That
  decision belongs to the GLM.

The preprocessed BOLD will **not** be motion-regressed, filtered, censored or
smoothed. All of that stays downstream. The handoff manifest will list the
confounds TSV/JSON, the non-steady-state indicators, TR and the slice-timing
reference for each run, so your GLM can build motion24 and the baseline from them.

I have **not** saved "motion24 / B-spline" as a stored preference. It doesn't
affect preprocessing, and I only store reusable preferences when you ask me to.
Tell me if you want it recorded for downstream use, and whether it should apply to
this project only or to you generally.

## Proposed starting recipe (not yet checked against your data)

I haven't seen your dataset or your compute system, so this is a proposal only:

- T1w plus `MNI152NLin2009cAsym:res-2`. I will confirm the actual output grid.
- Distortion correction from acquired fieldmaps where they are validly associated
  with each run. Runs without a resolved fieldmap will be listed, not quietly given
  SyN correction.
- Slice-timing correction where the metadata supports it, and fMRIPrep's
  data-driven handling of the initial non-steady-state volumes.
- Full-quality processing, with reports and confounds.
- One representative subject as a full-quality pilot, with its output and QC
  reviewed before the rest of the cohort runs.

## What I need from you (up to three items)

1. **Where the data and the compute are.** Give me the BIDS root, and tell me
   whether fMRIPrep should run on this machine or on a cluster, and which one.
   Once I know, I will inventory the runs, anatomicals, fieldmaps and slice timing
   myself, validate the dataset, and check the fMRIPrep version/image, the
   FreeSurfer license path, mounts and scratch space from inside the real
   execution environment.
2. **Surface reconstruction (FreeSurfer).** Is there an existing project setting,
   or reconstructions you want reused? If not, I propose leaving FreeSurfer on
   (fMRIPrep's default). It adds hours per subject but gives better anatomical
   registration and a surface option later. A volumetric GLM alone doesn't decide
   this.
3. **Launch scope.** Should I prepare the pilot command and records only, or am I
   authorized to run the pilot once readiness is shown? Without your go-ahead I
   won't launch or submit anything.

## Status

| Area | Status |
|---|---|
| Scientific recipe | Proposed, not yet grounded in data |
| Data inventory and validation | Blocked: BIDS root unknown |
| Execution route | Blocked: target system unknown |
| Process, outputs, QC | Nothing has run |
| Downstream preferences | Noted for this conversation only, not saved |
