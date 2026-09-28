# Portable execution contract

For record fields and hashing, read [records](records.md) when preparing artifacts.

## Boundary

The preprocessing skill owns scientific intent and output/QC requirements. An
execution adapter (whatever turns the recipe into a runnable job on a given
system: a launcher, a site skill, or your own script) owns environment setup,
path translation, scheduling, staging, resource enforcement, and process receipts.
It cannot change scientific options.

Use three ordinary JSON records, not a new orchestration service:

| Record | Contents |
|---|---|
| `plan.json` | Input snapshot/selection; scientific recipe; software identity; expected outputs; decisions and approval scope. |
| `execution.json` | Target/site; provisioner; runtime; scheduler; mount and storage contracts; resources; staged assets; observed evidence. |
| `receipt.json` | Plan/execution hashes; exact argv/env and script identities; job/attempt ID; observed version; timestamps; exits; outputs/QC/publication status. |

## Contents

- [Execution dimensions](#keep-independent-dimensions-independent)
- [Optional provider](#optional-provider-protocol) and [evidence](#evidence-levels)
- [Compute proof](#prove-inside-the-real-execution-context)
- [Command construction](#building-the-command)
- [Resource and storage budgets](#resources-and-storage)

## Keep independent dimensions independent

- **Provisioning:** module commands, preinstalled executable, or explicit image.
- **Runtime:** native process, Apptainer/Singularity, Docker, or a documented wrapper.
- **Scheduling:** local authorized workstation/allocation, Slurm, PBS, SGE, LSF,
  or another verified site interface.
- **Storage:** shared input/output, local scratch, or explicit stage-in/stage-out.

A module may supply Apptainer or may itself wrap fMRIPrep in a container. Inspect
`type -a`, module help/show, the entrypoint, and actual behavior. Do not containerize
a container wrapper a second time. A shell-visible binary does not prove daemon
access, execution rights, image compatibility, or compute-node availability.
Containers are preferred to rebuilding fMRIPrep's external dependency stack. [S3]

## Optional provider protocol

A provider is a site-specific skill or guide that resolves how to run on one
system (e.g. the `alliance-hpc` skill for Alliance Canada clusters).
When a relevant site skill is available, use it in this session to **resolve and
verify** the execution record for the frozen plan. Delegation is optional; skill
availability alone does not require another agent or imply authorization. Return
setup commands, executable/runtime identity, path mapping, resource/scheduler
policy, staging/publish commands, and evidence or blockers. It may supply a
rendered job script but does not submit unless that responsibility was explicitly
delegated; it returns limitations rather than editing the recipe.

Without a site skill, follow the same discovery and proof steps yourself using
local commands and official site documentation. Cache successful resolution by
site/node-pool, runtime/module identity, architecture, storage mappings, and policy
provenance. Reuse a cached or supplied profile by checking drift in those recorded
conditions; it is never a permanent certification.

## Evidence levels

These labels describe where a field's value came from (provenance). They differ
from the planning status of a finding (observed/inferred/proposed/blocked in SKILL.md).
Record `observed`, `documented`, `inferred`, or `unknown` for each important field,
with timestamp, host/job scope, and source. Never turn unknown into false or into a
verified default. Particularly keep login-node observations distinct from compute
observations. Recheck changed software/modules, image identity, filesystem paths,
node pool, allocation policy, or cached assets.

`python <skill-directory>/scripts/probe_host.py --path role=/abs [--versions]
[--write-probe role]` gives a bounded host inventory (capped version probes; one
temporary file in designated writable, non-input destinations). It submits nothing,
is not a sandbox, and never establishes readiness; timeout or truncation is
incomplete evidence.

## Prove inside the real execution context

First inspect site policy and submission mechanics; never benchmark on a login
node. With authorization, run a small probe through the same queue/module/runtime/
mount setup as the pilot. The probe must establish:

1. Actual fMRIPrep version and CLI, image/installation identity, architecture, and
   available CPU/memory allocation. A module name or file name alone is inadequate.
2. Read access to selected inputs, including resolved symlink targets, and to the
   license/assets; create/delete a unique test file in each designated output,
   work, log/status, tmp and writable HOME/cache destinations. A deliberately
   read-only, complete asset cache needs read proof instead. Do not write in raw BIDS.
3. Correct host-to-container translation for every path-valued argument: BIDS,
   output, work, license, TemplateFlow, filters, precomputed derivatives, and any
   database/plugin configuration. Relative JSON references must resolve as intended.
4. Required template/model assets are materialized, not merely empty directories
   or unfetched DataLad/git-annex links. Derive the asset set from the selected
   release/recipe, including implicit dependencies; check usable file contents.
5. No unplanned network reliance. Record telemetry policy and explicitly disable
   tracking with the selected release's supported control (for example `--notrack`)
   unless project policy authorizes it. Keep secrets out of environment records.
   When compute is offline, stage assets through an
   authorized connected node and exercise workflow initialization/full pilot in
   the offline context. `--version` alone cannot prove asset completeness. [S10]
6. fMRIPrep refuses an output directory equal to the BIDS directory and a work
   directory inside it, and warns when the output directory holds results from a
   different fMRIPrep version (`dataset_description.json`). Catch these before
   submission; a version warning means choosing a new output namespace. [S13]

Do not require privileged network isolation as a universal probe mechanism; it
may be forbidden. Use site-approved isolation or the actual offline node, and
state the scope of the test. Do not weaken TLS validation to fix downloads.
A successful pilot covers its branch, not every heterogeneous acquisition.

## Building the command

Construct one application argument vector with logical paths. Map those paths
into host or container namespaces. Apply runtime options, explicit environment,
and mounts. Finally wrap the payload in the scheduler's job script.

Apptainer/Singularity: use explicit binds, clean environment, an intentionally
writable HOME and tmp (bind one, e.g. `-B <scratch_tmp>:/tmp`, unless the site's
default tmp is verified adequate), and an explicit cache read/write policy. Preserve necessary application variables via the
runtime's supported `--env` or environment-prefix mechanism; `--cleanenv` alone
does not carry arbitrary host variables through. `run IMAGE` uses the image's
runscript; `exec IMAGE fmriprep` names an executable. Verify the entrypoint. [S10, S12]

Illustrative shape only (one participant, 25.2.x; placeholders in `<>`; confirm
every flag against the selected image's `--help` and the frozen recipe):

```bash
export APPTAINERENV_TEMPLATEFLOW_HOME=/templateflow
apptainer run --cleanenv \
  -B <bids>:/data:ro -B <out>:/out -B <work>:/work \
  -B <templateflow_cache>:/templateflow -B <fs_license>:/opt/freesurfer/license.txt:ro \
  -B <scratch_tmp>:/tmp --home <private_writable_home>:/home/fmriprep \
  <fmriprep_25.2.x.sif> /data /out participant --participant-label <01> \
  -w /work --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces T1w MNI152NLin2009cAsym:res-2 \
  --nprocs 8 --omp-nthreads 4 --mem-mb 30000 --notrack
```

Docker: confirm daemon access and mounted filesystem visibility, preserve UID/GID
where supported, and verify output ownership. Use the chosen immutable image, not
an implicit wrapper default. `fmriprep-docker` defaults `--image` to
`nipreps/fmriprep:<wrapper version>`, so the installed wrapper silently pins the
image; pass `--image` explicitly. Its `--env` takes two tokens (`--env NAME value`);
a single `NAME=value` token is a parse error when last and otherwise silently
consumes the next argument as its value. `-u/--user UID:GID` sets ownership.
Do not assume a wrapper's environment option performs a bind. [S14]
On Apple Silicon, explicitly check image architecture and the available execution
route; do not silently promise native performance or assume emulation. [S3, S11]

Native/module fMRIPrep: use verified host paths and the module setup in the actual
noninteractive job shell. Record loaded modules and dependency provenance. If the
installation cannot be immutably identified, document that reproducibility limit;
prefer a pinned container rather than inventing an image digest.

Keep argv arrays and environment maps separate. Render shell only at the boundary
with correct quoting, or have a tiny Python payload call `subprocess.run(argv,
env=...)`. Do not flatten arrays, reparse them with `read -a`, or use `eval`.
Compare the rendered payload's scientific arguments to the frozen recipe.

## Resources and storage

Let P = per-subject `nprocs`, O = per-process OMP cap, M = concurrent subjects,
B = subjects assigned per task (rriscripts `subjects_per_job`; the example
record's `subjects_per_task`), and H = memory headroom. Require O <= P and M <= B.
Request at least M*P CPU slots and M*subject-memory + H memory when the site's
scheduler supports those units. Do not multiply P by O again. These are budgeting
rules, not guarantees that all external tools perfectly obey soft limits.
The per-subject budget holds only with one participant per fMRIPrep invocation
(the NiPreps HPC pattern: one array task or process per subject). If one
invocation receives several participants, `--nprocs` and `--mem` are totals for
that whole invocation and are shared among its subjects. [S1, S10]

Bound resources by the actual allocation/cgroup/runtime limits; never infer a
per-job entitlement from `/proc/meminfo` on a login node. Whole-node sites may use
other memory directives; express the same budget through the documented policy.
Start conservatively and tune from pilot accounting. Do not hard-code a universal
memory or runtime promise.

Use separate work and writable HOME areas per subject/recipe execution. A
materialized read-only template cache can be shared if the runtime supports it;
prestage assets and serialize any required cache writes. Do not require a full
private template copy per subject without a reason. Reuse the
same retained work area only after establishing exclusive ownership and compatible
inputs/software/arguments. Node-local scratch is ephemeral: either use retained
shared work for restartability or explicitly checkpoint/publish needed state.
Create scheduler stdout/stderr parent directories before submission. If the final
destination is not compute-writable, write to approved scratch and publish from an
authorized transfer context; the last verified copy must not exist only in scratch.

## Minimal fallback policy

Scheduler absence on a login shell is not permission for a
local heavy run. Unknown accounts/quotas/permissions are blockers to resolve, not
strings to guess. A working Slurm command does not imply PBS or SGE equivalence.
