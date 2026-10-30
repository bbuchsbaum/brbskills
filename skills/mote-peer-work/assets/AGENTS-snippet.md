## Persistent peer collaboration

When the user authorizes ongoing work by two or more agents, read
`skills/mote-peer-work/SKILL.md` and use it within that scope. Recheck live state
after compaction or restart. A bounded one-off request remains bounded.

Work as peers on the approved plan. Complete, verify, obtain independent review,
and take the next useful authorized action. Help peers succeed while preserving
their responsibility. Mote is authoritative for ownership and acceptance; use
distinct actors and the same coordination store across terminals/worktrees.

Preserve useful file/module stewardship. Acquire narrow live claims and
reservations before editing; stewardship is not a perpetual lock. Agree on a
writer for shared files and serialize shared Git mutations. Never overwrite or
discard another worker's changes because a reply is missing or a lease expired.

At safe boundaries, unblock peers and finish existing work before opening more.
Default to one implementation and at most one additional change awaiting review
per worker. Give each change one independent primary reviewer; prefer
cross-provider review when suitable. Review exact artifacts, preserve acceptance
gates, and never treat silence as approval.

Communicate scope changes, blockers, handoffs, evidence, decisions, and resource
windows. Keep routine activity out of the coordination record. Continue while
useful authorized work remains; otherwise checkpoint and wait or park. Do not
manufacture work, busy-poll, expand authority, spawn workers, or build coordination
tooling without a request. Instructions alone cannot restart an exited session.
