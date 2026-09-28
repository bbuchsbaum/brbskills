I can take this from your verified Apptainer/Slurm profile, validated snapshot and approved recipe without redoing any of them. I did not render or submit anything. This session can't see the launcher or the pilot record, so there is nothing yet to check for drift or to render.

**Evidence still needed (smallest set):**

1. **Which pilot is "next", and its authorization.** Give me the pilot record: the acquisition branch (fieldmap, multiband, TR, voxel size), the subject label(s), and the authorization scope. Also tell me whether any earlier pilot submission is unresolved. If one is, I'll reconcile it in the scheduler accounting (`sacct`) and in its status markers before preparing another, so we don't submit a duplicate.
2. **The installed launcher's identity.** I need the output of `type -a fmriprep_launcher.py` and the SHA-256 of `fmriprep_launcher.py`, `fmriprep_backend.py` and `fmriprep_shared.py`. I also need to know whether `grep -n load_cli_base fmriprep_backend.py` and `grep -n no-default-config fmriprep_launcher.py` match. That tells me whether this install has the fixes from the rriscripts `fix/fmriprep-issues-3-5` branch or is older `main` code with known defects. If this doesn't match what your verified profile recorded, the profile needs a recheck.
3. **The effective configuration.** I need the saved output of `fmriprep_launcher.py probe`, run from a known directory. The launcher also reads `./fmriprep.ini` in that directory and the files in `~`. On older `main` code there is no `--no-default-config`, so `--config` only overrides keys and every file `probe` lists still applies.

**What I'll prepare once I have those:**

- A pilot overlay that sets explicitly every launcher default that changes the science:
  - `fs_reconall` as the recipe specifies. The launcher's default adds `--fs-no-reconall`.
  - `skip_bids_validation`, which may be `true` only because your validated snapshot matches the input; otherwise `false`.
  - An explicit `.sif` path with its digest, not `container=auto`.
  - Per-subject `nprocs` and `mem_mb`, so it can't fall back to the login node's CPU/memory.
  - Explicit `--fs-license`, output spaces and an explicit participant label.
  - `cifti_output` only if the recipe wants 91k; `use_aroma` absent.
  - `--notrack` recorded.
  - `subjects_per_job = parallel_subjects = 1` for the pilot.
- Render the bundle with `fmriprep_launcher.py slurm-array --script-outdir <new pilot bundle dir>`. I'll then check `fmriprep_array.sbatch` (not `print-cmd`) for binds, `--home`, per-subject work dir, TemplateFlow env, and `--cpus-per-task`/`--mem`. I'll also check `job_manifest.json` `build_config` and `subjects.txt`, and compare the fMRIPrep arguments with the approved recipe.
- Drift checks only: image digest, output/work namespaces (a separate output directory with no results from a different fMRIPrep version), and TemplateFlow cache still materialized.
- Submission is a separate step that I'll do only after you've reviewed the rendered bundle. When the pilot finishes, `.ok` only means exit 0. The branch isn't qualified until the outputs and QC have been reviewed.

If the installed launcher can't express the recipe (for example, whitespace in extras on older `main` code), I'll say exactly what it can't do and switch to a minimal direct Apptainer script with the same arguments.
