# Scanner findings: meaning and false positives

Each finding has an `id`. Repeated hits are grouped under one id, with a `count`
and up to 50 example `paths`. Severity is the scanner's default. A reviewed
finding (in `findings.json`) can explain a scanner finding or contextualize it;
it never removes one.

## Dataset and files

| id | meaning | common benign cause |
| --- | --- | --- |
| `dd-missing`, `dd-invalid`, `dd-Name`, `dd-BIDSVersion` | `dataset_description.json` is missing, malformed, or lacks a required field | none; fix it |
| `readme-missing` | no README | — |
| `annex` | image files are unfetched git-annex links | a text-only clone, which is expected |
| `placeholders` | every image file is zero bytes | a skeleton dataset such as bids-examples, or an S3 text-only mirror |
| `zero-images` | some image files are zero bytes and others are not | an interrupted copy, which is a real problem |
| `json-empty`, `json-invalid` | a sidecar is empty or does not parse | a placeholder mirror (empty files only) |
| `nonbids` | a file is outside BIDS naming and not covered by `.bidsignore` | mirror artefacts such as `annex-uuid` |
| `junk` | OS junk files such as `.DS_Store` | harmless |

## Metadata (BOLD unless noted)

| id | meaning | notes |
| --- | --- | --- |
| `no-tr`, `no-taskname`, `no-ped` | a required or important key is missing after inheritance | `no-ped` is common in older datasets. Without it, fMRIPrep cannot apply fieldmap-based distortion correction |
| `tr-ms`, `te-ms` | TR or TE values look like milliseconds | a real unit error |
| `te-long` | BOLD EchoTime between 0.1 and 1 s | implausible for gradient-echo BOLD (typically 0.015–0.05 s); check the source and units |
| `st-empty` | `SliceTiming` is present but `[]` | slice-timing correction will be skipped or fail |
| `st-gt-tr` | a SliceTiming entry is ≥ TR | milliseconds (error), or a TR override at a deeper level that SliceTiming did not follow |
| `hdr-tr` | the NIfTI header TR disagrees with the sidecar | some converters write a header TR of 1 or 0. The sidecar wins in BIDS, but mention the disagreement |
| `typo-<Key>` | an unknown key is close to a known BIDS key | the intended value is effectively missing |
| `inherit-override-<Key>` | an analysis-relevant key set at a higher level is overridden lower down | legal, but often how heterogeneity hides |
| `hetero-<task>-<Key>` | TR, multiband or manufacturer varies within a task | multi-site data, or deliberate protocol changes |

## Coverage and events

| id | meaning | notes |
| --- | --- | --- |
| `fewer-runs`, `more-runs` | a subject's run count differs from the modal count for that task and session | extra runs are often repeats after a problem. Check `scans.tsv` |
| `task-missing-<task>` | the task is absent for some subjects | — |
| `ses-missing`, `ses-mixed` | sessions are unbalanced, or the layout mixes sessions with none | — |
| `task-noevents-<task>`, `task-someevents-<task>` | a non-rest task lacks `events.tsv` | events may be inherited from the top level (the scanner resolves this) or stored elsewhere |
| `events-past-end` | an event ends more than one TR after volumes × TR. Volumes come from the NIfTI header, else confounds rows, else MRIQC `size_t + dummy_trs` | some designs (e.g. BART) log trials past the scan. Explain; do not delete |
| `events-unchecked` | scan length is unknown for some runs with events | no local image, confounds or MRIQC volume count |
| `events-neg`, `events-na`, `events-empty`, `events-cols` | the events table has problems | negative onsets can mean the clock started before discarded volumes |
| `events-notype` | no `trial_type` column | the page infers conditions from the most condition-like column and names it |

## Fieldmaps and diffusion

| id | meaning |
| --- | --- |
| `intendedfor-missing` | an `IntendedFor` entry points at a file that does not exist |
| `bold-nofmap` | the dataset has fieldmaps, but this BOLD run is targeted by none (via `IntendedFor` or `B0FieldSource`) |
| `dwi-nobval` | a DWI image has no `.bval`, after inheritance |

## Derivatives (fMRIPrep)

| id | meaning | notes |
| --- | --- | --- |
| `conf-missing-<label>` | a raw BOLD run has no confounds | preprocessing failed or was skipped. Check logs and the subject report |
| `conf-noraw-<label>` | a confounds file has no raw run | a different raw dataset version, or a task excluded from raw |
| `conf-absent-<label>` | the confounds file is not fetched (zero bytes or annexed) | metrics are unavailable, not zero |
| `conf-nvols` | confounds rows ≠ header volume count | dummy scans removed, or the wrong pairing |
| `conf-naming-<label>` | camelCase and snake_case columns are mixed | versions are mixed |
| `high-motion-<label>` | runs with mean FD > 0.5 mm | a fixed screening threshold. The page's sliders define the exclusion set |
| `deriv-desc-*`, `deriv-gen-*`, `deriv-type-*` | derivative provenance is incomplete | — |

## Image quality (MRIQC)

| id | meaning | notes |
| --- | --- | --- |
| `mriqc-outlier-<metric>-<label>` | robust outlier (median/MAD > 3.5) for low tSNR, high mean FD (> 0.25 mm), high std DVARS (> 1.5) or high AQI, within task; multi-echo uses the middle echo | screening only. Repeated flags for one subject usually share one cause (motion); say so in a reviewed finding |

## Participants

`participants-missing`, `-col`, `-prefix`, `-dup`, `-notlisted` (on disk but not
listed), `-nodata` (listed but no folder), `-undoc` (a column without a
dictionary entry).
