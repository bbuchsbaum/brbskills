## Diagnosis

**Inferred, not yet observed:** the probe most likely failed because it tried to write to the project tree or `$HOME` from a compute node. Those locations are writable on the login node and read-only on compute nodes. The paths at risk are `$HOME` (fMRIPrep's runtime HOME, Nipype config, and the TemplateFlow cache if it lives under HOME), plus any output, work, log or tmp directory under the project. The login-node check passed because it ran on the wrong host. Writability checked from a login shell doesn't show what a compute job can do.

This is an execution failure (the "bind/cache visibility" class). It needs a change to storage only. The scientific recipe stays exactly as it is: same inputs, fMRIPrep version and image, output spaces, FreeSurfer/SDC/STC choices, and flags. `content_id` doesn't change, so this is a new execution revision, not a new plan.

To confirm, please send the probe's stderr/log and the path it failed on (e.g. `Read-only file system` / `Permission denied` on `/home/...` or `/project/...`). If the failing path is anything other than a write target, the diagnosis changes and so does the fix below.

## Smallest repair (execution only)

Move every writable destination to compute-writable scratch. Keep read-only mounts where reads are all that's needed.

| Role | Before | After |
|---|---|---|
| BIDS input | project | unchanged, `:ro` |
| FS license | HOME/project | unchanged, `:ro` (read proof only) |
| TemplateFlow cache | `$HOME/.cache/templateflow` | unchanged, `:ro`, **if** fully materialized for this recipe; otherwise prestage it from the login node first (no downloads from compute) |
| Runtime HOME | `$HOME` | `<scratch>/fmriprep_home/<attempt>/sub-XX` via `--home` |
| tmp | node default | `-B <scratch>/tmp/<attempt>:/tmp` |
| work (`-w`) | project | `<scratch>/work/<attempt>/sub-XX` |
| output | project derivatives | `<scratch>/out/<attempt>`, then publish to the project from the login node with checksums |
| Slurm stdout/stderr | project | `<scratch>/logs/<attempt>` (create before submission); copy into the project with the receipt |

Payload shape (your existing flags stay exactly as they are; only mounts and HOME change):

```bash
export APPTAINERENV_TEMPLATEFLOW_HOME=/templateflow
apptainer run --cleanenv \
  -B <bids>:/data:ro -B <scratch>/out/<attempt>:/out -B <scratch>/work/<attempt>/sub-XX:/work \
  -B <tf_cache>:/templateflow:ro -B <fs_license>:/opt/freesurfer/license.txt:ro \
  -B <scratch>/tmp/<attempt>:/tmp --home <scratch>/fmriprep_home/<attempt>/sub-XX:/home/fmriprep \
  <same image> /data /out participant ... <unchanged recipe flags> ...
```

Before any pilot, rerun the probe **as a compute job** through the same queue, module and runtime. It should:
1. Create and delete a unique file in out, work, tmp, HOME and logs.
2. Read the inputs (following symlinks), the license and TemplateFlow files, and check that those files have real content.
3. Record the version/help of the actual image.
4. Diff the rendered scientific argv against the frozen recipe; it must match.

Record the whole thing as a new execution revision under the same plan. The last verified copy has to end up in the project, not only in scratch, and don't clear scratch work until publication is confirmed.

## What I need from you

1. The failed probe's log/error (confirms the diagnosis).
2. The approved compute-writable scratch path and its purge/quota policy. I won't guess one.
3. Whether you want me to render the probe job script for review, or to submit it too. So far only preparation is authorized; nothing has been submitted.
