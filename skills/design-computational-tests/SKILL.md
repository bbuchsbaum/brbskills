---
name: design-computational-tests
description: "Design tests for numerical algorithms and computational pipelines, or investigate subtle regressions using independent correctness evidence."
---

# Design Computational Tests

Choose or implement tests for a stated computational contract and plausible
failure modes.
Prefer independent evidence over output snapshots or assertions that reproduce
the implementation. This skill designs computational assurance; it does not
add a mandatory test matrix to every code change.

## Establish the contract

Identify valid domains, shapes, representation conventions, invariants, error
behavior, and accuracy guarantees. Separate mathematical correctness from
numerical stability, convergence, approximation quality, and performance.
Reuse existing tests that establish these claims. For a regression, reproduce
the reported behavior before minimizing the input or changing the metric. A
failing assertion may expose a bad expectation or fixture; establish which
contract is violated before changing production code.

## Select evidence that could reveal the error

- **Analytic or differential oracle:** use a closed-form case, independent
  implementation, higher precision, or a slower exact algorithm. Shared code or
  preprocessing can make two implementations agree on the same mistake. Higher
  precision can expose arithmetic error without validating the formulation.
- **Metamorphic relation:** test transformations the contract actually promises,
  such as permutation, scale, decomposition, or representation equivalence.
- **Properties and adversarial cases:** generate valid domains and targeted
  degenerate, ill-conditioned, minimal, or extreme cases. Keep shrinking useful
  and failures reproducible.
- **Internal invariants:** inspect intermediate state when a correct-looking
  final output could conceal a wrong-domain operation. Avoid coupling to
  private structure without a correctness reason.
- **Regression fixtures:** retain the triggering input and failed invariant for
  demonstrated bugs.
- **Performance evidence:** measure representative work when performance is a
  changed contract or the requested task. Record configuration, data generation,
  completed work, and time/memory. A smoke run is not a benchmark.

Exercise approximate/exact, streaming/batch, parallel/serial, and backend paths
when their differences affect the requested guarantee. Do not require every
family or backend for an unrelated localized fix.

## Numerical judgment

Use tolerances justified by dtype, scale, conditioning, and expected error growth;
combine absolute and relative terms where appropriate. If accuracy is unspecified,
state a justified working assumption rather than inventing a correct-rounding or
all-input guarantee. Choose the tolerance independently of the candidate output. Check finite values when
required by the contract, and test intentional non-finite behavior explicitly.
Use fixed seeds/streams for reproducibility without treating one seed as broad
stochastic evidence.

For approximate methods, use exact baselines where feasible, including tractable
subcases; otherwise use justified bounds or independent references and state what
remains unverified. Distinguish accuracy from cost. Require monotonic improvement
with compute budget only when guaranteed. Stochastic quality claims may need
independent runs and Monte Carlo uncertainty; one seed establishes reproducibility,
not calibration. Keep correctness and timing thresholds separate.

For statistical pipelines, preserve the estimand and sampling/dependence
structure. Where training/evaluation splits apply, keep tuning and learned
preprocessing within the appropriate training data. Do not impose a holdout
split on an inferential analysis without a prediction task. Evidence should
check the reported metric or inferential target.

## Validation and handoff

Place fast contracts and regressions in ordinary CI; schedule expensive stress
and performance work according to project needs. Run affected tests and required
gates, fix failures caused by the change, and rerun what the fixes affect. Broaden
only when new evidence warrants it.

Explain the contract tested, why the evidence is independent, what failed before
the fix, and material untested boundaries. Do not inflate confidence with arbitrary
test counts, mirror tests, or a universal merge checklist. Assessing the broader
scientific claim belongs to scientific-check when available and relevant; this
skill remains usable on its own.
