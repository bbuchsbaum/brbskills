# Review, integrate, and resolve disagreements

Read before a handoff, independent review, shared Git operation, or unresolved
dispute. Preserve the project's actual acceptance and landing procedure.

## Submit a reproducible artifact

Make acceptance conditions concrete before implementation. Submit an immutable
commit plus base, or a reproducible snapshot including required untracked files,
patches, and checksums. A dirty live checkout alone is not a frozen artifact.
Ensure the reviewer can access it from their terminal or worktree. Keep the
handoff compact:

```text
REVIEW <ticket> -> <primary reviewer>
Artifact: <exact commit/snapshot and relevant base; accessible location>
Scope: <paths and behavior changed>
Evidence: <commands, results, artifact locations>
Check: <acceptance conditions and principal risk>
Known limitations: <what remains unproved>
Next: <what approval unblocks; who integrates>
```

Move implemented work to `review`, not `done`. Separately record the reviewer,
request, and eventual verdict using the project's candidate protocol when
applicable. A status change does not do those things or release any leases.
Freeze the submitted artifact; release idle paths with a checkpoint and retain
only reservations still needed. Review may continue after paths are released.
Avoid stacking new work on unreviewed changes unless the project permits it.

## Review independently

Inspect acceptance conditions, the actual delta, and evidence. Independently
check the highest-risk assertion with a suitable test, trace, or inspection.
Use an isolated snapshot or the existing safe review arrangement so tests cannot
overwrite a peer's files or attribute concurrent edits to the submitted artifact.
Generated files, fixtures, caches, and shared build outputs can require a writer
slot even during review. Reading alone needs no reservation.

Return a verdict bound to the exact artifact: approval, changes required, or
unable to review with a reason. State what was checked and what remains unproved.
Scale effort to risk; do not rerun every expensive suite for a minor edit.
Separate blocking acceptance/correctness findings from optional preferences.
Do not manufacture criticism, unrelated redesigns, or a quota of findings.

The author addresses valid findings and returns work to active status while
fixing it. Disputes need evidence. A changed artifact requires review of the
delta and any invalidated evidence; old approval does not transfer silently.
Reciprocal reviews are welcome when each verdict is independently evidenced.
No self-approval, silence-as-approval, or approval trading. Cross-provider review
can help, but shared assumptions can still produce shared errors.

## Serialize integration

Keep the current checkout/worktree arrangement. In a shared checkout, name one
writer at a time for staging, commits, and ref-changing operations. Inspect the
index before staging. If it contains another worker's changes, preserve it and
coordinate; do not unstage, stash, reset, clean, or commit their work implicitly.
Stage intended paths only and inspect the staged diff before committing.

Integrate the reviewed artifact through the authorized landing procedure.
Resolve conflicts within agreed ownership, refresh affected review/evidence,
and run relevant integration checks. Record the resulting artifact and close the
ticket only when its gates pass. Peer approval is not permission to push, merge,
deploy, publish, spend, or change an acceptance gate; use existing user authority
for those actions and ask only for authority actually missing.

## Keep requests and disagreements bounded

Use issues for execution state and verdicts, the existing public topic for
decisions affecting lanes, and a named request for a peer's next action. If the
team already uses Fray for requests, link its attention/evidence to Mote rather
than making another ownership record. Do not broadcast repeated requests when
a primary reviewer becomes unavailable; explicitly reassign the review.

For Mote multiline or shell-sensitive prose, use supported literal stdin, for
example `mote msg send ... --stdin` or `mote discuss post ... --body -`, with a
quoted heredoc delimiter. Do not interpolate prose into a shell command. On
uncertain delivery, inspect state and use supported stable idempotency keys.
Acknowledgement means receipt; answer, decline, or redirect separately. Resolve
the request through the channel's normal lifecycle after the result is handled.

Separate the disputed claim, evidence, and decision needed. After two exchanges
without new evidence, stop repeating positions: run a bounded discriminating
test, consult the existing decision owner, or ask for the precise human decision
needed. Reversible choices within a lane belong to its responsible owner;
changes to public contracts involve affected owners. Peer agreement cannot
weaken gates or grant new authority. Block only affected work.

## Recover a missing peer's work

Silence and lease expiry do not prove a worker has exited or abandoned files.
Inspect Mote, dirty changes, artifacts, and relevant running work. Request a
handoff; use established expiry/adoption procedures only after preserving the
previous work and attribution and resolving conflicting ownership. A resumed
worker must recheck live state and reacquire any expired claim/reservation
through the established procedure before editing; past ownership is insufficient.
Never impersonate a missing peer
or invent their approval. If independent review remains unavailable, keep the
change pending and checkpoint a precise next step.
