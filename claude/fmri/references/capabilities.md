# Capability verification and version drift

The repository source review is dated **2026-09-27**. It is evidence for the
examples, not a lock on your installed environment. Run `scripts/probe_capabilities.R`
for only the packages needed at the current stage. The script reports installed
versions, RemoteSha when present, exports, and selected function formals; missing
packages are explicit. It does not install anything.

Prefer installed help and source matching the installed package to current
online docs. An exported generic may have only `...`: inspect its relevant S3
method as well, with `getS3method()` / help, before calling method-specific
arguments. Inspect the public reducer/posthoc registry before selecting methods.
Treat a reexport as a public API: for example fmrireg exports baseline/design
functions implemented by fmridesign and frames from fmridataset. Do not infer
absence from a missing same-named file in fmrireg/man.

If an API differs, either adapt a small reviewed adapter and test it, or propose
an explicit environment update. Do not use triple-colon internals as a shortcut,
or silently update all packages to latest. Save `sessionInfo()`, a package lock
(such as an existing renv lock), relevant versions/commit IDs, source script
hashes, and scheduler/container details in the analysis receipt.

`workbench.py` checks its own JSON contract and selected invariants. It does not
validate every BIDS rule, establish statistical assumptions, inspect all image
headers, or implement a complete workflow engine. Use the BIDS validator,
package-native `preflight()` / `validate()` and numerical/visual QC as separate
checks. An R smoke test is a compatibility test, not validation of real data.

# Audited package front doors

| Package | Source-reviewed front doors |
|---|---|
| bidser | bids_project, query_files, get_metadata, read_events, read_confounds, confound_set, derivative_pipelines |
| fmrireg | matrix_frame, sampling_frame, event_model, baseline_model, fmri_model, fmri_lm, fmri_template, baseline_spec, as_manifest, instantiate, preflight, run_jobs |
| fmrigds | gds, as_gds, derive, reduce, compute, preview, validate, with_col_data, posthoc, write_out, examine_group |
| neuromosaic | render_montage_report, montage_interactive; report/explore CLI |

Read only the selected package's local API reference. Do not preload all four.
