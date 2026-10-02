# Computational assurance skill imports

Imported on 2026-09-30 at the user's request from the installed local
design-computational-tests and scientific-check skills. Neither installation
was changed. The [original manifest](computational-assurance-original-manifest.json)
records resolved source paths, repository base and original file hashes. Neither
source supplied a license; no new license is inferred.

The canonical sources are skills/design-computational-tests/ and
skills/scientific-check/. Both generated products share the instructions and
fixtures; Codex additionally receives agents/openai.yaml.

## Workshop changes

- Differentiate choosing tests for a computational contract from reviewing the
  broader scientific claim. Each skill remains independently usable.
- Preserve inferential estimands and dependence units without imposing a
  prediction split on every statistical analysis.
- Permit tractable exact subcases, bounds and independent references when a
  full exact baseline is infeasible.
- Distinguish higher-precision arithmetic evidence from independent validation
  of a mathematical formulation.
- Separate fixed-seed reproducibility from probabilistic calibration and require
  Monte Carlo uncertainty when using simulation to assess probabilistic claims.
- Replace mandatory model escalation with competing explanations, discriminating
  evidence and an honest unresolved conclusion when review is unavailable.
- Recognize that a failing test can reflect an incorrect expectation or fixture.
  Disclose unspecified accuracy assumptions instead of inventing a guarantee.

Both entrypoints remain below the repository's roughly 600-word preference.
No new runtime dependency, compulsory cross-skill invocation, or universal test
matrix is introduced.

## Bounded behavioral evidence

Fresh Codex subagents received each entrypoint and minimal synthetic inputs;
the assessor rubric and previous critique were excluded. Provider/model details
not exposed by the collaboration tool are not inferred. These trials assess
explicit invocation only, without a no-skill or original-skill comparison.

- The [variance trial](computational-assurance-evidence/variance-forward/final-response.md)
  used exact rational arithmetic for represented float inputs and exposed
  catastrophic cancellation and intermediate overflow. Review of its full output
  also found an unstated correct-rounding guarantee and insufficient tolerance
  rationale. That prompted the accuracy-assumption clarification; the original
  evidence is preserved as a partial result rather than overwritten.
- The [bootstrap trial](computational-assurance-evidence/bootstrap-forward/assessment.md)
  identified row-level resampling of clustered readings, retained the participant
  mean estimand, and qualified the wider cluster-bootstrap reference as
  approximate rather than calibrated 95% coverage. It met the bounded rubric.

The [fresh variance follow-up](computational-assurance-evidence/variance-assumptions-forward/final_response.md)
used exact-representable translation and an exact-input reference. It removed the
correct-rounding overclaim but still did not sufficiently explain its numerical
tolerance constants. The numerical failure is decisive independently of those
thresholds; this remains a partial judgment result, not a blanket pass.

The [assessor record](computational-assurance-evidence/assessment.json) binds
trial outcomes to the actual evaluated entrypoints. Final scientific-check
wording makes simulation guidance conditional, preserving analytic evidence;
that last sentence has static review only. Raw prompts, hashes, outputs and
limitations are retained with the trial artifacts. Remaining evaluation cases are in each skill's tests directory.

## Verification

Repository checks were run in an isolated snapshot of tracked HEAD 894f68e plus
the two imported skills, preserving unrelated working-tree edits. The 24 root
tests and all required offline skill tests, Workbench audit/tests, lme4 static
validator and ShellCheck passed. The [check summaries](computational-assurance-evidence/repository-check-results.json)
record exits and test output; raw logs are retained in the task-local evidence.

The shared checkout already failed root check on dashboard-builder generated
drift before integration. This import does not regenerate that unrelated work.
Full product-session comparisons, automatic selection, hosted CI and scientific
validity beyond these synthetic fixtures remain unqualified. Final standalone
ZIP extraction/checksum validation is recorded alongside these checks.
