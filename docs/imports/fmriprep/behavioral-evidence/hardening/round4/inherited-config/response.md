# Effective launcher configuration: blocked, do not generate the pilot yet

**Bottom line:** As layered, the pilot would run **without FreeSurfer reconstruction** and **without BIDS validation**. Both conflict with the approved plan. Neither setting comes from your explicit INI. Both are inherited.

## Why the explicit INI doesn't protect you

`fmriprep_launcher.py` reads config files in this order: `/etc/fmriprep/config.ini`, then `~/.config/fmriprep/config.ini`, then `~/.fmriprep.ini`, then `./fmriprep.ini` (resolved from the **current working directory**, not the BIDS directory), then `--config`. A later file overrides an earlier one **only for the keys it sets**. Because your explicit INI sets only the image, every other key falls through to the inherited layers:

| Key | Winning layer | Effective value | Approved plan | Status |
|---|---|---|---|---|
| container/image | explicit `--config` | your pinned image | pinned image | OK. Record the digest. |
| `fs_reconall` | user INI | `false`, so the launcher adds `--fs-no-reconall` | reconstruction required | **Conflict.** This silently disables surfaces. |
| `skip_bids_validation` | project `./fmriprep.ini` | `true`, so the launcher adds `--skip-bids-validation` | no validator receipt exists | **Conflict.** Skipping validation needs a matching input/validator record. |
| `nprocs`, `mem_mb`, subjects, `fs_license`, TemplateFlow, output/work paths | not set explicitly | inherited, or derived from the host that generates the script (often the login node) | per plan | Unverified |

Launcher defaults and inherited settings still count as recipe choices. The launcher can't be allowed to change the approved method.

## Fix (an execution change only; the recipe stays the same)

1. **Identify the installed launcher revision.** Record the path and the SHA-256 of `fmriprep_launcher.py`, `fmriprep_backend.py` and `fmriprep_shared.py`. Then:
   - Run `grep -c load_cli_base fmriprep_backend.py`. A result of 0 means a pre-fix copy (≤ `acb0a38`).
   - Run `grep -c 'skip_bids_validation", "false")' fmriprep_launcher.py`. A result of 1 or more means a current copy (≥ `db7a0aa`).
   
   This decides whether step 2 is possible. Pre-fix copies have no `--no-default-config`, so `--config` can only ever be an overlay.
2. **Isolate the configuration.** Pass `--no-default-config --config <complete pilot INI>`, with the global options placed before the subcommand. Make that INI complete. At minimum it should contain:
   - the explicit image file, with its digest recorded
   - `fs_reconall = true`
   - `skip_bids_validation = false`
   - explicit `nprocs` and `mem_mb` per subject
   - `fs_license`
   - explicit pilot subject labels
   - output, work and TemplateFlow paths
   
   Setting `fs_reconall = true` in the file is required, because the CLI can only turn reconstruction *off* (`--no-fs-reconall`). For validation, you can also pass `--no-skip-bids-validation` as a belt-and-braces override.
   - On a pre-fix install, explicitly setting both keys in the overlay does override the inherited values. But you can't rule out other inherited keys, so upgrade the launcher or use a direct script.
3. **Keep validation on for the pilot.** Alternatively, run the validator first and record its receipt against the exact input snapshot. Only then is `skip_bids_validation = true` admissible.
4. **Prove the result before submitting.** From a recorded working directory:
   - Run `fmriprep_launcher.py --no-default-config --config <ini> probe` and save the load order and the "Effective config values".
   - Run `print-cmd` and capture the stderr block "fMRIPrep settings that affect results". The container, recon-all and BIDS validation lines must match the plan.
   - Render with `slurm-array --script-outdir <new bundle>`. Check that `job_manifest.json` → `build_config` and `fmriprep_array.sbatch` contain neither `--fs-no-reconall` nor `--skip-bids-validation`.

I don't recommend editing or deleting the project or user INIs, because they may serve other analyses. Isolation achieves the same result without touching them.

## Evidence limits

I didn't see the INI files or an installed launcher. The layer contents above come from the case description. No launcher, scheduler, container or install commands were run, and nothing was generated or submitted. Once `probe` output from the intended launcher and working directory exists, it supersedes this reconstruction.
