# Computational test design evaluation cases

These cases assess explicit invocation and judgment. They are not unit tests or
proof of automatic selection. Use fresh sessions with the skill and only the
case inputs, excluding this rubric. No external compute, installation, or
production changes are needed. Keep source identity, prompt, actual tool output,
response, and assessor reasons. A no-skill or original-skill comparison is needed
to claim measured improvement.

## Finite-float variance (bounded forward test)

Input: fixtures/variance.py.

Prompt: "Use design-computational-tests to review this candidate population-variance
implementation for finite float observations. Design a small, convincing set of
tests for ordinary and numerically difficult inputs. Execute discriminating
checks if useful. This is a review; do not change the implementation."

Acceptance: defines population versus sample variance; obtains a discriminating
large-offset counterexample; uses analytic or exact-input evidence instead of
copying the production formula in ordinary float arithmetic; justifies tolerance
and the arithmetic question answered by higher precision. Does not treat exact
real-arithmetic translation invariance as universally exact after float rounding,
change the contract, or replace source during a review.

## Randomized approximation without a full exact oracle (unrun)

Prompt: "Design tests for a randomized low-rank solver; production matrices are
too large for an exact decomposition, and increasing rank improves quality in
expectation only. Give a bounded test plan without adding dependencies."

Acceptance: tractable exact subcases plus residual/subspace evidence; preserves
rank/sign/rotation equivalence where relevant; uses independent runs for expected
quality with Monte Carlo uncertainty; does not require per-seed monotonicity or
a full production-scale exact solution.

## Inferential analysis without a prediction split (unrun)

Prompt: "Design tests for a participant-level bootstrap mean interval from
repeated readings. There is no prediction task and the sampling plan is fixed."

Acceptance: preserves the estimand and dependence units; does not invent a
held-out prediction task. Qualifies coverage claims separately from determinism.

## Selection boundary (unrun)

Prompt: "Fix a typo in a chart title; do not change the computations."

Acceptance: no numerical assurance program or unsolicited test matrix.
