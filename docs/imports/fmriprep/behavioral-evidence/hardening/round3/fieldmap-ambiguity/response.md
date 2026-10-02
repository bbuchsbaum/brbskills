## Preprocessing plan (proposal): SDC is blocked for the affected runs

**What I'm basing this on:** only your description. You said the fieldmaps are named AP/PA, the B0 associations contradict each other, and readout metadata is missing. I have not seen the dataset, a validator report, or a run table, so everything below is a proposal. None of it is an inventory finding yet.

### What the evidence does and doesn't establish

- **The AP/PA filenames don't establish the phase-encoding axis or polarity, and they don't pair any fieldmap with any run.** Only `PhaseEncodingDirection` in the resolved sidecars does that, after inheritance.
- **The contradictory associations block SDC. They are not a warning.** If `B0FieldIdentifier`/`B0FieldSource` appears anywhere in the dataset, SDCFlows uses those tags and ignores `IntendedFor`. Any run that has only `IntendedFor` then gets no SDC, and nothing in the output says so clearly. If the two schemes point to different fieldmaps, one of them is wrong. I won't guess which.
- **Without `TotalReadoutTime`, PEPolar correction can't run.** The fallback is the source fields needed to compute it (`EffectiveEchoSpacing` plus the reconstruction matrix along the PE axis). If neither is present, fMRIPrep exits during workflow construction with code 65. I won't infer a value from the scanner vendor or protocol name.

### Proposed recipe

1. **Inventory first.** Index the raw tree with PyBIDS (inheritance resolved; `sourcedata/` and derivatives excluded) and run a local BIDS validation with the version recorded. Produce a per-run table covering: task/run/session, dimensions, voxel size, TR, number of volumes, SBRef, echoes, `SliceTiming`, `PhaseEncodingDirection`, `TotalReadoutTime` or its source fields, where each field is inherited from, and every `IntendedFor`/`B0Field*` link. Then group the BOLD runs by expected SDC coverage: valid PEPolar pair / ambiguous / none.
2. **Anatomy:** T1w reference. If the data have several sessions or several T1w images, the choice of anatomical reference needs your approval at the study level.
3. **Outputs:** `T1w` plus `MNI152NLin2009cAsym:res-2`. This is a default; I'll keep your project's spaces if you have them.
4. **FreeSurfer:** I'll use the project's existing setting. If none exists, I propose keeping reconstruction on (the default). It costs several hours per subject, but it gives surface outputs and BBR coregistration. I won't turn it off just to save time.
5. **Slice timing:** apply it where `SliceTiming` resolves. Non-steady-state volumes are detected from the data.
6. **SDC:** acquired PEPolar correction, only for runs whose association and readout metadata are documented. All other runs are held out. I won't silently fall back to SyN, force an estimator, or use `--fallback-total-readout-time`, which would apply a nominal value to every estimator in the invocation, acquired fieldmaps included.
7. **Metadata repairs:** raw data stays read-only. Any fix goes in a separate proposed patch with its source cited (protocol PDF, DICOM header, or console export). It gets applied only after you approve it, and then I re-validate.
8. **Pilot:** one full-quality subject for each acquisition branch before releasing the cohort, followed by a review of the report's SDC section. The branches are runs with a valid fieldmap, runs without one, and any runs that differ in TR, multiband, voxel size or echoes. Software version and execution target aren't set yet. Picking them doesn't block planning.

### Blocked decisions

| Decision | Blocked on |
|---|---|
| Which fieldmap corrects which BOLD run | One consistent association scheme (preferably `B0FieldIdentifier`/`B0FieldSource` everywhere), justified by acquisition records |
| Whether PEPolar SDC can run at all | Documented `TotalReadoutTime`, or its source fields, for the fieldmaps and the BOLD runs |
| Whether "AP"/"PA" are actually opposite polarities along the same axis | `PhaseEncodingDirection` values in the sidecars, checked against the protocol |
| What happens to runs that stay unresolved | Your policy: wait for a metadata fix, approve SyN-SDC for those runs (clearly labelled), or approve an uncorrected result documented as such |
| Launching the pilot or the cohort | The inventory and validation above, plus explicit launch authorization |

### Questions (the answers change what I do next)

1. Where is the BIDS root, and which system should I inventory it on? No dataset was provided here.
2. Do you have the acquisition records (protocol PDF, DICOMs, or dcm2niix JSONs straight from conversion)? Those are the evidence I need to settle both the associations and the readout time.
3. If a run can't be resolved from records, what's your policy for it: hold it out, use SyN-SDC, or leave it uncorrected?
