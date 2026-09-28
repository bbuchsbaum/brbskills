# Proposed decision: offline assets

No. This profile cannot proceed to a full pilot: the available output MNI
template does not establish that the required extraction and SDC assets exist,
and the compute environment cannot fetch them.

The next action is to stage the release/recipe-specific missing assets through an
authorized connected context, then verify their identity and usable materialized
contents in the offline compute context. Record their manifest/identity, the
offline cache path and runtime visibility, then run the full-quality pilot.

## Questions and blockers

Blocked on the required extraction/SDC asset set, an authorized staging route,
and post-stage compute-context evidence. No runtime, network, or pilot was run.
