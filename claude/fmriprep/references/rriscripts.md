# Optional rriscripts adapter

Reviewed sources, 2026-09-28: `origin/main` at `acb0a38` and the unmerged branch
`fix/fmriprep-issues-3-5` at `747775e`. `install.sh` downloads from `main`, so a
typical installed copy has no git metadata and matches `main` at install time
(`acb0a38` when reviewed), not the branch. Neither revision is a certified execution profile. The skill also
works without this repository.

## Identify the installed copy first

Locate `fmriprep_launcher.py` (`type -a`; the installer symlinks from `~/bin` into
`~/.local/share/fmriprep` unless `--bin-dir`/`--lib-dir` were given). Record its path and the SHA-256 of `fmriprep_launcher.py`,
`fmriprep_backend.py` and `fmriprep_shared.py`. Then classify it by content:

- `grep -n load_cli_base fmriprep_backend.py` and
  `grep -n no-default-config fmriprep_launcher.py` both match: branch-era code
  (fixes below present).
- Neither matches: `main`-era code. Assume the older defects below still apply.

Do not infer the revision from a directory name, install date or this reference.
With a recorded launcher profile, recompute these hashes and diff `probe` output
against the recorded values; raise the tables below only for what drifted.

## Resolve the actual interface

`fmriprep_launcher.py` is the noninteractive frontend. It consumes INI; neither
this skill's JSON records nor fMRIPrep's native config is that INI format. Do not
use `wizard`, `tui` or `gui` from an agent; they prompt interactively and write files.

```bash
fmriprep_launcher.py --help
fmriprep_launcher.py probe
fmriprep_launcher.py print-cmd --help
fmriprep_launcher.py slurm-array --help
fmriprep_launcher.py rerun-failed --help
```

Global options (`--config`, and on branch-era code `--no-default-config`) go
before the subcommand.

### Configuration layering

The loader reads, in order, `/etc/fmriprep/config.ini`,
`~/.config/fmriprep/config.ini`, `~/.fmriprep.ini`, `./fmriprep.ini` in the
**current working directory** (not the BIDS directory), then `--config`. Later
files override earlier keys, so on `main`-era code an explicit `--config` is an
overlay, never an isolated configuration. Branch-era code adds `--no-default-config`,
which reads only `--config`. `$VAR` and `~` in values are expanded on the machine
generating the script, not on the compute node. Run commands from a known
directory and record it.

`probe` prints config files in load order and "Effective config values"; save
that output. A generated bundle's `job_manifest.json` records `build_config`
(the resolved values used). Do not force `init` over a user's file.

### Defaults that change the science

Set each of these explicitly; never inherit them silently:

| Setting | Launcher behavior | Required action |
|---|---|---|
| `fs_reconall` | CLI default off, so `--fs-no-reconall` is added unless configured `true`. Project `init` writes `true`; `init --user` leaves it commented (so off). | Set to match the approved recipe. |
| `skip_bids_validation` | `fmriprep.ini.example` and `init` set `true`. | Set `false` unless a matching validator record exists. |
| `--notrack` | Always added. | Record it; consistent with default telemetry policy. |
| `cifti_output` | When true, hard-codes `--cifti-output 91k`. | Use `extra`/direct route for 170k. |
| `use_aroma` | Raises an error (removed upstream). | Remove from config. |
| `container=auto` | Singularity: newest `*.sif`/`*.simg` by mtime in `FMRIPREP_SIF_DIR` (or a directory given as `container`). Docker: first local fmriprep image, else `nipreps/fmriprep:latest`. | Always pass an explicit image file/tag and record its digest. |
| `nprocs`, `mem_mb` | Unset values come from `SLURM_*` variables or the generating host's `os.cpu_count()` and `/proc/meminfo` × 0.9, i.e. often the login node. | Always set both explicitly per subject. |
| Subjects `all` | Uses `participants.tsv` when present, else a `sub-*` directory scan. | Pass explicit labels; compare against the data inventory. |
| `fs_license` | Configured/CLI value wins; `FS_LICENSE` is used only when neither is set (the module docstring says otherwise). | Pass `--fs-license` explicitly. |

### What `print-cmd` does and does not show

`print-cmd` renders the **direct** route and joins argv with spaces without shell
quoting. Use it only to compare fMRIPrep's own application arguments with the plan;
do not paste it into a shell when paths contain spaces or metacharacters.

The Slurm batch script differs from `print-cmd` for Apptainer/Singularity: it uses
a per-subject work dir `$WORK_DIR/sub-XX`, adds `--home $SUBJECT_WORK_DIR/.home`
and `--pwd /work`, exports `*ENV_MPLCONFIGDIR` and `*ENV_NUMEXPR_MAX_THREADS`,
and picks `apptainer` versus `singularity` at run time on the compute node rather
than by host `which`. Its fmriprep-docker branch does not pass `--env`; it exports
`TEMPLATEFLOW_HOME` in the host shell. Therefore verify runtime wrapper, binds and
environment in the rendered `fmriprep_array.sbatch`, not in `print-cmd`.

