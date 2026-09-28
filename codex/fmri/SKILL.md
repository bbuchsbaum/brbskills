---
name: fmri
description: "Coordinate end-to-end task-fMRI analyses across BIDS discovery, fmrireg models, fmrigds group inference, and neuromosaic reports. Use for multi-stage analysis plans or execution, not a single-package question."
license: MIT
compatibility: Requires local filesystem access; R for package execution and Python 3.10+ for optional helpers.
metadata:
  version: "0.1.0"
  reviewed: "2026-09-27"
---

# fMRI workbench

Turn the user's scientific question into an inspectable, executable analysis.
Coordinate stages; do not replace their package APIs or load every reference.
For an isolated task, route directly to `fmri-bids`, `fmrireg`, `fmrigds`, or
`neuromosaic` and stop coordinating. Each is independently installable.

## Start with evidence

Read the [operating contract](references/operating-contract.md) when creating or
changing an analysis. Reuse approved state and preferences before asking anything.
Discover which requested stages already have valid inputs. For datasets, use
`fmri-bids` to inspect local BIDS metadata first. Raw-only data can be inventoried
but these four packages do not implement a preprocessing pipeline. If the
independent `fmriprep` skill is installed and preprocessing is requested, use it
for that stage and record its downstream handoff manifest as
`fingerprints.preprocessing_handoff` (`path`, `sha256`) in `plan.json`; fit only
runs it lists as QC-passed. Otherwise record the
preprocessing handoff and missing capability; never fit raw BOLD or install a
preprocessor implicitly. Do not assume fMRIPrep completion means analysis readiness.

When the question is open, use [events to candidate designs](references/events-to-design.md)
to infer plausible models from event tables and task documentation. Present a few
supported candidates and their unresolved meanings before the interview.

Present a compact **observed / proposed / needs your decision** summary. Resolve
the scientific question, estimand, meaningful condition labels, cohort, and
material ambiguities. Use the [adaptive interview](references/interview.md).
Default to a standard review, no more than two rounds / six material questions
when possible. Do not ask again for facts or choices already supplied. Interaction
budget never licenses fabricated metadata or unapproved scientific decisions.

## Plan, test, then execute

Save a plan envelope plus editable native R code. The [execution protocol](references/execution.md)
links plan approval to code, inputs, environment and limits. Let package-native
objects carry implementation detail: fmrireg templates/jobs and fmrigds lazy plans.
Use [artifact contracts](references/artifact-contracts.md) for handoffs. Persist
what is known, proposed, confirmed, unresolved, or blocked; do not rely on chat
history for resumption. `scripts/workbench.py --help` exposes deterministic
state, audit, and preference helpers; it is not an analysis engine.

Read and invoke only the next relevant installed stage. Do not assume automatic
cross-skill dependency installation. If a needed stage is absent, report the
missing component; already available standalone work may still proceed. Keep
parallelization subordinate to scientific dependencies. Run design checks and a
small representative pilot before approved cohort execution. Review new scientific
issues, not every reversible coding detail. Preserve partial failures.

## Remember only with consent

Use [preferences](references/preferences.md) for conditional user/project profiles.
A preference such as motion24 is not an instruction to silently omit unavailable
columns. A B-spline baseline is not a B-spline HRF. Offer to save repeated choices,
but write only after explicit consent. Protocol conflicts need an amendment.

## Finish

Deliver the requested outputs, a readable methods/decision summary, QC/failure
ledger, reproducibility information, and exact remaining limitations. Distinguish
source review, executed numerical tests, and real-data validation. Do not present
uncorrected display clusters as corrected findings or automatically exclude
influential subjects. Keep report sharing and embedded voxel disclosure explicit.
For environment differences, load [capabilities](references/capabilities.md).
