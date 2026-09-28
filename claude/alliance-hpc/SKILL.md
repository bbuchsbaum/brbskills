---
name: alliance-hpc
description: Plans and troubleshoots Alliance/DRAC Slurm and qexec jobs on Trillium, Nibi, Fir, Rorqual, and Narval, including arrays, resource sizing, storage, and recovery.
---

# Alliance HPC

Optimize time to **validated results**, including staging, queueing, and execution.
Use the smallest sufficient allocation. Never invent access, scheduler policy, or
successful execution. This skill supplies guidance and local helpers; it does not
grant permission to connect, submit, cancel, or delete.

## Read for the current task

Resolve bundled paths relative to this skill directory. Read only the relevant
section; a diagnosis or planning request does not require a full campaign workflow.
For fMRIPrep workloads, a separately installed `fmriprep` skill owns the scientific
recipe; this skill resolves only the site execution route.

| Task | Reference |
|---|---|
| Select a cluster or verify its resource/policy profile | [systems.md](references/systems.md) |
| Prepare native submissions, arrays, packing, GPUs, or MPI | [submission.md](references/submission.md) |
| Stage data/environments, diagnose queues, recover campaigns | [operations.md](references/operations.md) |
| Use `qexec.sh` or interpret its results | [qexec.md](references/qexec.md) |
| Check provenance, refresh a claim, resolve conflicting documentation | [sources.md](references/sources.md) |

## Establish the execution context

Start with the requested workload, target cluster, available measurements, and
existing campaign profile. For missing or stale cluster evidence, run
`bash scripts/probe.sh /absolute/workdir` on the target login host through an
authorized connection. Keep its output private and retain a short selected-profile
summary. Exit 2 means incomplete evidence; the probe cannot establish every policy.

Before submission, verify the account, partition/QOS if needed, resource envelope,
walltime/concurrency limits, input/output paths, pinned environment, and retry
budget. Resolve only gaps relevant to the proposed action. The references record
a **2026-09-21 baseline**; current site policy and scheduler configuration govern.

**Trillium CPU differs:** whole-node allocation, baseline 192 cores, no memory
flags in the starter recipe, submission from scratch, and no local disks. Its GPU
subcluster has a separate scheduler/profile. Nibi, Fir, Rorqual, and Narval use
shared-node CPU sizing; request CPUs and memory explicitly. Read the selected
profile before relying on hardware, network, or storage assumptions.

## Prepare, execute, and verify

- Reuse trustworthy measurements or run a scheduled representative pilot. Measure
  runtime, peak memory, scaling, and output validity. Heavy analysis, builds, and
  unpacking belong on scheduled resources.
- For process pools, use one task with explicit worker and library-thread counts:
  `workers × threads ≤ allocated CPUs`. Budget private heaps and buffers. Multiple
  nodes do not combine RAM or distribute an ordinary process. See the submission
  recipes for MPI and packing.
- Freeze scripts, manifests, inputs, and environment. Create logs before submitting;
  inspect inherited `SBATCH_*` settings. Check shell syntax and use
  `sbatch --test-only` when supported. A failed preflight stops submission.
- Record submission intent and the returned `(cluster, job_id)` immediately.
  Reconcile ambiguous responses against queue/accounting before retrying. Use
  bounded arrays or packed work; retry only failed or absent units within budget.
- Require terminal accounting, successful exits, expected outputs, and application
  checks for every array element. `qexec --wait` is not a success assertion. Publish
  validated results before cleanup; preserve diagnostics on failure.

Use approved transfer/automation services and respect MFA and host keys. Scratch
is disposable: keep authoritative results and controller state on durable storage.
Do not evade purge, expose secrets in logs, race duplicate cross-cluster jobs, or
cancel/delete resources outside the authorized scope.

For a plan, provide the proposed resource shape and unresolved evidence. For an
execution handoff, persist cluster/account, job IDs, frozen inputs/environment,
output/log paths, validated and failed units, and next action. Distinguish
**planned / submitted / running / validated / failed**; scheduler completion alone
does not validate results.
