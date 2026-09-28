# Launch, recovery, QC, handoff

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
material acquisition/SDC/anatomical-reference branch before that branch scales.
Use full-quality processing; `--sloppy` is not a scientific qualification. Inspect
resource accounting and test the complete output/publish route. A version probe
or workflow-initialization test is not a completed pilot. [S1]

## Durable execution

The scheduler owns long jobs, not an SSH connection or an agent's conversation.
Capture a scheduler ID and submission timestamp immediately; retain stdout/stderr
and the exact script. When acknowledgement is lost, reconcile job name/token,
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
| Registration, extraction, or SDC failure | Inspect images/reports; any method change requires an approved scientific revision and pilot. |
| Interrupted job | Establish no live writer; retain compatible work and explicitly resume. |
| Lost scheduler acknowledgement | Reconcile before any new submission. |
| Work-cache/version incompatibility | Isolate the new attempt/output namespace; do not delete the only recoverable state. |

Preserve logs/crash reports. Never remove FreeSurfer IsRunning markers without
proving the owning process is gone. Do not retry indefinitely; after a verified
execution repair fails again, reassess the diagnosis. Technical retries may change
resources or location, not silently skip subjects or scientific corrections.

## Completion has several meanings

Track process exit, expected outputs, scientific QC, and durable publication
separately. An output manifest should join each selected BOLD group to exactly the
requested representations; multiple spaces/echoes must not inflate the run count.
Check loadability, image/header dimensions, confound row counts, JSON companions,
transform direction/space labels, reports, and actual observed processing choices.

Review anatomical extraction/segmentation/normalization, BOLD-to-anatomy alignment,
SDC application and artifacts, coverage/dropout, and motion summaries. Surface
requests need surface QC. Preserve the human/agent review status and unresolved
flags; a successful process is not a claim of acceptable scientific quality. Use
fMRIPrep-generated methods and citations instead of inventing a generic boilerplate.
[S4, S5]

Publish from an authorized context with checksums/manifests and controlled
permissions. Do not delete the last verified copy or retained restart state until
publication and the retention policy are satisfied. Logs/receipts must outlive
scratch cleanup even when the expensive work cache does not.

## Handoff to the downstream fMRI skill

Supply raw acquisition identity; derivative root and exact generated files;
software/recipe/execution identities; output template/grid; TR and applied temporal
reference; confounds TSV/JSON; nonsteady-state indicators; masks/transforms;
per-run observed SDC/STC; missing/failed runs; reports; and QC status. Mark ordinary
preprocessed outputs as not yet analysis-denoised, and keep downstream motion24,
filtering, censoring, and smoothing choices out of this preprocessing contract.
[S5]
