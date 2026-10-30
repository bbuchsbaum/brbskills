# Set up independent peer terminals

Read this when adopting the protocol, adding a terminal, or repairing identity
or store ambiguity. Joining an established team does not require rebuilding it.

Contents: [instructions](#make-the-same-instructions-available),
[identity](#keep-identity-local-to-each-worker),
[agreement](#agree-on-enough-to-start),
[opening mandate](#give-each-worker-the-same-opening-mandate).

## Make the same instructions available

Keep the complete skill folder, including references and assets, available to
each worker. A project may use `skills/mote-peer-work/`; an existing native skill
installation works too. Use its actual path in the startup prompt and project
guidance. Downloading only `SKILL.md` omits required references.

When asked to adopt the protocol in a project, adapt the
[standing agreement](../assets/AGENTS-snippet.md) into its existing `AGENTS.md`.
Preserve other instructions and reconcile conflicts. Do not install the snippet
merely because a worker uses this skill for one run. Keep assignments in Mote.

Ensure each terminal actually reads the same agreement. Claude Code's direct
`AGENTS.md` loading depends on version and instruction configuration; an existing
`CLAUDE.md` or `CLAUDE.local.md` in the directory ancestry can affect it. Where
needed, add `@AGENTS.md` to an existing root `CLAUDE.md`, outside a code fence or
inline code, without duplicating an import or replacing other guidance. Confirm
the loaded files in the installed product. These behaviors were checked against
the [Claude Code instruction documentation](https://code.claude.com/docs/en/memory)
on 2026-10-16; check it again when setup differs. Explicitly reading the skill
works without relying on automatic selection.

## Keep identity local to each worker

Use the existing Mote store. Do not initialize a store in every worktree or
change a shared persisted actor setting underneath another terminal. For
example, set these in each worker's launch environment, substituting the real
store path and a distinct actor:

```sh
export MOTE_STORE=/absolute/path/to/existing/project/.mote
export MOTE_ACTOR=codex-1
```

A second worker could use `claude-1`, and a third `codex-2`, with the same store.
Names identify workers, not model-specific duties. Confirm that subsequent
shell calls retain the environment and that no other live worker uses the name.

Useful read-only orientation commands are:

```sh
mote doctor
mote actor show
mote in-flight
mote inbox
mote discuss pulse
mote ready
```

Use installed Mote session guidance for presence and renewal. Presence, ticket
claims, and path reservations are separate. A recent message does not prove a
peer is live. Read-only orientation neither claims work nor acknowledges mail.
Inspect only relevant details after startup.

Use Mote's CLI for writes; never edit its operation files. `mote help --all`
and the installed tracker/message-board guidance define exact syntax. The
[`mote-tracker` source](https://github.com/bbuchsbaum/mote/blob/main/skills/mote-tracker/SKILL.md)
is a reference location, not a bundled dependency or a promise that an installed
CLI matches upstream. This package's Mote examples were checked locally against
`mote 0.1.0` help and installed guidance on 2026-10-16.

## Agree on enough to start

Reuse the existing coordination topic. If lanes are missing, one worker proposes
a small split; affected peers accept or adjust it. Safely claimed, uncontested
work can proceed while unrelated assignments are settled. Record:

```text
Plan / authorized run boundary: <existing plan or tranche and acceptance gates>
Actors and lanes: <actor -> file/module stewardship, including tests/docs>
Reviews: <one primary reviewer per change; availability or handoff>
Shared paths: <exact paths and agreed writer procedure>
Integration: <current writer slot and existing landing procedure>
Resource windows: <active booking and participants, if any>
```

Two peers normally review each other's changes. With three peers, A reviewing
B, B reviewing C, and C reviewing A is one starting arrangement; choose by
competence and availability, and adjust per change. For larger groups, route
each review to one primary reviewer and involve other affected owners only for
their contracts. No permanent coordinator, all-to-all review, or unanimous vote
is required. The integration writer is a temporary responsibility.

When someone finishes a lane, they first clear reviews and blockers, then offer
an explicit bounded handoff elsewhere. Do not split implementation from its
tests merely to keep everyone occupied. New workers inspect active claims and
resource windows before joining; existing workers need not reshuffle useful lanes.

## Give each worker the same opening mandate

Replace the skill path and run boundary with actual values:

> Read the project instructions and `skills/mote-peer-work/SKILL.md`. Join the
> existing peers on the approved tranche of tickets. Confirm your distinct
> actor and shared Mote store, inspect requests and active ownership, and preserve
> the working division of labor. Implement, verify, cross-review, and integrate
> through the authorized workflow. At each safe boundary, unblock and finish
> before starting more. After a ticket, take the next useful authorized action.
> Continue until this tranche meets its gates or a real boundary requires a
> checkpoint. Do useful work now; do not return only a plan or spawn more workers.

Use a bounded existing tranche for the first trial. Preserve budget/session
limits. Missing Mote, inaccessible artifacts, or unavailable peers are explicit
constraints, not reasons to invent coordination tools. Retain pending review
if nobody independent can perform it. Use the host's existing wait/resume
facilities; these instructions supply neither a daemon nor a scheduler.
