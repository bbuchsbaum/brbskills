# Project reality check import — 2026-10-14

Imported at the user's request from `~/Downloads/project-reality-check.zip`.
The [original manifest](project-reality-check-original-manifest.json) records the
archive SHA-256 and hashes of all six input files. The archive supplied no license
or upstream attribution; none is inferred. The original archive is unchanged.

The canonical source is `skills/project-reality-check/`. Generated Codex and
Claude folders share the workflow, references, and evaluation fixtures; only
Codex receives `agents/openai.yaml`. No installed skill or external service is
changed by this import.

## Review

The supplied method is coherent: it distinguishes implementation from evidence,
traces the actual user workflow, seeks counterevidence, preserves useful assets,
and permits a clean review. Its scientific lens distinguishes numerical,
statistical, operational, and empirical claims without forcing every review into
a scientific audit. Four linked references provide conditional depth. There are
no executable helpers, external tool dependencies, or automatic tracker writes.

The review found no blocking defect. The imported version makes bounded edits:

- Shortens the entrypoint to 528 words, retaining scope, evidence, counterevidence,
  conditional reference routing, and completion criteria.
- Recognizes authorization from prior instructions for repairs, avoiding an
  unnecessary demand to repeat permission in the review request.
- Allows a compact report and makes counterarguments conditional on a substantive
  case, consistent with the existing architecture reference.
- Adds synthetic evaluation fixtures and cases, including a selection exclusion.

These are authoring decisions, not a demonstrated improvement over the original.
The description and Codex UI metadata are retained. No new runtime dependency or
mandatory cross-skill invocation is introduced.

## Verification

Two fresh Codex subagents received the reviewed skill and separate synthetic
projects, without this review, the assessor rubric, or the other trial's result.
The [assessor record](project-reality-check-evidence/assessment.json) binds both
outcomes to [input hashes](project-reality-check-evidence/inputs.json) and records
the limits of the command receipts. The exact model identity was not exposed by
the collaboration tool response.

- The [pilot review](project-reality-check-evidence/pilot/report.md) caught the
  documented CLI returning demo mean 2 instead of the file's mean 10 and succeeding
  on a missing file, despite three passing component tests. It preserved the
  working core and explicit file backend, respected deferred dashboard scope,
  and recommended a bounded integration fix with concrete regression gates.
- The [repeat review](project-reality-check-evidence/reviewed/report.md) exercised
  the repaired CLI and invalid-input paths, superseded the two historical blockers,
  and gave a scoped clean verdict without manufacturing more work.

Both met their bounded rubrics. Parent probes independently reproduced the
decisive behavior and component tests; all supplied skill and fixture bytes were
hash-checked after the trials. Neither trial changed the fixture trees.

These explicit-invocation trials do not establish automatic selection, a full
Codex/Claude product comparison, improvement over the original or a no-skill
baseline, scientific review quality, live tracker integration, or repair behavior.
The remaining cases in the skill's `tests/evaluation-cases.md` are unrun.

Local verification: skill-creator validation and all 24 repository unit tests
passed, as did source/bundle sync and check. Standalone package extraction and
checksum results are retained in the evidence directory. No hosted CI run is claimed.
