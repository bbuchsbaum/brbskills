# fMRIPrep knowledge: decisions and consequences

## Authority and version drift

Use the selected executable/image's `--version` and `--help`, plus matching
versioned documentation and release notes. The stable usage page inspected on
2026-09-28 identifies its CLI as 25.2.5; this is a documentation observation, not
an instruction to upgrade or a claim that all sites provide that version.

Examples on otherwise authoritative pages may refer to older releases. [S1, S9]

For a new cohort, propose a pinned 25.2.x image: 25.2.0 is a long-term-support
release planned to October 2029. 25.1.x interpolation introduced artifacts in some
datasets (fixed in 25.2.0), so review 25.1.x outputs before reuse. Do not mix
fMRIPrep versions within one cohort's derivatives without an approved revision.
Version-dependent behavior below is marked with the release that introduced it. [S13]

## Inputs and preprocessing

Routine input is valid BIDS with anatomical and BOLD data; anatomical-only and
reuse modes need their own checks. fMRIPrep adapts to inputs rather than accepting
a manually specified sequence of every preprocessing step. Inspect the actual
report to determine what happened. [S1, S4]

STC requires usable timing metadata; absent SliceTiming is not proof of
simultaneous slice acquisition. Record the applied slice-time reference for the
downstream temporal model. Do not substitute a guessed interleaving order.
fMRIPrep skips STC only when SliceTiming is absent or `--ignore slicetiming` is
given; a run with fewer than five volumes left after dummy scans fails in STC
rather than skipping it. The default `--slice-time-ref` is 0.5.
Nonsteady-state handling is not permission to physically delete initial volumes;
`--dummy-scans N` overrides automatic detection for every run in the invocation.
Verify time-series/confound lengths and preserve the downstream exclusion plan.
The ordinary preprocessed BOLD output should not be described as already
nuisance-regressed, censored, or smoothed for statistical analysis. [S1, S4–S6, S13]

## Spatial products

A template identity and its sampling grid are distinct. MNI152NLin6Asym and
MNI152NLin2009cAsym are not interchangeable labels. `res-2` selects a template
resolution index, not universally a 2-mm voxel size. Verify TemplateFlow metadata
or headers. Output sampling resolution does not set registration resolution.
Request only needed representations; extra standard spaces can add work/storage.

`T1w` is the generated anatomical reference, not necessarily an original T1w
file's exact grid. Native BOLD and surface-native are different products.
`fsnative` denotes a surface output, not a volumetric native-space synonym.
Omitting `--output-spaces` yields `MNI152NLin2009cAsym` on the native BOLD grid
(`res-native`, not 2 mm) and no `T1w` BOLD series. Passing the option with no
values produces no resampled BOLD outputs. [S2, S4, S13]

## Anatomy and FreeSurfer

Choose a documented anatomical-reference strategy for repeated sessions. In
≥25.2, `--subject-anatomical-reference` takes `first-lex` (default), `unbiased`
(formerly `--longitudinal`, deprecated, removal slated for 26.1) or `sessionwise`;
`--session-label` selects sessions. 25.2.x appends session IDs to FreeSurfer
subject IDs (`sub-01_ses-pre`), so a reconstruction made by an earlier release may
not be matched and can be redone; 25.2.5 added `--no-track-sessions` to restore the
older naming (not for `sessionwise`; an argparse error on 25.2.0–25.2.4).
Confirm the expected FreeSurfer subject ID before reuse, and recheck
`--bids-filter-file` session filters written for older releases. Do not split
sessions into racing reconstructions of one shared subject directory. [S1, S4, S13]

Disabling reconstruction can change mask refinement and registration paths (BBR
via FSL FLIRT instead of `bbregister`), not merely omit surface files; surface and
CIFTI outputs require it. Existing reconstructions may be resumed and modified;
a directory's existence is insufficient proof of compatibility or completion.
Check source anatomy, version, naming, registration frames, and exclusive ownership.
With the BIDS output layout the default subjects directory is
`<output>/sourcedata/freesurfer` (the help text's `OUTPUT_DIR/freesurfer` is the
legacy layout). fMRIPrep resumes an existing reconstruction and runs any missing
recon-all steps; `--fs-no-resume` (≥24.0, expert) imports it without resuming.
A valid FreeSurfer license is always required, including with `--fs-no-reconall`:
fMRIPrep checks `--fs-license-file`, then `$FS_LICENSE`, then
`$FREESURFER_HOME/license.txt`, inside the runtime. FIPS mode is fatal. [S4, S13]

