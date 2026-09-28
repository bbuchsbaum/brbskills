---
name: fmriprep
description: Plans, runs, troubleshoots, and QC-checks fMRIPrep preprocessing of BIDS data on workstations or clusters (Apptainer, Docker, Slurm), explains its options, output spaces and failures, with optional rriscripts support. Not for denoising or statistical modeling.
---

# fMRIPrep

Preserve the scientific recipe while adapting execution to the available system.
Neither rriscripts nor another skill is required. Resolve bundled paths relative
to this directory; load only the references needed for the current task.
Optional helpers need Python 3.10+; preprocessing needs a verified installation
and authorized compute access.

Match the response to the request. Raise only the boundaries that bear on the
user's actual route and next action; do not restate every caveat below.

## Choose the task

| Request | Read and do |
|---|---|
| Explain an option or output | [Semantics](references/semantics.md); check the selected version. No campaign paperwork. |
| Inspect data or propose preprocessing | [BIDS and decisions](references/bids-and-decisions.md); inventory before interviewing. |
| Prepare or run | [Execution](references/execution.md); [records](references/records.md) only when the project has no tracker of its own (otherwise map to it). |
| Use the installed launcher | [rriscripts](references/rriscripts.md); identify the installed revision and effective configuration. |
| Diagnose, resume, check QC or hand off | [Operations](references/operations.md); start from existing receipts and failures. |
| Resolve uncertain technical behavior | [Primary sources](references/sources.md), matching the selected software version. |

## Plan from evidence

Locate selected BIDS data, project policy, software, existing derivatives and
execution destination. Do not assume this machine is the target. Use established
BIDS tooling to resolve inheritance and per-run fieldmap associations. Distinguish
observed, inferred, proposed and blocked findings; never invent metadata.

Propose one recipe: selected runs, explicit spaces/grids, reconstruction,
anatomical reference, expected SDC/STC, required products, and a representative
pilot. Preserve project choices; an approved or pinned recipe already supplies
its method choices. Defaults remain proposals. Recover facts from
data and system before asking. Ask only questions whose answers change the next
action; in brief mode (the user wants a quick answer or plan) aim for one round
of at most three, a ceiling rather than a quota. Essential uncertainty still blocks
affected work. Existing applicable authorization needs no repeated confirmation;
silence grants none.

For execution work, record scientific content separately from infrastructure and
attempt evidence. Input selection, methods, software and products determine the
scientific identity (the plan's `content_id`). Resource or mount changes revise
execution only. A provider cannot silently change either the recipe or cohort to
fit a machine.

## Prove the execution route

Resolve provisioning, runtime, scheduling and storage independently. Inspect
module entrypoints: a module may already wrap a container. Prefer a faithful
maintained launcher; otherwise construct a minimal direct payload. An available
site skill (for example `alliance-hpc` on Alliance Canada clusters) can help in
this session; it is optional and does not grant access. Exactly one actor owns
submission and retry.

Inspect the actual version/help, image identity, allocation, mounts, license,
HOME/tmp/cache and required assets through the intended compute context. Host
inventory and `--version` alone do not establish readiness. Preserve argv and
environment separately; verify every path-valued argument after translation.
When a verified profile, input snapshot, authorization or pilot record is
supplied, cite it and check only what may have drifted since it was recorded;
do not re-derive the full probe list.

Within authorized scope, qualify each material acquisition branch (runs that
differ in fieldmap availability, T2w/FLAIR presence, multiband, TR, voxel size or
echo count; see [BIDS and decisions](references/bids-and-decisions.md)) with a
full-quality pilot and output/QC review before cohort release. An uncertain
submission requires reconciliation, never an immediate duplicate.

## Preserve scientific and operational boundaries

- Raw inputs stay read-only. Metadata repair needs evidence and an approved patch.
- Skip BIDS validation only with a matching input/validator record.
- No silent software upgrade, SyN substitution, surface disabling, template change,
  participant exclusion or incompatible derivative reuse. Launcher defaults count.
- Bound concurrent processes by their actual allocation; prevent overlapping
  writers to anatomy, work and outputs. Never blindly clear locks or restart state.
- Keep imaging, identifiers, licenses and sensitive logs local to authorized
  systems. Resolve network/telemetry policy; do not print license contents.
- Save reusable preferences only on explicit request, with scope and provenance.

Report process, output, QC and publication status separately. When runs complete,
deliver exact commands and evidence, methods/citations, and the downstream handoff
manifest (per run; see [operations](references/operations.md) and
`assets/handoff.example.json`). Unavailable review
stays pending. For blocked work, state the smallest actionable blocker in a line
and keep the partial plan; name the next step rather than pre-listing checks for a
target not yet known.
