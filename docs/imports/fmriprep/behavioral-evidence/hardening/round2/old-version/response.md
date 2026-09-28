# fMRIPrep options for the project-pinned release

The approved version stays as it is. I am not upgrading it, swapping the image, or copying in flags from the current 25.2.x docs. One limit: I don't have the exact pinned version string or that installation's `--help`. Everything below is therefore marked by which release introduced each option. Anything that depends on the version stays **proposed** until it is checked against the pinned CLI.

## Smallest blocker

Send me the pinned version and the `--help` output from that exact image or module, captured in the intended compute context. A module name or file name doesn't establish identity. With those two things I can turn this into one final argv. I'll check only whether anything has drifted since the pin was recorded. I won't redo the full setup check.

## Anatomical reference (the part that differs)

`--subject-anatomical-reference {first-lex|unbiased|sessionwise}`, `--session-label` and `--[no-]track-sessions` first appeared in **25.2**. Don't pass them to an older release. Older releases offer:

| Project intent | Pinned-release option (<25.2) | Note |
|---|---|---|
| Unbiased within-subject template across sessions | `--longitudinal` | Correct spelling for this release. (It is only deprecated in ≥25.2.) |
| That release's default multi-T1w handling | omit the flag | Confirm what the default does from that version's docs/help. It is **not** the 25.2 `first-lex` behavior. |
| One anatomical reference per session (`sessionwise`) | no native equivalent | Running each session separately with `--bids-filter-file` changes the scientific recipe, needs a separate output/FreeSurfer namespace, and requires your approval. It is not a drop-in replacement. |

FreeSurfer subject IDs in this release are not session-aware. Before any future move to ≥25.2, remember that `--track-sessions` (default on there) expects `sub-X-ses-Y`, so reconstructions from this release may not be matched and could be redone. Never let sessions run concurrent reconstructions into one shared subject directory.

## Other options to check against the pinned release

- **SDC:** `--use-syn-sdc` (fallback only where no fieldmap exists) exists across releases. Forcing SyN in addition to fieldmaps is `--force-syn` before 25.0 and `--force syn-sdc` from 25.0. The same pattern applies to `--force-bbr`/`--force-no-bbr` vs `--force bbr|no-bbr`. `--fallback-total-readout-time` is ≥25.1 only. Before 25.1, approved fieldmap-less SyN needs a documented readout-time route or stays blocked. Don't use a metadata edit to work around it.
- **Jacobian weighting:** the default changed at 25.0. On an older pin, unwarping behaves differently from current docs. Record that; don't "fix" it.
- **Reuse/levels:** `--derivatives name=PATH` and `--level minimal|resampling|full` are ≥23.2 (reuse is much weaker before 25.0). `--fs-no-resume` is ≥24.0.
- **Version-independent (still confirm in `--help`):** explicit `--output-spaces` (e.g. `T1w MNI152NLin2009cAsym:res-2`; omitting it gives MNI at native BOLD resolution and no T1w series), `--participant-label`, `-w`, `--fs-license-file`, `--nprocs`/`--omp-nthreads`/`--mem-mb` sized to the real allocation, and `--notrack` unless policy allows telemetry.
- **If the pin is 25.1.x:** that line had interpolation artifacts in some datasets (fixed in 25.2.0). I am not upgrading because of this. Review pilot outputs carefully and tell me if you want to raise it as a separate version decision.

## Draft shape (placeholders; pre-25.2 unbiased-template variant)

```
<bids> <out> participant --participant-label <01>
  -w <work> --fs-license-file <license>
  --output-spaces T1w MNI152NLin2009cAsym:res-2
  --longitudinal            # only if the project chose an unbiased template
  --nprocs <P> --omp-nthreads <O> --mem-mb <M> --notrack
```

Keep the output namespace specific to this version. Mixing fMRIPrep versions within one cohort's derivatives needs an approved revision. After the `--help` check, run one full-quality pilot for each acquisition branch before releasing the cohort. I haven't run or submitted anything.

**Decision for you:** which anatomical-reference strategy does the project use for repeated sessions: default, `--longitudinal`, or per-session (which needs approval as above)?
