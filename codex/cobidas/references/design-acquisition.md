# Design and acquisition

COBIDAS Tables D.1 (experimental design) and D.2 (acquisition) are the formal checklist [C1]; BIDS defines the metadata fields used for extraction [B1, B2]. What follows is this skill's operational specification, not a transcription of the official tables.

## Participants and study design

Record aims, confirmatory/exploratory status, registration identifier/version/date, population and recruitment setting (including in/outpatient and treatment status for clinical samples), eligibility and MRI screening, diagnostic instruments and system (e.g., DSM/ICD, clinical versus inventory diagnosis) with rater reliability, group assignment, matching, and sample-size rationale. For a power analysis record the outcome it targeted (ROI, voxel-, peak- or cluster-wise), effect size and its source, alpha and correction, and target power. Record any stopping rule.

Report descriptives per analysis sample: age (mean, SD, range), sex counts, handedness with its basis (e.g., self-report, Edinburgh inventory), education/SES with instruments, and other collected measures. Distinguish sex and gender as actually collected; do not recode one as the other. For multi-group designs record scanning order relative to scanner changes or upgrades.

Maintain a participant/run flow table: approached/consented where known, scanned, usable acquisitions, excluded participants and runs with reasons, and analysed per model/contrast. Counts need units: 28 people, 56 sessions, 112 runs and 4,120 trials are not interchangeable. Overlapping exclusion reasons are not additive. Derive the analysed sample from actual model membership, not from the presence of a derivatives directory. In longitudinal studies separate attrition, missing visits, incomplete runs and model-specific complete cases.

Record the ethics body, protocol identifier, consent/assent and any secondary-use or sharing approval from documents or investigator confirmation. Public availability of data does not show that this secondary analysis was approved or exempt. Do not supply a jurisdictional conclusion.

## Task and behaviour

Record design type (block, event-related, mixed; task or rest), each condition and its stimuli, the baseline (e.g., fixation cross, blank screen), instructions (exact text in the supplement where possible), practice/training and rewards. Record trial/block counts per run (summaries if they vary by participant), trial and block durations, inter-trial interval distribution and jitter, run duration and run order, randomization or pseudo-randomization constraints, and any design-efficiency optimization. Preserve the actual timing files or generator plus seed.

Record presentation software/version and operating system, display hardware (projector, goggles, in-bore screen) and visual angle where relevant, response devices, eye tracking or physiology, and scanner synchronization (e.g., TTL trigger versus manual start). Record behavioural variables and the summaries needed to establish task engagement.

For naturalistic work preserve the exact stimulus edition/file hash, crop intervals, subtitles/transcripts, feature-extraction versions, audio/video synchronization, segmentation and annotation provenance. Record how recall events are aligned with encoding events, who or what produced the alignment, and whether alignment used the neural outcomes being evaluated. A filename is not a stimulus identity.

For rest record eyes open/closed/fixation, vigilance or sleep monitoring, duration and compliance evidence. Absence of an events file does not prove a resting-state protocol.

## Acquisition extraction

Resolve metadata per imaging file with a BIDS-aware implementation that applies the inheritance principle, retaining inherited sources and overrides [B1]. Compare acquisition signatures across all included runs. A validator report establishes the checks run by that validator version, not the truth of the metadata.

Keep original values and units beside presentation units. BIDS `RepetitionTime`, `EchoTime` and `SliceTiming` are in seconds; convert TE to milliseconds explicitly. For sparse or variable sampling retain `VolumeTiming`, `AcquisitionDuration` or `DelayTime` rather than inventing a single TR [B2]. Do not force structural-sequence timing into the fMRI definition of TR.

Per sequence record, as COBIDAS D.2 lists:

- Scanner make, model and field strength; receive coil (channel count as documented, e.g., BIDS `ReceiveCoilName`/`ReceiveCoilActiveElements`) and any nonstandard transmit coil, gradient insert or software version. Never infer coil channels from the scanner model.
- Pulse sequence (gradient/spin echo) and readout (EPI, spiral, 3D; number of shots); TE, TR, flip angle, TI where relevant, acquisition duration and number of volumes.
- FOV, acquired matrix, slice thickness and gap (2D) or 3D matrix, orientation and angulation, and coverage (whether cerebellum and brainstem are included).
- Phase-encoding direction, parallel imaging method and factor (e.g., GRAPPA/SENSE; BIDS `ParallelReductionFactorInPlane`), partial Fourier, multiband/simultaneous multislice factor (`MultibandAccelerationFactor`) and FOV shift where applicable, and readout information (bandwidth, effective echo spacing, total readout time).
- Slice order (sequential/interleaved, ascending/descending, first slice) or the full `SliceTiming` vector; with multiband, slices share acquisition times.
- Fat suppression for anatomical scans, specialized shimming, and scanner-side processing: reconstruction matrix differing from acquisition, prospective motion correction, online intensity-inhomogeneity (e.g., prescan normalize) or distortion correction.
- Field maps: type (dual-echo gradient-echo phase difference with ΔTE, direct field map, or reversed phase-encoding spin-echo/"blip-up/blip-down" pairs with their readout time) and which runs each serves (`IntendedFor`, `B0FieldIdentifier`/`B0FieldSource`). A field map's existence does not show it was applied.
- Subject preparation where used: mock scanning, special accommodations (e.g., a parent in the room for paediatric scanning).

A BIDS axis code such as `j-` is not an anatomical "posterior-to-anterior" label; converting it requires the image orientation [B2]. Record the provenance of `TotalReadoutTime`/`EffectiveEchoSpacing` (sidecar, computed, or a pipeline fallback). Do not report a resampled 2-mm derivative as a 2-mm acquisition. Keep distinct parameter sets for protocol changes, sites and echoes.

For diffusion retain b-values, shells, directions per shell and direction scheme, b=0 count, averages, single- versus dual-spin-echo, cardiac gating, b-vector coordinate convention and reversed-phase-encoding acquisitions. [structural-diffusion.md](structural-diffusion.md) covers processing. ASL and DSC perfusion have their own D.2 rows (labelling scheme, label duration, post-labelling delay, background suppression; contrast agent, dose and injection); record them from the actual protocol when present.

## Time origin accounting

Keep separate counts for scanner-discarded dummy volumes (`NumberOfVolumesDiscardedByScanner`), volumes removed before or after dataset creation (`NumberOfVolumesDiscardedByUser`), nonsteady-state volumes flagged but retained (fMRIPrep, for example, flags them in `non_steady_state_outlier_XX` columns without deleting them), and motion-censored observations. These are different operations. Identify the first stored volume and the model's time origin, and preserve the mapping from stimulus clock to BIDS event times to model frame times.

Slice-timing correction interpolates each slice to a reference time. Record that reference (slice index, time or fraction of the TR; fMRIPrep's `--slice-time-ref` is 0.5 by default in current releases) and how the model aligns to it (e.g., SPM's microtime onset `fmri_t0` relative to `fmri_t`, or a frame-time offset in nilearn). Verify whether events or the design already include an offset before applying another; avoid subtracting discarded-volume offsets twice [B2, F1].

## Acquisition QC

Record motion or image-quality checks made at acquisition, problems, exceptions and the decision rule. Separate the incidental-findings protocol from image-quality screening; a quality metric is not a clinical reading. When details cannot be retrieved, expose the gap rather than insert a conventional protocol.
