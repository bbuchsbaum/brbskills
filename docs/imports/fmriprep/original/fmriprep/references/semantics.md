# fMRIPrep knowledge: decisions and consequences

## Authority and version drift

Use the selected executable/image's `--version` and `--help`, plus matching
versioned documentation and release notes. The stable usage page inspected on
2026-09-28 identifies its CLI as 25.2.5; this is a documentation observation, not
an instruction to upgrade or a claim that all sites provide that version.

Defaults shown by generated help can be confusing for inverted booleans. Record
intended behavior and inspect how the selected version implements it. Examples
on otherwise authoritative pages may refer to older releases. [S1, S9]

## Inputs and preprocessing

Routine input is valid BIDS with anatomical and BOLD data; anatomical-only and
reuse modes need their own checks. fMRIPrep adapts to inputs rather than accepting
a manually specified sequence of every preprocessing step. Inspect the actual
report to determine what happened. [S1, S4]

STC requires usable timing metadata; absent SliceTiming is not proof of
simultaneous slice acquisition. Record the applied slice-time reference for the
downstream temporal model. Do not substitute a guessed interleaving order.
Nonsteady-state handling is not permission to physically delete initial volumes;
verify time-series/confound lengths and preserve the downstream exclusion plan.
The ordinary preprocessed BOLD output should not be described as already
nuisance-regressed, censored, or smoothed for statistical analysis. [S4–S6]

## Spatial products

A template identity and its sampling grid are distinct. MNI152NLin6Asym and
MNI152NLin2009cAsym are not interchangeable labels. `res-2` selects a template
resolution index, not universally a 2-mm voxel size. Verify TemplateFlow metadata
or headers. Output sampling resolution does not set registration resolution.
Request only needed representations; extra standard spaces can add work/storage.

`T1w` is the generated anatomical reference, not necessarily an original T1w
file's exact grid. Native BOLD and surface-native are different products.
`fsnative` denotes a surface output, not a volumetric native-space synonym.
An explicitly empty output-space list differs from omitting that option. [S2, S4]

## Anatomy and FreeSurfer

Choose a documented anatomical-reference strategy for repeated sessions. Current
interfaces include first-lex, unbiased, and sessionwise; older `--longitudinal`
examples must be interpreted against the installed version. Do not split sessions
into racing reconstructions of one shared subject directory. [S1, S4]

Disabling reconstruction can change mask refinement and registration paths, not
merely omit surface files. Existing reconstructions may be resumed and modified;
a directory's existence is insufficient proof of compatibility or completion.
Check source anatomy, version, naming, registration frames, and exclusive ownership.
Do not assume `--fs-no-reconall` removes every license/dependency requirement. [S4]

## SDC

Let the selected fMRIPrep/SDCFlows stack discover supported estimators from valid
metadata; independently audit expected versus reported per-run coverage. A
fieldmap directory is not proof that every BOLD run is corrected. Do not invent
associations, suppress fieldmaps, or force an estimator to make a failed job pass.

Without a usable acquired estimator, explain the choice between approved
fieldmap-less correction and a clearly documented uncorrected result. SyN is not
an automatic, scientifically equivalent repair. Verify current `--use-syn-sdc`
argument syntax and its failure policy. A force option may request extra
estimation even when fieldmaps exist; do not confuse forcing with fallback.
Runtime downloads may include templates not requested as output spaces. [S1, S2, S8]

## Advanced branches: load only when triggered

- **Multi-echo:** group echoes belonging to the same acquisition; retain echo-time
  metadata. Verify the installed release's combination/output behavior. Export
  individual corrected echoes when required for a planned tedana workflow; do not
  label ordinary multi-echo preprocessing as ICA denoising. [S1, S5]
- **CIFTI/surfaces:** confirm reconstruction, surface registration, density, and
  required template assets. A request for grayordinates is not satisfied by an
  additional MNI NIfTI. [S1, S2, S5]
- **Precomputed derivatives:** distinguish formal derivative reuse from Nipype
  work-cache reuse. Check selected-release support and provenance. Prefer a new
  output namespace for changed software or science. [S1, S9]
- **Brain-extracted T1w, lesion, narrow FOV, special population:** inspect the
  relevant workflow documentation and images under the data-access policy. Do not
  adopt generic skull-stripping or alignment switches without a targeted pilot.
  Some requests need a different preprocessing tool rather than forced success.
  [S4]

## Flags that deserve suspicion

Old ICA-AROMA examples; obsolete longitudinal/force flags; `--sloppy` used for
production; skip-validation without evidence; a global fixed dummy-scan count
applied to heterogeneous runs; `--ignore fieldmaps` as a troubleshooting shortcut;
`--clean-workdir` with shared concurrent work. Inspect the installed CLI instead
of memorizing spellings as timeless facts. [S1, S9, R1]
