# Plan and execution protocol

Use lightweight local files and the packages' native execution primitives.
This is not a new distributed workflow engine. Local in-process execution is
the reference route; future/Slurm is optional.

## Authoritative objects

A plan envelope has `schema_version`, `analysis_id`, `scope`, `stage_configs`,
`decisions`, `checks`, `fingerprints`, `budget`, `data_policy`, and `approval`.
`stage_configs` points to or summarizes reviewed native code; it is not a promise
that arbitrary JSON can be compiled automatically into any fMRI model. Store
code/formulas as explicitly reviewed analysis artifacts, not executable BIDS
metadata. `workbench.py init` creates a blocked starter plan; `validate` explains
missing decisions/checks. Edit with normal version control or structured scripts.

Before sealing, hash the actual inventory/selected immutable inputs, code,
package/environment lock and resolved preferences; use content hashes or object
versions, not only mtime. With large immutable repositories record their stable
object checksums instead of rehashing terabytes every stage. The helper's `seal`
command hashes explicitly supplied local files and records their paths. Include
all material dependencies; it cannot discover undeclared ones automatically.

`approve` records the selected stage, digest, timestamp and user evidence. `check`
verifies the stage digest and rehashes listed files before a launch. One scientific
plan can delegate subsequent bounded stages without repeated approval, but
results-dependent changes to cohort, contrasts, nuisance or inference need a
revised plan/approval. Any changed sealed file invalidates the record. Approval
records are ordinary local files, not signed access-control capabilities.

## Stages

Discovery -> proposed plan -> design validation -> pilot -> approved execution ->
QC -> optional group -> report. This is a dependency graph, not an itinerary:
existing valid estimates enter at group, existing maps enter at reporting, and
first-level requests stop before group. Native preflight and pilot checks are
required for real cohort fits even when the helper's envelope is valid.

A pilot samples distinct acquisition/design strata, not merely the first subject.
Estimate memory/runtime empirically, check design/contrast/noise behavior, and
freeze a resource budget before full fan-out. Pilot choices must not cherry-pick
scientific findings. Use fmrireg `export_jobs()`/`run_jobs()` rather than duplicating
job serialization; a scheduler adapter only allocates and invokes native jobs.
Keep CPU workers x BLAS threads within the allocation; avoid nested oversubscription.
Do not install packages on compute workers or assume internet on compute nodes.

## Receipts and restart

Write an append-only receipt per stage/unit containing digest, input/output hashes,
start/end status, command/script path, versions, seed/threads, resources, QC links,
errors and exclusion reasons. Use temporary outputs and rename after successful
checks. Resume only units whose current dependency digest matches a completed
receipt and whose output files exist and validate. Do not overwrite partial work;
retry into a new attempt directory. Mark `partial` if any required unit failed.
A native job's success alone does not certify a scientifically valid model.

## Sharing

Separate local generation from publication. Explicit authorization must cover
what is disclosed and to whom: static image, aggregate report, recoverable group
voxels, or participant-linked data are different artifacts. Public data status
must come from an appropriate source, not the mere presence of BIDS fields.
A cloud-connected coding agent needs an allowed prompt/tool-output boundary even
when computation stays on the local filesystem.
