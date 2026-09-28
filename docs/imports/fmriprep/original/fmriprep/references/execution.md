# Portable execution contract

## Boundary

The preprocessing skill owns scientific intent and output/QC requirements. An
execution adapter owns environment setup, path translation, scheduling, staging,
resource enforcement, and process receipts. It cannot change scientific options.

Use three ordinary JSON records, not a new orchestration service:

| Record | Contents |
|---|---|
| `plan.json` | Input snapshot/selection; scientific recipe; software identity; expected outputs; decisions and approval scope. |
| `execution.json` | Target/site; provisioner; runtime; scheduler; mount and storage contracts; resources; staged assets; observed evidence. |
| `receipt.json` | Plan/execution hashes; exact argv/env and script identities; job/attempt ID; observed version; timestamps; exits; outputs/QC/publication status. |

The included JSON is an illustrative format, not a recognized rriscripts API.
An agent can populate records and emit reviewed shell scripts without a daemon.
A future validator/compiler can adopt the same boundary without changing it.

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

When a site skill exists, ask it to **resolve and verify** the execution record for
the frozen plan. It returns setup commands, executable/runtime identity, path
mapping, resource/scheduler policy, staging/publish commands, and evidence or
blockers. It may supply a rendered job script, but it must not submit independently
unless that responsibility was explicitly delegated. Exactly one actor owns
submission/retry. It must return any limitation rather than edit the recipe.

Without a site skill, follow the same discovery and proof steps yourself using
local commands and official site documentation. Cache successful resolution by
site/node-pool, runtime/module identity, architecture, storage mappings, and policy
provenance. A cached profile is a candidate, not a permanent certification.

## Evidence levels

Record `observed`, `documented`, `inferred`, or `unknown` for each important field,
with timestamp, host/job scope, and source. Never turn unknown into false or into a
verified default. Particularly keep login-node observations distinct from compute
observations. Recheck changed software/modules, image identity, filesystem paths,
node pool, allocation policy, or cached assets.

Run `python <skill-directory>/scripts/probe_host.py` with explicit `--path role=/absolute/path` values
for a small initial inventory. It uses only the standard library and does not
submit, install, transfer, or preprocess. Executable discovery alone proves little.
Add `--versions` only to run bounded version probes. `--write-probe` tests only
explicitly designated existing writable destinations using a unique temporary
file. It rejects input-designated roles/overlaps; the caller must label paths
correctly. The helper is not a security sandbox. Its report leaves readiness unresolved.

## Prove inside the real execution context

First inspect site policy and submission mechanics; never benchmark on a login
node. With authorization, run a small probe through the same queue/module/runtime/
mount setup as the pilot. The probe must establish:

1. Actual fMRIPrep version and CLI, image/installation identity, architecture, and
   available CPU/memory allocation. A module name or file name alone is inadequate.
2. Read access to selected inputs, including resolved symlink targets, and to the
   license/assets; create/delete a unique test file in each designated output,
   work, log/status, tmp, and HOME/cache directory. Do not attempt writes in raw BIDS.
3. Correct host-to-container translation for every path-valued argument: BIDS,
   output, work, license, TemplateFlow, filters, precomputed derivatives, and any
   database/plugin configuration. Relative JSON references must resolve as intended.
4. Required template/model assets are materialized, not merely empty directories
   or unfetched DataLad/git-annex links. Derive the asset set from the selected
   release/recipe, including implicit dependencies; check usable file contents.
5. No unplanned network reliance. When compute is offline, stage assets through an
   authorized connected node and exercise workflow initialization/full pilot in
   the offline context. `--version` alone cannot prove asset completeness. [S10]

Do not require privileged network isolation as a universal probe mechanism; it
may be forbidden. Use site-approved isolation or the actual offline node, and
state the scope of the test. Do not weaken TLS validation to fix downloads.
A successful pilot covers its branch, not every heterogeneous acquisition.

## Lowering into commands

Construct one application argument vector with logical paths. Map those paths
into host or container namespaces. Apply runtime options, explicit environment,
and mounts. Finally wrap the payload in the scheduler's job script.

Apptainer/Singularity: use explicit binds, clean environment, and an intentionally
writable HOME/tmp/cache. Preserve necessary application variables via the
runtime's supported `--env` or environment-prefix mechanism; `--cleanenv` alone
does not carry arbitrary host variables through. `run IMAGE` uses the image's
runscript; `exec IMAGE fmriprep` names an executable. Verify the entrypoint. [S10, S12]

Docker: confirm daemon access and mounted filesystem visibility, preserve UID/GID
where supported, and verify output ownership. Use the chosen immutable image, not
an implicit wrapper default. With `fmriprep-docker`, inspect its own CLI and pass
the explicit image. Do not assume a wrapper's environment option performs a bind.
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
B = subjects assigned per task, and H = memory headroom. Require O <= P and M <= B.
Request at least M*P CPU slots and M*subject-memory + H memory when the site's
scheduler supports those units. Do not multiply P by O again. These are budgeting
rules, not guarantees that all external tools perfectly obey soft limits.

Bound resources by the actual allocation/cgroup/runtime limits; never infer a
per-job entitlement from `/proc/meminfo` on a login node. Whole-node sites may use
other memory directives; express the same budget through the documented policy.
Start conservatively and tune from pilot accounting. Do not hard-code a universal
memory or runtime promise.

Use separate work and HOME/cache areas per subject/recipe execution. Reuse the
same retained work area only after establishing exclusive ownership and compatible
inputs/software/arguments. Node-local scratch is ephemeral: either use retained
shared work for restartability or explicitly checkpoint/publish needed state.
Create scheduler stdout/stderr parent directories before submission. If the final
destination is not compute-writable, write to approved scratch and publish from an
authorized transfer context; the last verified copy must not exist only in scratch.

## Minimal fallback policy

Prefer a verified existing recipe, then a suitable maintained launcher, then a
small direct adapter. Scheduler absence on a login shell is not permission for a
local heavy run. Unknown accounts/quotas/permissions are blockers to resolve, not
strings to guess. A working Slurm command does not imply PBS or SGE equivalence.
