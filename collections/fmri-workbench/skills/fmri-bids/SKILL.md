---
name: fmri-bids
description: "Inspect and audit BIDS fMRI datasets with bidser: inherited metadata, derivatives, events, confounds, and acquisition matching. Use for dataset discovery or analysis readiness; do not fit models or preprocess images."
license: MIT
compatibility: Requires local filesystem access; R for package execution and Python 3.10+ for optional helpers.
metadata:
  version: "0.1.0"
  reviewed: "2026-09-27"
---

# BIDS discovery with bidser

Produce a traceable inventory and an analysis-readiness assessment before asking
the user questions answered by files. This skill stands alone; group analysis
and first-level fitting are not required.

For a new analysis, read the [operating contract](references/operating-contract.md).
Use [capability checks](references/capabilities.md) before relying on unfamiliar
installed arguments. Read the [discovery procedure](references/discovery.md), then
use `scripts/discover_bids.R` for an initial file/metadata/header inventory. This
script is a **first pass**, not a BIDS validator or complete scientific audit.
Finish the [timing and join checks](references/timing-and-joins.md) explicitly.

## Discover cheaply, then selectively inspect

Separate raw and derivative roots, pipeline/version, file representation, task,
subject, session, acquisition, direction, run, echo, space, and resolution/density.
Use `bidser::query_files()` with explicit scope and exact entity selection.
Resolve effective metadata with `get_metadata(..., inherit=TRUE,
provenance=TRUE)` and retain its sources. Never ask for a TR already established
per acquisition; never silently take the first TR when values differ. Check
metadata against headers with units. Detect inherited events/sidecars, ambiguous
same-level sidecars, stale indexes, alternate representations, and missing files.

Inspect events and confounds locally: schema/units, timing origin, durations,
condition counts, missingness, available confound sets, rows vs volumes, and
nonsteady-state handling. Condition labels and metadata can suggest a task but
cannot establish the user's hypothesis or contrast direction. Negative onsets
and zero-duration events are not inherently invalid. Do not shift onsets merely
because metadata records volumes discarded before the stored image.

For onboarding, use [events to candidate designs](references/events-to-design.md)
to identify factors, modulators, phases and candidate contrasts from those files.
Return evidence-backed proposals and remaining questions; proposing a design
does not require fitting a model or inventing the study's primary hypothesis.

## Match by meaning, not order

Use full acquisition keys and explicit projection rules for event/confound joins.
One event file may legitimately serve several echoes; several BOLD representations
must not become extra runs or subjects. Check cardinalities and exclusions.
A mask and a space label are insufficient without grid/affine compatibility.
Report unsupported CIFTI/surface, nonuniform timing, or other adapter limits rather
than coercing data to a different representation without approval.

For the source-reviewed fmrireg importer, `from_bids()` is a convenience path,
not a universal discovery oracle: it orders by numeric run, selects the first TR,
and uses a single supplied mask. Certify its preconditions or create explicit
bindings through `as_manifest()` downstream. Do not send session/echo filters in
`...` and assume they filter scans; those arguments go to confounds.

## Handoff

Write inventory/provenance, validation states, exact selections, unresolved
scientific questions, and a concise dataset card. Use the [artifact contract](references/artifact-contracts.md).
Run the official BIDS validator locally when available and authorized; preserve
version and structured findings. Missing validator or unchecked header/joins
must remain "not checked". File discovery alone never certifies readiness.
Only ask about gaps that affect the requested scope. Read only the applicable
preference fields; do not save new preferences without explicit consent.