The direct Singularity builder prefixes argv with `APPTAINERENV_TEMPLATEFLOW_HOME=...`
(or `SINGULARITYENV_...`) whenever TemplateFlow binding is on, which is the default
(`bind_templateflow` is not a CLI option). That is shell assignment syntax, not an
executable for `subprocess.run(argv)`. Separate env from argv; never `eval` it.

```bash
# JOB_DIR is an authorized absolute bundle directory.
fmriprep_launcher.py slurm-array --script-outdir "$JOB_DIR"
# Inspect fmriprep_array.sbatch, job_manifest.json, subjects.txt and path mappings
# before authorized submission.
```

The scheduler submission is a separate action. Persist intent before calling it.

## Revision-bound capability checks

| Interface | `main` (`acb0a38`) | Branch (`747775e`) | Consequence |
|---|---|---|---|
| Extras and CLI arrays | Batch script splits `extra` with `read -ra` (whitespace-quoted values break) and builds `CLI_BASE` at top level. When `subjects_per_job` > 1, subjects run through `xargs bash -c` (even with `parallel_subjects` = 1): Singularity/Docker children get a `%q`-escaped string expanded unquoted (escapes stay literal), and fmriprep-docker children lose `CLI_BASE` entirely (no `participant` or resource flags). | `build_common_cli` serves both routes; exported `load_cli_base` rebuilds arrays inside each child. | On `main`-era installs, avoid whitespace in extras and verify multi-subject tasks' actual argv, or use a direct script. |
| Config isolation | No `--no-default-config`. | `--no-default-config` available. | Record every file `probe` lists. |
| Compute-writability warnings | Bundle dir only. | Also warns for `--out` and `--work`. | Heuristic only; prove writes from compute. |
| fmriprep-docker image | Direct and batch branches never pass `--image`; the wrapper then uses `nipreps/fmriprep:<wrapper version>`. | Same. | `container=` does not select the image on this route; the wrapper version pins it. Use raw Docker or a direct command. |
| fmriprep-docker env | Direct builder appends `--env TEMPLATEFLOW_HOME=/path` as one token. The 25.2.5 wrapper defines `-e/--env` with `nargs=2` (`ENV_VAR value`), so this fails argument parsing. | Same. | Treat the direct fmriprep-docker route as broken when TemplateFlow binding is on. |
| TemplateFlow | Host cache (config, `TEMPLATEFLOW_HOME`, else `~/.cache/templateflow`) is bound read-write, shared by all concurrent subjects. | Same. | Prestage assets; for concurrent subjects use a fully materialized cache and verify no writes are required. |
| Module switch | Inserts `module load singularity`. | Same. | Use explicit site setup for other module names or native installs. |
| Preflight | Image/license/BIDS paths and selected config on the host. | Same. | Add compute-context proof, asset checks and pilot evidence. |
| Extra paths | Extras do not create mounts. | Same. | Map filter/config/derivative files explicitly and test container visibility. |
| Raw Docker | No host UID/GID selection. | Same. | Verify output ownership for the chosen image/site. |

Set assigned subjects B (`subjects_per_job`) and simultaneous subjects M
(`parallel_subjects`) separately; M defaults to B. `nprocs` and `mem_mb` are
per subject; `--cpus-per-task`/`--mem` are task totals (default per-subject × M).
Array concurrency is another bound, and neither array count nor exclusivity
guarantees simultaneous start or distinct nodes. Use measured site budgets from
the execution reference.

## Status markers and `rerun-failed`

Each subject writes `status/sub-X.running`, then `.ok` or `.failed` on process
exit. `.ok` means exit code 0, not output completeness or scientific QC.

`rerun-failed` reads only `*.failed`. A subject killed by time limit, OOM or node
loss keeps a stale `.running` marker; a task that died before starting a subject
has no marker. Both are silently skipped. It also skips preflight and compute-
writability warnings, always writes logs under the rerun bundle (dropping the
original `--log-dir`), and defaults to a fixed `<manifest dir>/rerun_failed_job`
that a second rerun overwrites.

Before any rerun:

1. Reconcile scheduler accounting (for Slurm, `sacct -j <job> --format=JobID,State,ExitCode,Elapsed,MaxRSS`)
   and confirm no task is still running.
2. Diff the original `subjects.txt` against `.ok` markers and existing outputs;
   the rerun set is every selected subject without verified completion, not
   only `.failed` ones.
3. Pass an explicit, new `--script-outdir` per rerun, and a subject list built
   from step 2 through `slurm-array` when `rerun-failed` would miss subjects.
4. Re-run preflight and compute-writability checks; a new manifest does not prove
   that an old writer is gone.

## Fallback and upstream work

Use the launcher only if the installed copy can express and demonstrate the
approved plan. A fallback must preserve subjects, methods, software and products,
including options inherited from configuration. Explain the specific capability
gap and emit the same logical application arguments through a direct runtime or
minimal scheduler script. Do not install rriscripts as a prerequisite.

Possible upstream improvements are explicit image forwarding for fmriprep-docker,
two-token `--env`, structured extra mounts, rerun selection beyond `.failed`, and
module setup beyond `singularity`. These are not existing commands or requirements
to modify the repository during an ordinary preprocessing task. Source pointers
and verification limits are in [sources](sources.md).
