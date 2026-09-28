# Implementation and evidence — 2026-09-28

Maintained source: [skills/fmriprep](../../../skills/fmriprep/SKILL.md).
The original archive and its hashes remain unchanged. The skill is independently
packaged for Codex and Claude; neither rriscripts, Alliance nor fmri-workbench is
a runtime dependency. The optional fmri coordinator handoff now preserves the
preprocessing run/QC manifest rather than assuming analysis readiness.

## Implemented

- Task-specific routing and a compact entrypoint; seven conditional references.
- Updated rriscripts source cautions, with historical warnings distinguished from
  current inspected code and direct fallback when the wrapper cannot preserve intent.
- Small record convention and stdlib consistency checker: separate content IDs,
  approval provenance, rendered-script binding, artifact hashes, submission intent,
  and duplicate detection within the supplied receipt set. No universal compiler.
- Bounded opt-in POSIX version probes with output caps and owned-process cleanup;
  ordinary host inventory does not invoke tools, install, submit or claim readiness.
- 23 reproducible synthetic task specifications, fake runtime/scheduler fixtures,
  helper regressions, and an isolated two-product packaging regression.
- Pilot evidence reuse, offline assets, telemetry policy, single submission owner,
  QC holds, and standalone downstream handoff.

## Independent exercises and corrections

One fresh-context Codex subagent exercised four cases, then six further cases in
that same session. It received raw prompts/fixtures and the skill, not the rubric
or intended answers. Exact model build/settings were inherited and not separately
pinned. This is bounded subagent evidence, not a fresh product session per case,
a Claude run, automatic discovery or a no-skill comparison.

Parent review found all ten responses consistent with their bounded fixtures:

- wrapper-absent and whitespace-arguments: actual fake-runtime capture vectors and
  allowlisted environment matched the approved values exactly; synthetic batch
  submission was captured for the latter.
- duplicate-subject: UNKNOWN scheduler state was queried; no submit occurred.
- metadata-inheritance: both timing arrays and inherited TR resolved correctly;
  no image validation claimed.
- module-container-wrapper: existing wrapper used once, compute proof unresolved.
- offline-assets and non-slurm: precise asset/site-interface blockers, no guessed
  entitlement or false execution claim.
- stale-approval: changed SDC recipe could not reuse old approval.
- qualified-pilot: matching evidence reusable without repeating the pilot; missing
  actual batch values remained explicit.
- unavailable-qc: output/process success did not release a QC-pending branch.

[Raw responses, captured argv and generated artifacts](behavioral-evidence/)
are retained with an [evidence manifest](behavioral-evidence/evidence-manifest.json).
Paths inside them refer to their original temporary exercise workspace. They are
historical evidence, not reusable production job scripts. Thirteen other cases
remain unrun. Code/docs were being finalized during these exercises; they are not
an immutable release-candidate certification.

A separate read-only reviewer reproduced interrupted probe-child leakage. The
cleanup finally block and finite drain repaired it; interruption/error regressions
were added. The reviewer also exposed JSON exponent overflow in metadata; finite
float parsing now rejects it. Repeated submission-token tuples are now rejected
within a supplied receipt set. The reviewer rechecked both record repairs and
reported no remaining blocker in that bounded scope. Original SIGINT experiments
were temporary and only their tool-result observations survive; the retained
[record verification](behavioral-evidence/records-review-verification.json) is
separate evidence. Do not claim retained raw SIGINT artifacts.

## Checks and limits

See [bundled validation](../../../skills/fmriprep/tests/VALIDATION.md) and the
[delivery manifest](delivery-manifest.json) binding the final source, generated
folders and ZIP files. Retained [repository test log](repository-tests.log) and
[Workbench test log](workbench-tests.log) record their actual outcomes.
During import preparation, no live BIDS validation, preprocessing, real container
or cluster qualification, installation, commit, push or hosted CI was performed. No rriscripts files were
changed. Existing unrelated edits in this working tree were preserved.

