# Optional rriscripts adapter

Reviewed 2026-09-30 at `origin/main` `db7a0aa`, compared with `acb0a38`.
`install.sh` downloads `main` without git metadata, so an installed copy matches
`main` at install time. No revision is a certified execution profile, and the
skill works without this repository.

## Identify the installed copy first

Locate `fmriprep_launcher.py` (`type -a`; installer default: `~/bin` symlinks into
`~/.local/share/fmriprep`). Record its path and the SHA-256 of the launcher,
`fmriprep_backend.py` and `fmriprep_shared.py`. Classify by content:

| Check | Result | Era |
|---|---|---|
| `grep -c load_cli_base fmriprep_backend.py` | `0` | **Pre-fix** (≤ `acb0a38`): read [older installs](#older-installs). |
| `grep -c 'skip_bids_validation", "false")' fmriprep_launcher.py` | ≥ `1` | **Current** (≥ `db7a0aa`): this page applies. |
| Neither of the above | — | **Unclassified** (`5524fc6`, `747775e`, `5e3f643`; late Aug–Sep 2026): inspect `--help` defaults and a rendered bundle before use. |

Classify before using era-specific flags (`--no-default-config`, `--no-*`); a
pre-fix copy rejects them. At `db7a0aa` the launcher hash is `ad10426d…97c4`; only
it identifies that revision (backend `72fb8bb5…` and shared `ca1c2aad…` are
unchanged since `5e3f643`). Never infer it from paths or dates.
With a recorded launcher profile, recompute the hashes and diff `probe` output
against the recorded values; raise the sections below only for what drifted.

## Resolve the actual interface

The launcher reads its own INI, not this skill's records or fMRIPrep's config.
Do not use the interactive `wizard`, `tui` or `gui` from an agent.

```bash
fmriprep_launcher.py --help
fmriprep_launcher.py probe
fmriprep_launcher.py print-cmd --help
fmriprep_launcher.py slurm-array --help
fmriprep_launcher.py rerun-failed --help
```

Global options (`--config`, `--no-default-config`) go before the subcommand.

### Configuration layering

The loader reads, in order, `/etc/fmriprep/config.ini`,
`~/.config/fmriprep/config.ini`, `~/.fmriprep.ini`, `./fmriprep.ini` in the
**current working directory** (not the BIDS directory), then `--config`. Later
files override earlier keys. `--no-default-config` reads only `--config`; prefer
it for an isolated, recorded configuration. `$VAR` and `~` expand on the generating
machine, not the compute node. Run from a known, recorded directory.

Save `probe` output (files in load order, "Effective config values"); a bundle's
`job_manifest.json` records `build_config`. Do not force `init` over a user's file.

### Defaults that change the science

`print-cmd`, `slurm-array` and the wizards print "fMRIPrep settings that affect
results" (container, recon-all, BIDS validation) on stderr; capture it. Still set
each of these explicitly:

| Setting | Current behavior (`db7a0aa`) | Required action |
|---|---|---|
| `fs_reconall` | On unless configured `false`; `--fs-reconall`/`--no-fs-reconall` override config (`--no-…` adds `--fs-no-reconall`). | Match the approved recipe. A config omitting the key ran without recon-all on older launchers and runs it now. |
| `skip_bids_validation` | Off unless configured `true`; `--[no-]skip-bids-validation` overrides config. | Keep off unless a matching validator record exists. Configs from `init` or the example before `db7a0aa` set it `true`; check `probe`. |
| `--notrack` | Always added. | Record it; consistent with default telemetry policy. |
| `cifti_output` | When true, hard-codes `--cifti-output 91k`. | Use `extra`/direct route for 170k. |
| `use_aroma` | Raises an error (removed upstream). | Remove from config. |
| `container=auto` or a directory | Newest `*fmriprep*.sif`/`.simg` by mtime in `$FMRIPREP_SIF_DIR` or the given directory (names the pick and skipped images). Docker: first local fmriprep image, else `nipreps/fmriprep:latest`. | Pass an explicit image file/tag and record its digest. |
| `nprocs`, `mem_mb` | Unset values come from `SLURM_*` or the generating host's `os.cpu_count()` and `/proc/meminfo` × 0.9, often the login node. | Always set both explicitly per subject. |
| Subjects `all` | `participants.tsv` when present, else a `sub-*` scan. | Pass explicit labels; compare with the inventory. |
| `fs_license` | Config/CLI value wins; `FS_LICENSE` only when neither is set (the module docstring says otherwise). | Pass `--fs-license` explicitly. |

### `print-cmd` versus the batch script

For each subject, `print-cmd` prints (each line prefixed `$ `; strip it) a
shell-quoted `mkdir` of the per-subject work directory and the command an array
task runs: same binds, `--home`, `--pwd`, container environment and argument order.
Use it to compare application arguments with the plan. It still differs from the job in four ways, so inspect the
rendered `fmriprep_array.sbatch` for these:

- The runtime binary and `APPTAINERENV_`/`SINGULARITYENV_` prefix are chosen on the
  generating host; the job chooses on the compute node.
- `module load singularity` (when enabled), status markers and `SBATCH` settings
  appear only in the job script.
- The Apptainer/Singularity line begins with `NAME=value` assignments. That is
  shell syntax, not an executable for `subprocess.run(argv)`; separate env from argv.
- Multi-subject tasks run each subject in an `xargs bash -c` child; verify one
  child's actual argv in a pilot when `subjects_per_job` > 1.

```bash
# JOB_DIR is an authorized absolute bundle directory.
fmriprep_launcher.py slurm-array --script-outdir "$JOB_DIR"
# Inspect fmriprep_array.sbatch, job_manifest.json, subjects.txt and path mappings
# before authorized submission.
```

The scheduler submission is a separate action. Persist intent before calling it.

## Route and resource cautions

| Interface | Behavior at `db7a0aa` | Consequence |
|---|---|---|
| fmriprep-docker image | Never passes `--image`; the wrapper runs `nipreps/fmriprep:<wrapper version>`. | `container=` does not select the image on this route. Use raw Docker or a direct command. |
| fmriprep-docker TemplateFlow | Exports host `TEMPLATEFLOW_HOME`; the 25.2.5 wrapper ignores it and mounts no cache. | The configured cache is unused; prove offline behavior or use another route. |
| TemplateFlow (Apptainer/Docker) | Host cache (config, `TEMPLATEFLOW_HOME`, else `~/.cache/templateflow`) bound read-write and shared by concurrent subjects. | Prestage a fully materialized cache and verify no writes are required. |
| Work directories | One per subject under `work` (Apptainer/Docker also hold `.home`, `.cache`, `.matplotlib` there). | Budget storage per subject; do not share with another run. |
| Module switch | Only `module load singularity`. | Use explicit site setup for other module names or native installs. |
| Preflight | Host checks of image, license, BIDS path and subject list; heuristic compute-writability warnings for bundle, `--out` and `--work` only when `$SCRATCH` is set. | Add compute-context proof, asset checks and pilot evidence. |
| Extra paths | `extra` is `shlex`-split; it creates no mounts. | Map filter/config/derivative files explicitly and test container visibility. |
| Raw Docker | No host UID/GID selection. | Verify output ownership. |

Set assigned subjects B (`subjects_per_job`) and simultaneous subjects M
(`parallel_subjects`) separately; M defaults to B. `nprocs` and `mem_mb` are
per subject; `--cpus-per-task`/`--mem` are task totals (default per-subject × M,
with no headroom: set `--mem` explicitly to include H from the execution reference).
Array concurrency and exclusivity guarantee neither simultaneous start nor
distinct nodes.

## Status markers and `rerun-failed`

Each subject writes `status/sub-X.running`, then `.ok` or `.failed` on process
exit. `.ok` means exit code 0, not output completeness or scientific QC.

`rerun-failed` reruns every manifest subject without `.ok`, grouped as failed,
interrupted (stale `.running`, e.g. TIMEOUT/OOM/node loss) or never started. It
refuses while `squeue` lists the original or rerun job name (no check when `squeue`
is absent; a warning when it fails), refuses to overwrite an existing rerun bundle, and accepts
`--time`/`--mem` overrides; `--allow-active` bypasses both refusals. It still skips
preflight and compute-writability warnings and writes logs inside the rerun bundle.

Before a rerun: check `sacct` states and raise `--time`/`--mem` only for recorded
TIMEOUT/OUT_OF_MEMORY; never pass `--allow-active` without establishing that no
earlier writer is live; use a new `--script-outdir` (or the next round's
`--manifest`); rerun preflight and completion checks separately. With recon-all
on, an interrupted subject may leave FreeSurfer locks; see
[stale locks](operations.md#stale-freesurfer-locks).

## Older installs

A pre-fix copy (≤ `acb0a38`) differs as follows. Prefer upgrading the launcher
(an execution change) or a direct script over working around these:

- `fs_reconall` defaults off, so `--fs-no-reconall` is added unless configured
  `true`; `fmriprep.ini.example` and `init` set `skip_bids_validation = true`.
  Both flags are plain switches with no `--no-*` forms, so a config `true` can be
  undone only by editing the file. No settings summary is printed.
- No `--no-default-config`: an explicit `--config` is only an overlay.
- The batch script splits `extra` with `read -ra` (quoted whitespace breaks).
  Singularity/Docker tasks always expand a `%q`-escaped argument string unquoted;
  with `subjects_per_job` > 1, fmriprep-docker children also lose `CLI_BASE`.
- `print-cmd` is unquoted and omits the per-subject work dir, `--home`, `--pwd` and
  environment the job uses; trust only the rendered `fmriprep_array.sbatch`.
- The direct fmriprep-docker route appends `--env TEMPLATEFLOW_HOME=/path` as one
  final token; the wrapper's `--env` takes two, so argument parsing fails.
- `rerun-failed` reads only `*.failed` (interrupted and never-started subjects are
  skipped), overwrites `<manifest dir>/rerun_failed_job`, and has no `squeue` check.
  Build the rerun set from `subjects.txt` minus verified `.ok`, via `slurm-array`.
- Compute-writability warnings cover only the bundle directory.

## Fallback and upstream work

Use the launcher only if the installed copy can express and demonstrate the
approved plan. Otherwise name the gap and emit the same logical arguments through a
direct runtime or minimal scheduler script. Do not install rriscripts as a
prerequisite or modify it during a preprocessing task. Sources: [sources](sources.md).
