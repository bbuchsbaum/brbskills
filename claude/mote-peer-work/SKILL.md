---
name: mote-peer-work
description: Coordinate persistent peers across Claude, Codex, or other terminals using Mote. Use for ongoing work by two or more agents on an approved plan, including ownership, reciprocal review, and handoffs.
---

# Mote peer work

Optimize for accepted project progress. Help peers succeed while preserving
their responsibility. A bounded request stays bounded; ongoing authorization
permits the next useful action within the approved plan.

Requires an available Mote CLI and a shared store. Mote owns tickets, claims,
reservations, decisions, and acceptance state. Use its
installed guidance or `mote help --all` for mechanics. An existing Fray channel
may carry peer attention and evidence; link back to Mote without duplicating
ownership. Preserve stricter candidate/review/landing policies. Peer agreement
cannot expand user authority. Do not spawn workers or build coordination tooling
unless requested.

## Join or resume

Confirm a distinct actor per live worker, the same Mote store, checkout/branch,
dirty files, active claims, incoming requests, and protected resource windows.
Re-observe this state after restart or compaction before mutating anything.
Read the relevant plan and current agreement, not the entire history.

Preserve established lanes. When setting up terminals or an agreement, use
[setup](references/setup.md). If Mote or its shared store is unavailable, report
the coordination blocker; do not silently create a substitute store.

Own coherent slices including tests and documentation. Stewardship supplies
continuity and a default contact; live claims and reservations govern edits.
Reserve narrow paths before editing, renew while using them, and stop on lost
ownership. Preflight alone does not reserve. Obtain a writer slot for shared
files and agreement for another lane's interface changes. Generators, formatters,
and lockfile updates count as edits. Ordinary decisions within your lane need
no team consensus.

## Choose the next useful action

Check actionable updates at safe boundaries: after a task or meaningful test,
before shared operations, and before waiting or ending. Prioritize:

1. Honor stops, ownership conflicts, protected windows, and urgent correctness issues.
2. Unblock a peer: answer a blocking request, review ready work, supply an agreed interface.
3. Finish, fix, verify, or integrate work already in progress.
4. Take the highest-value ready ticket in your lane that advances the plan.
5. Offer a bounded contribution outside your lane; obtain agreement before editing.
6. Checkpoint and wait or park when no useful authorized work remains.

Default to one implementation in progress and at most one additional change
awaiting review per worker. Drain review/integration backlog before opening
more. With three or more peers, name one primary reviewer per change; reassign
unavailable reviewers explicitly. Prefer cross-provider review when useful,
without making provider diversity a gate or proof of independence.

## Finish and communicate

Before handing off, reviewing, integrating, or resolving a dispute, read
[review and integration](references/review-and-integration.md). Approve exact
artifacts after independent checks; silence and reciprocal approval bargains
never count. Keep implemented work in `review` until its actual gates pass.
Status changes do not release claims or record a verdict. Serialize shared Git
mutations and preserve other workers' changes.

Communicate information that changes another worker's action or preserves a
needed handoff: scope, blockers, contracts, evidence, decisions, resource windows.
Skip routine narration. Acknowledgement is receipt, not completion; answer,
decline, or redirect requests. Use supported literal-stdin message forms.

For quiet benchmarks or protected evaluations, read
[shared resources](references/shared-resources.md) before booking or running.

## Continue, recover, or park

A missing reply or expired lease does not establish abandoned work. Inspect
current artifacts and running jobs; use the existing handoff/expiry procedure,
preserving dirty changes and attribution before reclaiming.

After a ticket, take the next useful authorized action. When blocked, help
elsewhere or leave artifact locations, checked/unchecked state, leases, jobs,
pending requests, next action, and resume condition. Release unused resources.
Use bounded existing waits; never busy-poll or promise an unimplemented wakeup.

Stop at completion or a real scope, authority, resource, or session boundary.
Instructions do not restart exited workers. This protocol remains experimental;
[trial cases](tests/evaluation-cases.md) define observable behavior, not proven efficacy.
