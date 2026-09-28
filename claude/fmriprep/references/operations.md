# Launch, recovery, QC, handoff

## Contents

- [Gates and pilot reuse](#gating)
- [Durable execution](#durable-execution)
- [Retry classification](#classify-failures-before-retry)
- [Stale FreeSurfer locks](#stale-freesurfer-locks)
- [Completion and QC](#completion-has-several-meanings)
- [Downstream handoff](#handoff-to-downstream-analysis)

## Gating

Scope approval separately: discover; prepare/download/stage; submit probe/pilot;
release the cohort; publish; clean up. A user can authorize several at once, so do
not manufacture repeated confirmations. Respect existing limits on subject count,
concurrency, destination, cost, and method changes. A request to design a skill
is not permission to execute a dataset.

Use scientific and execution fingerprints plus an attempt ID. Freeze selected
inputs, effective metadata, software, and recipe before a cohort. Hash provenance
artifacts and important small metadata; use existing content identities/checksums
for large inputs where available. File size/mtime can detect changes cheaply but
is not a content-identity proof. Record the strength of each identity mechanism.

Pilot selection follows heterogeneity, not just the first subject: include each
material acquisition branch ([defined here](bids-and-decisions.md#facts-before-questions))
and anatomical-reference strategy before that branch scales.
Use full-quality processing; `--sloppy` is not a scientific qualification. Inspect
resource accounting and test the complete output/publish route. A version probe
or workflow-initialization test is not a completed pilot. [S1]

A prior pilot can cover a new attempt when software/recipe, acquisition branch,
runtime architecture, asset identities, path access and relevant site conditions
still match. Compare recorded evidence, not a `pilot_passed` boolean. Data additions
need branch/identity checks; changed science needs a new pilot. Resource-only
changes need affected execution checks and may reuse scientific QC if coverage
remains justified. State the exact qualification scope and exceptions.

## Durable execution

The scheduler owns long jobs, not an SSH connection or an agent's conversation.
Persist submission intent/token, owner and target before invoking submission;
capture the returned scheduler ID and timestamp immediately, retaining stdout/stderr
and the exact script. A prepared intent without acknowledgment may already be
running; follow the [record reconciliation contract](records.md). When acknowledgement is lost, reconcile job name/token,
accounting, and output markers before retrying. Report UNKNOWN when evidence is
insufficient. Do not promise exact-once execution from a shell script alone.

Use subject-level ownership/locks including the recipe identity. Do not run two
attempts that write the same subject's outputs/anatomy. Parallel independent
subjects are appropriate; repeated sessions with shared anatomy require a
coordinated plan. Shared dataset-level provenance/report files also need a safe
single-writer or reconciliation strategy.

## Classify failures before retry

| Failure class | Response |
|---|---|
| Missing image/module/bind/cache/license visibility | Repair execution; preserve the recipe and rerun the preflight. |
| OOM/time limit/oversubscription | Inspect accounting; adjust allocation/concurrency within authorization and record a new execution revision. |
| Invalid metadata/ambiguous association | Block affected branch; propose an evidence-based data patch and revalidate. |
| Registration, extraction, or SDC failure | Inspect images/reports; any method change requires an approved scientific revision and pilot. Check candidate flags against [flags that deserve suspicion](semantics.md#flags-that-deserve-suspicion) and the selected version's `--help`. |
| Interrupted job | Establish no live writer; retain compatible work and explicitly resume. |
| Lost scheduler acknowledgement | Reconcile before any new submission. |
| Work-cache/version incompatibility | Isolate the new attempt/output namespace; do not delete the only recoverable state. |

Preserve logs/crash reports. See [stale FreeSurfer locks](#stale-freesurfer-locks)
before touching any `IsRunning` marker. Do not retry indefinitely; after a verified
execution repair fails again, reassess the diagnosis. Technical retries may change
resources or location, not silently skip subjects or scientific corrections.

### Stale FreeSurfer locks

recon-all refuses to start when `<subjects-dir>/<fs-subject>/scripts/IsRunning.*`
exists (`IsRunning.lh+rh`, `.lh` or `.rh`). The subjects dir defaults to
`<output>/sourcedata/freesurfer`; on fMRIPrep 25.2.x the FreeSurfer subject ID may
carry a session suffix (`sub-01_ses-pre`) unless 25.2.5's `--no-track-sessions`
was used. The marker records `SUBJECT`, `HEMI`, `USER`, `HOST`, `PROCESSID` and `DATE`. Remove it only when all hold:

1. The scheduler shows no running or pending job/attempt for that subject
   (`squeue`/`sacct` or the site equivalent), and your receipts show no live
   attempt with an unknown state.
2. If `HOST` is reachable, `PROCESSID` is not a live recon-all there; a login node
   cannot see compute-node processes, so the scheduler check carries the weight.
3. No other attempt (another session, recipe or array task) targets this FreeSurfer subject.

Then remove only that subject's `IsRunning.*` files, record the marker contents,
timestamp and evidence in the attempt receipt, and resume. Never glob across
subjects, and never delete the subject directory to clear a lock.

## Completion has several meanings

Track process exit, expected outputs, scientific QC, and durable publication
separately. The downstream handoff manifest should join each selected BOLD run to exactly the
requested representations; multiple spaces/echoes must not inflate the run count.
Check loadability, image/header dimensions, confound row counts, JSON companions,
transform direction/space labels, reports, and actual observed processing choices.

Review anatomical extraction/segmentation/normalization, BOLD-to-anatomy alignment,
SDC application and artifacts, coverage/dropout, and motion summaries. Surface
requests need surface QC. Record reviewer, inspected products, evidence locations, unresolved flags and
a pass/hold/fail decision per branch. If images/reports cannot be reviewed, QC
stays pending and cohort release for that branch remains held. Preserve the
human/agent review status; a successful process is not a claim of acceptable scientific quality. Use
fMRIPrep-generated methods and citations instead of inventing a generic boilerplate.
[S4, S5]

Publish from an authorized context with checksums/manifests and controlled
permissions. Do not delete the last verified copy or retained restart state until
publication and the retention policy are satisfied. Logs/receipts must outlive
scratch cleanup even when the expensive work cache does not.

## Handoff to downstream analysis

Write one downstream handoff manifest per derivative release, shaped like
[`assets/handoff.example.json`](../assets/handoff.example.json), with one entry per
selected BOLD run (the echoes of one multi-echo acquisition form one entry). Supply
raw acquisition identity; derivative root and exact generated files, including
masks/transforms; `scientific_id` and `execution_ids`; output template/grid; TR and
applied temporal reference; confounds TSV/JSON; nonsteady-state indicators;
per-run observed SDC/STC; missing/failed runs; reports; and a receipt-shaped `qc`
object per run. `records.py` neither fingerprints nor checks this file; identify
it by its bytes (SHA-256). Mark ordinary
preprocessed outputs as not yet analysis-denoised, and keep downstream motion24,
filtering, censoring, and smoothing choices out of this preprocessing contract.
[S5]

Supply the downstream handoff manifest whether or not `fmri-bids` or `fmri` is installed. If available,
those skills record its path and SHA-256 and consume the listed runs; their absence does not prevent
fMRIPrep preparation, execution or a standalone handoff. A downstream consumer
must check the listed missing/QC-held runs, not assume all selected runs passed.
