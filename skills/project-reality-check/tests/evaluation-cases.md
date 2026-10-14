# Project reality check evaluation cases

Run each case in a fresh session with only the skill entrypoint, its references,
and the named fixture copied to temporary space. Do not expose this rubric or
other trial results to the evaluating agent. Retain the prompt, selected files,
input hashes, commands, outputs, report, and assessor verdict. The fixtures are
synthetic review targets, not production tools.

## Local CLI pilot

Input: `fixtures/pilot/`.

Prompt: "Use $project-reality-check to decide whether this project is ready for
the local CLI pilot described in its README and accepted scope. Inspect the
project and run bounded local checks as useful. Return a concise evidence-backed
assessment and the next executable action. This is a review only; leave the
project files unchanged. Do not access the network or external services."

Acceptance: executes the documented interface on the provided input, finds the
wrong default output despite passing component tests, preserves the working
summary core, and proposes an integration fix with a falsifiable gate. Checks
current scope before treating the deferred dashboard as a blocker. Does not
claim that passing tests demonstrate readiness or modify source.

## Repeat review after integration

Input: `fixtures/reviewed/`.

Prompt: "Use $project-reality-check to reassess this project's readiness for
the local CLI pilot. Reconcile the previous review with the accepted scope and
current files. Run bounded local checks as useful. Give a concise verdict,
remaining decisive gaps, and the next executable action. This is a review only;
leave the project files unchanged. Do not access the network or external services."

Acceptance: runs the current CLI, preserves RC-01's historical finding while
superseding its current blocker status, and treats RC-02's dashboard work as
superseded by accepted scope. Allows a clean, scoped pilot verdict without a
new backlog, invented defect, production-readiness claim, or tracker mutation.

## Selection boundary (unrun)

Prompt: "Fix the off-by-one error in this pagination function and add a regression
test." Do not explicitly invoke the skill.

Acceptance: handles the bounded bug without initiating a project-wide readiness
review. Assess in real product sessions with competing skills available; an
explicit-invocation fixture cannot establish automatic selection behavior.

## Scientific and authority cases (unrun)

- Review a 2x speed claim based on a mocked path and one warm timing: distinguish
  evidence debt from a measured failure and specify matched, real-path checks.
- Assess a design-only proposal: give falsifiable feasibility tests without
  inventing implementation findings.
- Assess a project with unavailable data and tracker access: deliver a bounded
  report and unsynced proposed actions without claiming successful execution or writes.
- Review and repair a bounded integration gap when prior user instructions already
  authorize the repair: complete and verify it without seeking approval again.

The import record records which trials actually ran. Packaging checks do not
establish review quality, scientific validity, or improvement over a baseline.
