# alliance-hpc import

Imported from the user-provided `alliance-hpc-skill.zip` on 2026-09-27.

- Archive SHA-256: `412a0e9ab7587e3e2d3ced9512331c96663dffc6d3fc6c03bb7a719e00a5cc28`.
- 13 files, 73,001 uncompressed bytes; safe relative paths and no symlinks.
- All 12 payload hashes in the original inventory verified before extraction.
- [Original inventory](alliance-hpc-original-SHA256SUMS) is retained as provenance;
  it does not describe the edited source or current bundles.

The import retains cluster references, executable helpers, template, and offline
tests. Repository edits shorten the shared entrypoint, add Codex display metadata,
update installation guidance, and correct two locally reproducible failure paths:
continuing after failed submission preflight and accepting a truncated probe as
complete evidence. Generated bundles have fresh inventories.

Cluster facts retain their original 2026-09-21 audit date and source limitations.
This packaging task does not refresh live Alliance entitlements, scheduler policy,
or qexec behavior against a live installation. Model evaluation cases are provided
but are not automated acceptance results. See each skill's `tests/VALIDATION.md`
for the offline test boundary.