## SDC

Let the selected fMRIPrep/SDCFlows stack discover supported estimators from valid
metadata; independently audit expected versus reported per-run coverage. A
fieldmap directory is not proof that every BOLD run is corrected. If
`B0FieldIdentifier`/`B0FieldSource` appears anywhere in the dataset, SDCFlows uses
it to the exclusion of `IntendedFor`: runs annotated only with `IntendedFor` then
get no SDC. Treat mixed annotation as a blocker to resolve, not a warning. Do not
invent associations, suppress fieldmaps, or force an estimator to make a failed
job pass. [S4]

Without a usable acquired estimator, explain the choice between approved
fieldmap-less correction and a clearly documented uncorrected result. SyN is not
an automatic, scientifically equivalent repair. `--use-syn-sdc` applies SyN only
where no fieldmap exists; bare it means `error` if SyN cannot run, `warn` continues.
`--force syn-sdc` (≥25.0; replaces deprecated `--force-syn`, removal slated for 26.0)
computes SyN *in addition* to acquired fieldmaps; do not confuse forcing with
fallback. `--force bbr|no-bbr` likewise replaces `--force-bbr/--force-no-bbr`.
Since 25.0, Jacobian weighting during unwarping is default only for PEPolar
fieldmaps (`--force fmap-jacobian` / `--ignore fmap-jacobian` override), which
changes results across that version boundary. Runtime downloads may include
templates not requested as output spaces. [S1, S2, S8, S13]

TotalReadoutTime (or source fields to derive it) must be documented for acquired
fieldmap SDC; if missing, workflow construction exits with code 65. For approved
SyN-SDC a nominal value suffices: `--fallback-total-readout-time <seconds|estimated>`
(≥25.1; `estimated` uses Philips `Estimated*` fields) is the supported route. It
applies to every estimator in the invocation, so in a mixed dataset confirm it
cannot silently supply a nominal value to acquired-fieldmap SDC. Record it as a CLI
choice, not a metadata repair. [S13]

## Advanced branches: load only when triggered

- **Multi-echo:** group echoes belonging to the same acquisition; retain echo-time
  metadata. T2*/S0 fitting uses `--me-t2s-fit-method` (`curvefit` default,
  `loglin` lighter). ≥25.2.4 raises an error for two-echo data. Export individual
  corrected echoes (`--me-output-echos`, not produced at `--level minimal`) when a
  planned tedana workflow needs them; do not label ordinary multi-echo
  preprocessing as ICA denoising. [S1, S5, S13]
- **CIFTI/surfaces:** confirm reconstruction, surface registration, density, and
  required template assets. A request for grayordinates is not satisfied by an
  additional MNI NIfTI. [S1, S2, S5]
- **Precomputed derivatives:** distinguish formal derivative reuse
  (`--derivatives name=PATH`, ≥23.2; much improved in 25.0, which accepts earlier
  releases' derivatives and lets the last matching path win) from Nipype work-cache
  reuse. `--level minimal|resampling|full` (≥23.2; default `full`) controls what is
  written; `minimal` omits resampled BOLD and confounds. Check provenance. Prefer a
  new output namespace for changed software or science. [S1, S5, S9, S13]
- **Brain-extracted T1w, lesion, narrow FOV, special population:** inspect the
  relevant workflow documentation and images under the data-access policy. Do not
  adopt generic skull-stripping or alignment switches without a targeted pilot.
  Some requests need a different preprocessing tool rather than forced success.
  [S4]

## Flags that deserve suspicion

Old ICA-AROMA examples (removed); deprecated `--longitudinal` and `--force-*`
spellings (above); `--sloppy` in production; skip-validation without evidence; a global fixed dummy-scan count
applied to heterogeneous runs; `--ignore fieldmaps` as a troubleshooting shortcut;
`--clean-workdir` with shared concurrent work. Inspect the installed CLI instead
of memorizing spellings as timeless facts. [S1, S9, R1]
