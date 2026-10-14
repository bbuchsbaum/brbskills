# Evidence rules

## Claim records

Use a compact table or short records, not a mandatory database. Retain stable claim IDs
across repeat reviews where previous IDs exist. Split a claim when its parts require
different evidence; do not atomize every sentence.

For each decision-changing claim, record:

- The precise claim, its source and scope, and whether it is an accepted requirement,
  a public promise, or a hypothesis.
- The implementation state: **absent**, **partial**, **connected**, **unknown**, or
  **not applicable**. “Absent” is bounded by the inspected surfaces; “connected” does
  not by itself establish correct behavior.
- The evidence state: **demonstrated**, **supported by inspection**, **unverified**,
  or **contradicted**, with the actual evidence reference.
- The consequence for the current decision, relevant dependencies, and the next
  discriminating observation when support is insufficient.

These are two axes, not a maturity score. A connected implementation can be contradicted
by execution; an absent implementation can still rest on a well-supported feasibility
argument. Excluded scope is not a defect, but a still-live misleading public promise
remains a documentation or expectation problem.

## Match the evidence to the claim

For a behavior claim, prefer a run through the actual public interface on representative
input and inspect the meaningful output, not just the exit status. For an existence or
dependency claim, precise source inspection may suffice. For an algebraic claim, a checked
derivation under explicit assumptions is relevant; numerical agreement alone does not
prove an identity. For speed, usability, adoption, or scientific validity, use a suitable
measurement rather than substituting unit-test counts.

Examples of support boundaries:

| Observation | What it supports | What it does not establish |
|---|---|---|
| A function exists | An implementation candidate exists | Callers reach it or it is correct |
| A mocked service test passes | The tested interaction with the mock | The real integration works |
| An installed CLI produces a checked result | That workflow on that input/environment | Every advertised input or deployment works |
| CI passed at a recorded revision | Those checks passed there | A different dirty tree has passed |
| Two agents agree | Their assessments agree | An independent oracle or successful execution |
| A proof establishes equivalence under assumptions | The stated mathematical equivalence | Numerical stability or matching software conventions |
| A held-out metric improves | The specified evaluation improved | Leakage-free design or universal generalization |

## Keep reusable evidence inspectable

A useful execution receipt includes the command or experiment, working directory,
revision plus relevant dirty-state identifier, inputs or fixture identity, environment
that could affect the result, exit status, meaningful output, and artifact location.
A source receipt includes path and line/symbol, and its version or observation date.
For remote facts, include the original source, version/date, and access limits.
Do not capture secrets or sensitive datasets merely to make a receipt comprehensive.

Reusing an artifact is legitimate when its provenance and tested scope match the claim
and relevant inputs have not changed. Say it was reused, not rerun. Revalidate evidence
invalidated by changes to code, configuration, data, environment, or the claim itself;
age alone is not the only staleness criterion. Unmatched or inaccessible artifacts
remain unverified, not passing and not automatically failing.

## Seek disconfirmation economically

Choose probes by likely decision impact, uncertainty reduction, and cost. This is a
qualitative judgment unless defensible probabilities and utilities exist; do not invent
an expected-value calculation. A single counterexample can refute a universal behavior
claim, but passing a small sample cannot establish one.

For a suspected missing feature, inspect its likely entry points, implementations,
callers, relevant tests, and accepted scope before concluding it is absent. For a
suspected bug, reproduce when feasible and inspect evidence that might explain the
behavior legitimately. Record environmental blocks distinctly from product failures.
When execution is unavailable, provide the inspected finding and exact next probe;
never imply that the probe ran.

If independent review is worthwhile and available, give a reviewer a narrowly defined
claim and inspectable artifacts rather than only your conclusion. Model diversity or
fresh context may help challenge assumptions but does not create an independent
correctness oracle. Verify consequential findings against sources or behavior.
