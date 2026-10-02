# Next pilot through the installed launcher

You've given me a validated snapshot, a verified Apptainer/Slurm launcher profile, an approved recipe and authorization for this pilot. I won't re-run the full probe or ask you to confirm again. What's left is a drift check against the recorded profile, a rendered bundle to inspect, and then the one submission. Nothing has been run or submitted from here. The launcher lives on the cluster, and this workspace has only synthetic stand-ins.

## 1. Drift check against the recorded profile (on the submit host)

Run this from a fixed, recorded directory. A `./fmriprep.ini` in the working directory would otherwise be layered in.

```bash
cd "$RUN_DIR"                                   # record this path
type -a fmriprep_launcher.py                    # must match the profile's path
sha256sum "$LIB"/fmriprep_launcher.py "$LIB"/fmriprep_backend.py "$LIB"/fmriprep_shared.py
fmriprep_launcher.py --no-default-config --config "$PILOT_INI" probe > probe.$(date +%F).txt
diff "$PROFILE_DIR"/probe.txt probe.$(date +%F).txt
```

- **Hashes match the profile:** the launcher is the same, so nothing more to check there.
- **Hashes differ:** reclassify the install before going further. `grep -c load_cli_base` on the backend and `grep -c 'skip_bids_validation", "false")'` on the launcher tell you which version you have. Then check the defaults below again.
- **Probe diff shows changes:** look only at what changed (effective config values, image path, license, TemplateFlow cache, module setup). Re-probe inside the compute context only if the image, the module, the node pool or the storage mappings changed.
- **Snapshot:** re-hash the input snapshot, or check its recorded identity, against the validated snapshot record. The validator record lets the pilot skip BIDS validation only while the snapshot still matches.

## 2. Pilot INI (use only `--config`, never the default config chain)

Set every result-affecting default explicitly, even when the profile's value would be the same:

| Key | Value |
|---|---|
| `container` | explicit `.sif` path, same digest as the profile (not `auto` or a directory) |
| `fs_reconall` | whatever the approved recipe says (the current launcher turns it on by default) |
| `skip_bids_validation` | `true` only if the validator record matches the current snapshot; otherwise `false` |
| `fs_license` | explicit path (never print its contents) |
| `subjects` | the explicit pilot label (not `all`) |
| `subjects_per_job` / `parallel_subjects` | `1` / `1` |
| `nprocs`, `mem_mb` | explicit values from the profile (unset values come from the login node) |
| `cifti_output`, `extra` | as the recipe requires. `cifti_output` forces 91k, and `extra` creates no mounts. |
| `use_aroma` | leave it out |

`--notrack` is always added. Record it.

## 3. Render and inspect, don't submit yet

```bash
fmriprep_launcher.py --no-default-config --config "$PILOT_INI" print-cmd  2> print-cmd.settings.txt > print-cmd.txt
fmriprep_launcher.py --no-default-config --config "$PILOT_INI" slurm-array \
  --script-outdir "$JOB_DIR" 2> bundle.settings.txt   # new, empty directory
```

Check each of these against the approved recipe:

- the stderr "settings that affect results" block (container, recon-all, BIDS validation)
- `job_manifest.json` `build_config`
- `subjects.txt`, which should contain only the pilot label
- `fmriprep_array.sbatch`: the `--cpus-per-task`/`--mem`/time/partition/account values, the bind and path mappings, `--home`/`--pwd`, and the `APPTAINERENV_` variables, including TemplateFlow
- output spaces and resolutions, and that the output directory is neither the BIDS directory nor holding a different fMRIPrep version's results
- that the per-subject work directory isn't shared with any other run

Then create the log/status parent directories.

## 4. Before the single submission

- Confirm that no earlier pilot or cohort job is still writing to the same anatomy, work or output areas. Check `squeue`/`sacct` for the prior job names, plus the prior bundle's `status/*.running`. Don't clear locks or delete stale `.running` markers.
- Write down the intent (plan/content id, bundle hashes, `$JOB_DIR`) in your tracker before calling `sbatch`. Exactly one actor submits. If the submission outcome is uncertain, reconcile with `sacct` before trying again; never submit a duplicate.
- Afterwards, `status/sub-X.ok` means only that the process exited with 0. Output completeness and visual QC are separate gates before cohort release.

## Evidence I still need

1. **Which pilot is next and why:** the subject label, and the previous pilot's record: job ID, final `sacct` state, status marker and QC outcome. If the previous pilot hasn't passed QC, this isn't "next" yet.
2. **The recorded profile artifacts:** the launcher path and three hashes, the saved `probe` output, the image digest, the pilot INI (or the profile's config file) and the compute-context probe scope and date. I need these to diff against. Without them the drift check has nothing to compare to.
3. **Current values on the submit host:** today's hashes, `probe` output and image digest (step 1), and the snapshot identity check.
4. **The rendered bundle:** `fmriprep_array.sbatch`, `job_manifest.json`, `subjects.txt` and the stderr settings summary. I'll compare them line by line with the recipe.
5. **Whether any job is live** on the shared anatomy, work or output areas (step 4).

If items 3–5 show no drift and the bundle matches the recipe, the existing authorization covers submitting `fmriprep_array.sbatch` as it stands.
