# Validation record

## Audit/reporting update — 2026-09-27

General evidence handling was updated without changing the model-selection or
random-effects policy. [The update receipt](tests/audit-update-2026-09-27.json)
retains code hashes, runtime output, static results, and a bounded forward case.

- **23 R smoke checks passed** on R 4.5.1, lme4 2.0.1, Matrix 1.7-3. New cases
  use synthetic/bundled data and damaged saved evidence to check unavailable
  derivatives, Hessian defects, covariance provenance, and retained fallback
  conditions. No external corpus was used. DHARMa and optional bootstrap branches
  were skipped; those capabilities were not changed or qualified by this run.
- **The updated GLMM example completed** in an isolated directory. The retained
  covariance was passed into `emmeans`, three finite contrast SEs were checked,
  and the prediction plot was inspected. The output explicitly identifies
  Bonferroni confidence intervals and Holm p-values. The LMM example was not rerun.
- **14 static/algebra groups and 23 repository tests passed**; both generated
  product bundles were synchronized and checked. The source-date validator now
  accepts independent ISO review dates rather than imposing the original date.
- **One fresh-context agent reporting case** used a synthetic manufacturing
  scenario. Parent review found the required distinctions in its answer. This is
  a bounded forward check with no old-skill/no-skill comparison, not an estimated
  improvement or a cross-product behavioral evaluation. The 28 scenario
  specifications have not been systematically executed.

Cross-version compatibility, independent statistical review, error-rate/coverage
simulation, and a controlled skill-effectiveness comparison remain unperformed.
The original authoring receipt below and `VALIDATION.json` are preserved.

## Original authoring record

**Release:** 0.1.0-candidate

**Recorded:** 2026-09-25

## Executed successfully

`python tests/validate_bundle.py` ran in the creation environment. All **14 static/algebra check groups passed**, with zero failed groups. The final [JSON record](VALIDATION.json) gives exact counts and numerical results.

Checks cover unique/scoped source entries and URL syntax; portable skill frontmatter and core word budget; relative Markdown link targets; short citation-ID resolution; analysis-plan/evaluation YAML structure; basic quoted-string/bracket balance in four R files; key guardrail presence; and independent Python calculations for covariance recoding, binary contrast scaling, nonlinear random-effect integration, a lognormal moment, and Monte Carlo standard errors.

These are not live link-crawler results, R parsing/execution results, statistical coverage results, or agent behavioral results.

## Not executed

| Validation layer | Status | Reason / implication |
|---|---|---|
| R syntax parsing and helper smoke tests | NOT RUN | R/Rscript was absent. Attempted system-package installation could not reach package servers; a subsequent request reported DNS resolution failure. |
| LMM and GLMM examples | NOT RUN | No R runtime. No generated model outputs or figures are represented as existing. |
| Current/legacy DHARMa compatibility matrix | NOT RUN | The wrapper follows inspected APIs but both branches need actual environments. |
| Bootstrap execution check | NOT RUN | R unavailable; B=20 in the optional test would only be an execution check. |
| 24 Codex/Claude adversarial cases | SPECIFIED, NOT RUN | The YAML is an evaluation specification, not a measured pass rate. |
| Independent expert review | NOT PERFORMED | Named sources did not review or endorse this bundle. |
| Error rates, coverage, power under the entire skill policy | NOT ESTIMATED | Requires design-specific simulation of selection, fitting, diagnostics, and inference. |

## Reproduction

Follow [tests/README.md](tests/README.md). Record the actual R/lme4/companion versions and retain errors, warnings, plots, and session information. A future release should update this record with genuine executions, including failures and skips. Do not replace “not run” with “pass” based on code inspection alone.
