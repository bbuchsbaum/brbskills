Motion24 and a B-spline baseline are first-level GLM choices. They don't change the fMRIPrep recipe, so I'm leaving them out of the preprocessing plan and the handoff contract. Nothing here needs special flags for them. What they do need is for fMRIPrep to write its confounds file, which it does at the default `--level full`. So I'll keep full output and won't use `--level minimal`, which drops confounds. The confounds TSV already has the six rigid-body parameters with their derivatives and squares (`trans_x`, `trans_x_derivative1`, `trans_x_power2`, `trans_x_derivative1_power2`, and so on). Those are the columns your motion24 regressors come from later. The B-spline drift basis is built entirely in your GLM, from the TR and volume count in the handoff manifest. Outputs will be marked "preprocessed, not yet analysis-denoised".

**Proposed recipe** (a proposal until I've looked at your data and project settings):
- Outputs in `T1w` plus `MNI152NLin2009cAsym:res-2`, with confounds and reports.
- Fieldmap distortion correction wherever a valid acquired fieldmap is associated with the run. Runs without one are held and listed, not quietly switched to SyN.
- Slice-timing correction and non-steady-state handling based on the metadata.
- Full-quality processing, one participant per fMRIPrep invocation, `--notrack`.
- A pinned fMRIPrep version, checked against the image's actual `--help`.
- One pilot participant per acquisition branch (branches differ in fieldmap availability, TR, multiband, voxel size or echo count), with QC review before running the full cohort.

**What's blocking**: I don't have the dataset or the execution target yet. This workspace has no BIDS data, so I haven't inventoried anything, validated anything, built a command or submitted anything. The answers to these three questions would change what I do next:

1. Where is the BIDS dataset, and which subjects, sessions and tasks should I include?
2. Where will this run: a workstation (Docker or Apptainer) or a cluster (which site and scheduler)? And is there already an fMRIPrep image or version you want to pin?
3. Surface reconstruction: does the project already have a FreeSurfer setting? If not, I propose keeping it on (the fMRIPrep default). It adds several hours per subject, but fMRIPrep uses it for boundary-based BOLD-to-T1w registration, and turning it off changes preprocessing, not just which outputs you get.

Once I have those, I'll build the run table (fieldmap coverage, slice timing, TR, echoes), confirm or adjust the recipe, check the runtime inside the real compute context, and prepare the pilot job for your go-ahead.