## Hardening pass — 2026-09-28 (later the same day)

Four fresh-context reviewers (fMRIPrep technical accuracy against 25.2.5 source,
helper code with runnable reproductions, rriscripts claims against `acb0a38` and
`747775e`, and behavioral cases) found no blockers but several material defects.
Each fix lane was followed by a separate adversarial verification pass, whose
further findings were also fixed.

- **Helpers:** SIGTERM/SIGHUP/SIGINT (including during process creation and handler
  install/restore) now trigger owned-group cleanup; symlink loops and deep JSON give
  structured errors; bounded record reads cover FIFOs/devices; empty argv/env values
  are allowed; receipts enforce job-ID/state rules, `(target, job_id)` uniqueness,
  whitespace-free identifiers, `process.status`, and normalized script binding.
  Real-CLI random-SIGTERM stress: 0 leaks in 600 runs (3.10/3.12/3.14), versus 3/300
  before. Helper tests: 62 (32 probe + 30 records), stable 5× on CPython 3.10.18,
  3.12.11 and 3.14.7 on macOS. Linux-only cleanup paths are verified by reasoning
  only until hosted CI runs.
- **fMRIPrep content:** B0FieldIdentifier precedence; 25.2 session semantics and
  `sub-X_ses-Y` FreeSurfer IDs (`--no-track-sessions` only from 25.2.5); invocation-wide
  `--fallback-total-readout-time`; always-required license; output-space default;
  STC skip vs. failure conditions; version floors for reuse, SDC and multi-echo flags;
  hard CLI rejections; one participant per invocation for P/M budgeting; one
  illustrative Apptainer command. Two errors introduced during revision (STC and
  track-sessions) were caught by the verification pass and corrected.
- **rriscripts:** reviewed fixes are on an unmerged branch; installed copies track
  `main`. The reference now says how to classify the installed copy, that `print-cmd`
  differs from the batch script, which launcher defaults change the science, and
  where `rerun-failed` misses subjects.
- **Behavior:** proportionality, drift-only reuse of supplied evidence, a question
  ceiling rather than quota, conditional deliverables, and a concrete
  [downstream handoff manifest](../../../skills/fmriprep/assets/handoff.example.json)
  consumed by the Workbench `fmri` skill as `fingerprints.preprocessing_handoff`.
  Three cases were added (license-leak, stale-lock, derivative-reuse).

Behavioral evidence ([hardening/](behavioral-evidence/hardening/)): round 1 ran 7
previously unrun cases on the pre-hardening skill (7 rubric passes; systematic
over-processing). Round 2 ran 9 cases on the mid-hardening skill: 3 regressions,
the 3 new cases, and 3 previously unrun cases. All 9 passed, with no critical
failures, and response length fell by about half on the regression cases. Small
wording edits and the verification-pass corrections followed round 2 and have not
been re-exercised. Across both sessions 23 of 26 cases have at least one run;
host-compute-difference, fieldmap-ambiguity and arm-host remain unrun. All runs were
single-sample Claude subagents, not product sessions, automatic discovery, a
no-skill baseline, or live compute.

## Commit review — 2026-09-28

A subsequent read-only review found a cancellation-reporting defect: the CLI
claimed a version-probe group had stopped even if cleanup timed out or failed.
The fix preserves cleanup evidence through interruption and reports complete,
incomplete (with cause), or unverified cleanup while keeping signal exit codes.
Two regression tests cover combined interrupt/cleanup failures and missing
evidence. A second bounded review found the blocker resolved.

Packaging now excludes embedded Git metadata and Python tooling caches. The
[earlier hardening manifest](hardening-manifest.json) retains the old snapshot,
including cache paths; the [delivery manifest](delivery-manifest.json) records
the reviewed source and generated packages. Historical stress, multi-version
and behavioral receipts above are not reruns of the final code. The delivery
manifest lists checks performed for this commit; no live preprocessing, cluster
qualification, or fresh product-session evaluation was added.
