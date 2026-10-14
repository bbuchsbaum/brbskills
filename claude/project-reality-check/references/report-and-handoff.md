# Report, closure, and handoff

## Report contract

Scale length to the decision and requested depth. A small review can fit on one page;
a deep review may need an evidence appendix. For a substantial review, use the order
below; combine items for a short answer and omit empty sections:

1. **Verdict and scope.** Answer the actual decision in plain language. State version,
   local modifications, environment/access limits, and whether this is a feasibility,
   implementation, or release-readiness assessment.
2. **Reality map.** List the few claims that determine the verdict. For each, give its
   requirement source, implementation state, evidence state, source/run receipt,
   decision consequence, and key dependencies.
3. **What to preserve.** Identify useful working assets and which claims are already
   adequately supported. Distinguish a sound core from missing connections or proof.
4. **Decisive gaps.** Separate observed failure, missing implementation, missing
   integration, evidence debt, and misleading/obsolete promises. Explain impact and
   the counterevidence checked. Keep minor hygiene outside the critical path.
5. **Bridge.** Give dependency-ordered actions with concrete acceptance gates. Include
   the first executable action, relevant non-goals, and a decision branch for decisive
   experiments. Do not invent owners, precise effort estimates, or approvals.
6. **Limits and reversal condition.** Name unexamined surfaces and blocked probes;
   distinguish them from failures. State any substantive countercase and the evidence
   that would change the recommendation; do not invent opposition for balance.

A useful compact table is:

| Claim / source | Implementation | Evidence / receipt | Consequence / next gate |
|---|---|---|---|
| A concrete user outcome and its scope | connected / partial / absent / unknown / n/a | demonstrated / inspection / unverified / contradicted; reference | Why it matters and what resolves it |

Do not report percentage completion unless a meaningful denominator and weighting were
specified independently of this review. A list of 100 tasks is not such a denominator.
Do not label the whole project “production ready” on the strength of one smoke test.

## Action records

Use prose or the existing tracker schema. Each consequential action needs a claim ID,
reason, proposed change or experiment, dependencies, falsifiable acceptance criterion,
and verification evidence to retain. State an owner only when known. Include a stop or
reframe condition for uncertain research work. Reuse the project's task granularity;
do not create a ticket for every sentence of the review.

Example, for a fictional project:

> **RC-02 — Connect the existing reader to the documented command.** The API reader is
> implemented, but the command still selects a sample backend. Depends on agreement on
> the supported input contract. Acceptance: the installed command processes the checked
> real-input fixture and its values match the reference output; missing input produces
> an explicit error. Preserve the reader and numerical core. Retain command, revision,
> fixture identity, stdout/stderr, and checked output. Do not replace the parser merely
> to fix this wiring gap.

## Repeated reviews

Load the previous review and current relevant task state when available. Report changes
in claims, dependencies, evidence, and decisions rather than rewriting an equivalent
roadmap. Preserve historical evidence; mark superseded conclusions explicitly. A closed
task does not establish the claim without suitable proof, and an open task should not
be reproposed when its implementation already exists. Revalidate only invalidated or
insufficient evidence unless the requested decision calls for a fresh complete run.

Report “no new decisive gaps” when justified. Changed product promises, binding
constraints, important dependencies, a failed proof artifact, or a consequential milestone
can warrant another review. Do not install a schedule or recurring automation merely
because those triggers are mentioned here.

## Optional Mote or other tracker handoff

The method is tracker-independent. When Mote is the project's tracker, retain its IDs
and conventions; do not introduce Beads or a parallel source of task truth.
Discover the installed tracker tools and inspect existing relevant tasks before
proposing or making changes. Do not invent CLI commands, field names, or task IDs.

An assessment alone produces proposed actions, not external writes. If task creation
or updates are requested, deduplicate against current work, preserve existing content,
record dependencies and evidence gates, perform authorized writes with the real tool,
and verify the returned state. Do not silently replace notes or mass-close tasks.
If the tracker is unavailable, deliver clearly marked, not-synced action records in the
report. Never claim they have been created, assigned, accepted, or completed.

## Assessment versus repair

A review can be complete while the project remains blocked. When source repairs are
also authorized by the request or prior instructions, keep baseline findings distinct from modifications, preserve
unrelated local work, verify the affected behavior and relevant regressions, and update
the verdict only to the extent supported. Do not let a successful fix erase the original
finding or imply that untested project-wide claims have passed.
