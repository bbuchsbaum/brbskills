# Mote peer work import — 2026-10-16

Adapted from the user's supplied `mote-peer-work.zip`, `SKILL.md`,
`AGENTS-snippet.md`, and `START-HERE.md`. The loose files match the three archive
members byte for byte. The [original manifest](mote-peer-work-original-manifest.json)
records their SHA-256 hashes and sizes. No upstream authorship or license was
supplied; none is inferred. The Downloads originals are unchanged.

Canonical source: `skills/mote-peer-work/`. Both product downloads carry the
same protocol, references, agreement asset, and trial cases. Only Codex includes
`agents/openai.yaml`. Authoring this skill does not install it globally or adopt
its agreement into this repository's operational `AGENTS.md`.

## Adaptation

- Keeps persistent peers, existing end-to-end lanes, review priority, limited
  work in progress, precise handoffs, and continuation through authorized work.
- Keeps the entrypoint focused on next-action decisions; moves setup, review,
  integration, and quiet-resource procedures to conditional references.
- Includes a project agreement as a copyable asset and a common opening mandate.
  Two peers can review reciprocally; larger teams choose one primary reviewer
  per change without a permanent manager or all-to-all review requirement.
- Keeps Mote authoritative while allowing an existing Fray attention/evidence
  channel. Does not install either tool, introduce a second store, or spawn peers.
- Preserves shared-index contents, dirty artifacts, lease recovery, candidate
  gates, protected evaluations, and explicit resource-window release.
- Replaces the draft's optional product-discovery/symlink setup with explicit
  reads of an accessible complete skill folder. The Claude import fallback is
  retained with a current primary documentation link and version/configuration
  caveat. Local Mote help and installed tracker/session guidance supplied the
  command semantics; remote Mote source retrieval was unavailable.

These are authoring decisions, not demonstrated gains over the supplied draft.
No executable helpers, hooks, services, or new test dependencies are introduced.

## Verification boundaries

See the bundled [validation status](../../skills/mote-peer-work/tests/VALIDATION.md)
and [candidate cases](../../skills/mote-peer-work/tests/evaluation-cases.md).
Packaging checks and an independent read-only instruction review do not amount
to a live multi-terminal trial. No actual shared project, peer messages,
benchmark, protected gate, publication, or deployment is part of this import.

The [review record](mote-peer-work-review.json) binds the initial instruction
files to hashes and retains findings/dispositions. One independent reviewer
walked through simultaneous review handoffs, a three-worker quiet run with an
existing build and a silent peer, and resumed work with an expired lease, foreign
staged changes, and obsolete approval. Clarifications distinguish a proposed
resource window from an agreed one and explicitly reacquire expired ownership.
Independent reciprocal reviews remain welcome. The reviewer also observed a
temporarily missing trial-cases link while that file was still being authored;
final isolation checks cover its presence. This is instruction review, not a
behavioral pass.

The follow-up review found the material concerns resolved and recorded hashes
for the entrypoint and the two clarified references. The installed skill-creator
validator initially rejected the optional `compatibility` frontmatter field;
the requirement was moved into the body without changing the dependency or any
check. The subsequent validator passed.

Final local verification passed: source/bundle sync and check, all 24 repository
unit tests, `git diff --check`, and isolated extraction, source parity, relative
reference validation, and checksum verification for both ZIPs. The
[packaging receipt](mote-peer-work-packaging.json) records archive hashes and
checked file counts. No hosted CI run is claimed.
