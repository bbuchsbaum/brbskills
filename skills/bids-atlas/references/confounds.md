# fMRIPrep confounds: reading them across versions

Read this before interpreting the Motion & confounds section or writing reviewed
findings about it. Version boundaries below are from memory of the fMRIPrep
changelog and were not re-verified at review time. When a boundary matters, confirm it
against the dataset's own `dataset_description.json` (`GeneratedBy`) and the
fMRIPrep documentation for that version.

## File names the scanner recognises

| Generation | Confounds file | Column style |
| --- | --- | --- |
| early 1.x | `*_bold_confounds.tsv` | CamelCase: `X Y Z RotX RotY RotZ`, `FramewiseDisplacement`, `stdDVARS`, `aCompCor00`, `Cosine00`, `NonSteadyStateOutlier00` |
| about 1.4 to 20.1 | `*_desc-confounds_regressors.tsv` (+ `.json`) | snake_case: `trans_x … rot_z`, `framewise_displacement`, `std_dvars`, `a_comp_cor_00` |
| 20.2 LTS onward | `*_desc-confounds_timeseries.tsv` (+ `.json`) | snake_case, plus `c_comp_cor_*`, `w_comp_cor_*`, `motion_outlier_*`, `rmsd` |
| 24+ | same, when produced | `--level minimal` runs produce **no** confounds or preprocessed BOLD |

The page reports a derivative's naming mix. If one derivative mixes generations,
it was assembled from different runs or versions, so say so.

Run labels can differ between raw and derivatives: some versions write `run-1`
where the raw data has `run-01`. The scanner compares run numbers as integers,
so a "no matching raw run" finding is a real mismatch and not a padding artefact.

## Quantities shown

- **FD** is Power-style framewise displacement in mm, with rotations converted
  on a 50 mm sphere. The first row is `n/a` and is excluded from means. Spike
  counts use the slider threshold (default 0.5 mm, fMRIPrep's default spike
  threshold).
- **std DVARS** is standardized DVARS: about 1 for a well-behaved volume, and
  1.5 is fMRIPrep's default spike threshold.
- **Translation and rotation traces** show the realignment parameters. Translation
  is in mm and rotation in radians; the page labels each.
- **CompCor**: the JSON sidecar lists each component's `Method`, `Mask`,
  `Retained`, `VarianceExplained` and `CumulativeVarianceExplained`. By default
  fMRIPrep retains components until 50% of variance is explained, so the
  retained count varies by run. That variation is expected and not an error.
  Report retained counts and cumulative variance, not the total column count.
- **non_steady_state_outlier_XX** marks initial volumes detected as non-steady.
  Their number can differ across runs. Analyses should drop or censor them
  consistently.
- **motion_outlier_XX** are one-hot spike regressors for volumes exceeding
  fMRIPrep's FD and DVARS thresholds at run time. They are not recomputed from the
  slider.

## MRIQC as a motion source

When fMRIPrep confounds are missing or unfetched, the page uses MRIQC's `fd_mean`.
MRIQC estimates motion from its own realignment, so its mean FD differs slightly from
fMRIPrep's; the page reports the median gap where both exist. `size_t` excludes the
dummy volumes MRIQC detected (`dummy_trs`): acquired volumes are `size_t + dummy_trs`.
`fd_num`/`fd_perc` count volumes above MRIQC's FD threshold (0.2 mm by default; the
page assumes the default), so the spike criterion is evaluated for MRIQC runs only at
0.2 mm. For multi-echo runs MRIQC reports each echo separately; motion uses echo-1,
as fMRIPrep estimates head motion on the first echo.

MRIQC outlier findings are robust z-scores (median/MAD > 3.5) within task (and one
echo), with absolute floors for FD (0.25 mm) and std DVARS (1.5). They are screening
flags; open the MRIQC report before excluding a run.

## Exclusion conventions (not rules)

Common lab criteria are a mean FD above 0.2–0.5 mm, or more than 20–50% of volumes
above a spike threshold of 0.2–0.5 mm. Resting-state and connectivity work tends
toward the strict end; task GLMs with censoring tolerate more. The page's sliders
let the user pick; never present one threshold as standard. The exported
`exclusions.tsv` reflects the thresholds at the moment of export. Record those
thresholds with it.

## What the page cannot tell you

- Whether the confounds came from the same fMRIPrep run as the preprocessed
  BOLD files. Check `GeneratedBy` and the logs.
- tSNR, carpet plots or registration quality. Those need image data. Link to
  the subject's `sub-XX.html` report instead.
- Physiological noise beyond CompCor and global signals.
