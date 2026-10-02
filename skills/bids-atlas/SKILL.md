---
name: bids-atlas
description: "Survey a BIDS dataset and build an interactive offline HTML dashboard: inventory, metadata oddities, events, fieldmaps, fMRIPrep confounds and motion. Use to get the lay of the land; not for validation or preprocessing."
metadata:
  version: "0.1.0"
  reviewed: "2026-10-02"
---

# BIDS atlas

Turn a BIDS tree into one self-contained HTML page that a researcher can browse:
dataset identity, a run-status ribbon, a subject × run acquisition grid, parameter
consistency after inheritance, events, fieldmap coverage, derivatives, fMRIPrep
confounds and MRIQC image-quality metrics, and motion exclusion with live thresholds
and a TSV export. fMRI gets depth; anat, dwi and fmap get summaries. The
scanner reads JSON/TSV/bval files and at most the NIfTI header; it never loads
voxel data, so a text-only clone (git-annex links unfetched) is enough.

This is exploration, not validation. Recommend the official BIDS validator for
conformance; never claim the dataset "passes".

## Build

Requires Python 3.10+ (standard library only).

```bash
python <skill-dir>/scripts/bids_atlas.py build DATASET -o atlas.html --model-out atlas-model.json
# fMRIPrep/MRIQC outputs stored outside DATASET/derivatives:
python <skill-dir>/scripts/bids_atlas.py build DATASET --derivatives /path/fmriprep -o atlas.html
```

Write output outside the dataset unless the user asks otherwise; do not modify
the dataset. Report links are relative to the location given at `build`/`scan`
time, so `render` the page into that same directory.

## Review the scanner's findings

The scanner's findings are mechanical. Add judgment before handing the page over:

1. Read the `findings` array in the model JSON and the summary counts. Open the
   few files behind each error or warning group; confirm or explain it. Read
   [findings.md](references/findings.md) for what each detector means and its
   known false-positive patterns.
2. For fMRIPrep confounds or MRIQC motion, read [confounds.md](references/confounds.md)
   before interpreting motion, CompCor, multi-echo, or naming differences across versions.
3. Write `findings.json`, a list of objects with `id`, `severity`
   (`error|warn|info`), `category`, `title`, `detail`, and `paths`, and re-render:
   `python <skill-dir>/scripts/bids_atlas.py render atlas-model.json --findings findings.json -o atlas.html`.
   The page marks these as reviewed. Use them to explain causes, to group
   symptoms with one root cause, and to say what is benign, e.g. "events past
   scan end: BART design; trials continue after the last volume". Never delete
   a scanner finding; downgrade it by explaining it.
4. Summarize for the user in chat: scale, the 3–5 problems that matter for
   analysis, and what was not checkable (unfetched images, placeholder files).

## Privacy

`participants.tsv` values are embedded only when the dataset is recognized as
OpenNeuro (`--participants auto`, the default) or the user says `--participants yes`
after confirming the data are de-identified or that the page stays on an internal
machine. Otherwise the page shows column names and missingness only. Treat
the HTML as containing whatever it embeds: do not publish or upload it without
the user's approval, and never publish one with participant values from a
non-public dataset.

## Motion sources

Motion comes from fetched fMRIPrep confounds; otherwise from MRIQC's FD, labelled as
such everywhere (MRIQC realigns separately; its spike count exists only at 0.2 mm, so
those runs are judged on mean FD alone and exported as `kept_mean_fd_only`). For
multi-echo data, MRIQC motion uses echo-1; other MRIQC metrics use one named echo.
The exported `exclusions.tsv` records thresholds, sources, criteria evaluated and
reasons for every raw run. Present thresholds as the user's choice, not a standard.

## Limits to state plainly

- Volume counts and header TRs exist only for locally present images.
- Zero-byte or annexed files are reported as unfetched, not as missing data.
- Large datasets embed decimated (peak-preserving) traces; summaries use full data.
- Detectors are heuristics; a clean page is not proof of a clean dataset.
