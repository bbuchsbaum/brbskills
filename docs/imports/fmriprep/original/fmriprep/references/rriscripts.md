# rriscripts adapter

Reviewed repository commit: `acb0a384a8aebcf9ea3b1b57d526478ad1681dc8`.
Reinspect the installed checkout/help; this reference does not certify all revisions.

## Existing interface

`fmriprep_launcher.py` is the primary noninteractive frontend. Its shared backend
builds commands and Slurm bundles. INI is its configuration format. The installed
launcher may live in `~/.local/share/fmriprep`, with a link in `~/bin`; discover it
rather than assuming either path. [R1–R4]

```bash
fmriprep_launcher.py --help
fmriprep_launcher.py probe
fmriprep_launcher.py print-cmd --help
fmriprep_launcher.py slurm-array --help
fmriprep_launcher.py rerun-failed --help
```

Generate config only when needed; never use init's force option over a user's file
without authorization. The loader reads system, user, project, then explicit INI
files, with later values overriding earlier ones. The code can read both user-file
locations if both exist. Resolve and record the complete effective configuration;
an explicit INI is an overlay, not necessarily an isolated configuration. [R2]

Map the approved science into explicit `[defaults]` settings. Keep infrastructure
in a site-specific config/profile. Never pass the proposed JSON contract to
`--config`: this launcher accepts INI, and native fMRIPrep configuration is another
separate interface. Treat extra arguments as version-specific and audit path binds.

After effective settings are correct:

```bash
# JOB_DIR must be an approved absolute bundle location, compute-writable where required.
fmriprep_launcher.py slurm-array --script-outdir "$JOB_DIR"
# Inspect generated script, subjects.txt, manifest, and all effective paths first.
# Submit only when authorized and after environment/pilot gates are satisfied.
sbatch --parsable "$JOB_DIR/fmriprep_array.sbatch"
```

The bundle includes a subject list, Slurm script, manifest, and per-subject status
markers. `rerun-failed` uses the manifest; first reconcile markers with scheduler
state and output checks. An `.ok` marker is process success, not visual QC. [R3, R4]

For B subjects assigned to a task, explicitly set `parallel_subjects=M`; if omitted,
it follows B in this snapshot. Per-subject resource limits are distinct from task
allocation. Set array concurrency independently. Do not equate array count with
guaranteed node count or simultaneous starts. [R1, R3, R4]

## Snapshot-specific cautions

These are source-inspection findings, not a live cluster qualification.

| Area | Finding and required action |
|---|---|
| Validation | Example INI enables skip-validation. Override unless a matching validation receipt exists. |
| FreeSurfer | Configuration-generation and unset-option paths do not all imply the same reconstruction choice. Write the intended setting explicitly. |
| `fmriprep-docker` image | `build_fmriprep_command` and the Slurm wrapper branch do not pass the configured image with `-i/--image`. Do not treat `container=` as proof of pinning on this route. |
| Wrapper environment | Python builder emits `--env TEMPLATEFLOW_HOME=...`; the inspected current wrapper help expects a name and a value. Confirm wrapper syntax and actual cache visibility. |
| Argv preservation | Direct construction uses shlex parsing; the Slurm template uses `read -ra` for extras and later expands a `%q`-serialized CLI as a string. Whitespace/quoting-sensitive arguments can diverge. Test or bypass this path; do not patch with eval. |
| Child shells | The Slurm `fmriprep-docker` branch refers to CLI_BASE inside exported functions run by child Bash for batching. Bash arrays are not exported as arrays; test batched argument preservation before use. |
| Module support | The built-in module switch inserts `module load singularity`; it is not a general module recipe or a native fMRIPrep-module adapter. |
| Preflight | Backend preflight checks a few host-side paths/options, not compute-node execution, offline assets, or image identity. Add the execution-contract proof. |
| Docker ownership | Direct Docker construction does not explicitly choose host UID/GID. Verify the image/site behavior and output ownership. |
| Extra file arguments | Extras do not automatically add mounts for filter files, derivative directories, or other external paths. Resolve these explicitly. |

Do not require every launcher branch to be repaired before using the skill. Use a
verified supported route; otherwise lower the same scientific plan to a direct
runtime/job script and explain why the launcher was bypassed. [R2, R3, S1]

## Focused upstream improvements, not existing commands

Add machine-readable effective-config/capability output, a no-side-effect plan
export with argv/env separated, explicit image pinning on every route, structured
path mounts and module setup, and a shared payload renderer for print/direct/batch
execution. Add tests for whitespace paths, quoted extras, batched child processes,
config precedence, and Docker image forwarding. Keep these additions in the
launcher/backend; do not reimplement the launcher inside the skill.
