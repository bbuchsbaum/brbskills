---
name: visual-hill-climb
description: "Improves interfaces and figures through bounded, scored review rounds with fixed specimens, independent critics, and regression checks. Use for visual hill climbs or iterative design critique, not a one-off edit."
---

# Visual hill climb

Improve a visual artifact from a recorded baseline, preserving function and data
fidelity. Scores are subjective review aids, not proof of correctness or measured
user preference. User choices constrain every round.

## Establish the comparison

1. Infer the target, audience, constraints, and references from the request; ask only
   for decisions that materially affect the work. Fix a small rubric and a bounded
   budget (default: baseline plus three improvement rounds). Name the deliverable
   and stopping rule. Routine styling requests do not need this workflow.
2. Create a task-owned harness in writable scratch space or an ignored project
   directory. Read [harness setup](reference/harness.md) for layout, commands, and
   dependencies. Keep source changes in the project's normal workflow and preserve
   unrelated edits. A separate branch is useful when practical, not a prerequisite.
3. Choose fixed specimens covering relevant states, sizes, and failure cases.
   Record what cannot change: data, scales, copy, behavior, or API contracts. Changes
   to those constraints need the user's agreement unless already authorized.
   For data-bearing work, include the fidelity lens; visual scores cannot excuse
   scientific errors. Render print specimens at delivery size and resolution.
4. Adapt the [rubric](reference/rubric-template.md), then build, check, capture,
   and review **v0 before editing**. Record source revision/dirty diff, inputs,
   environment, and gate logs. Retain failed baselines with their failure status.

## Improve in bounded rounds

- Select a coherent change from confirmed defects and the highest-impact critique.
  For reproducible defects, add a regression check with an attributable failing
  fixture when practical. Read [gate checks](reference/gate-checks.md) when designing
  checks; use [lessons](reference/lessons.md) when a diagnosis or metric is suspect.
- Build under a new round ID; never overwrite captured evidence. Run relevant
  project checks and the harness gate, saving actual exit status. Failed or missing
  checks stay visible; a failed candidate cannot replace the accepted best round.
- Verify claims on the final build. Write [round notes](reference/round-notes.md),
  then update the local progress page. Private evidence stays local unless sharing
  is authorized. The page is supplementary to a short chat update.
- Use the [critic prompts](reference/critic-prompts.md) for fresh-context visual,
  function/accessibility (or scientific fidelity), and target-user critics. Critics
  inspect immutable artifacts, write in separate directories, and do not edit source.
  Use available, permitted delegation; serialize when capacity or resources require.
  Never launch extra model processes to bypass limits. If independent reviewers are
  unavailable, label self-review explicitly and leave independent scores pending.
  Read only the applicable [Codex](reference/platform-codex.md) or
  [Claude Code](reference/platform-claude.md) adapter when arranging reviews.
- Record complete critiques, including contrary findings. Fix regressions before
  interpreting score gains. Keep rubric, critic roles, and specimen comparisons
  stable; a material change starts a new baseline. Scores with missing reviewers
  remain provisional. Reuse gate evidence rather than rerunning expensive work.

## Finish

Stop at the budget, the user's request, a blocker, or two successive rounds with
less than 0.2 movement per critic and no unresolved regressions. Flat averages can
hide regressions; report those explicitly. Further rounds need a stated reason
and renewed budget. Select the best qualifying round, not automatically the latest.

Report baseline and final scores, verified improvements, remaining defects, check
failures, and evidence paths. Update a task-local resume note. Do not automatically
write persistent memory, install dependencies globally, publish, commit, or push;
follow the user's existing authorization for those actions.
