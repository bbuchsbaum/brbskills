---
name: r-rmvpa
description: "Builds and reviews rMVPA analyses in R: run-blocked decoding, searchlights, RSA, feature encoding, cross-domain models, and pattern confirmation. Use for rMVPA workflows, API choices, or debugging."
---

# rMVPA

Turn an analysis question into the correct rMVPA objects, execution path, and
interpretable result. Preserve the user's chosen estimand and scope. This skill
starts with analysis-ready neural observations; it does not supply raw-fMRI
preprocessing or a generic machine-learning workflow. Execution requires R,
rMVPA, and the optional dependencies of the selected model.

## Establish the contract

Identify the prediction direction or representational quantity, observation unit,
independent unit (run, item, session, participant), and requested spatial output.
Check row order, feature identity, image geometry, and train/test provenance before
fitting. Resolve ambiguity that changes the scientific question; ordinary API
choices can be made directly.

Check the **loaded installation**, not just a checkout's DESCRIPTION. When
versions or arguments are uncertain, run the bundled helper from this skill's
directory: `Rscript --vanilla scripts/inspect_runtime.R symbol ...`. It reports
package provenance and requested exported signatures without reading datasets.
Use installed help and registered S3 methods for dispatch details. A matching
version number does not establish matching source. Missing features require a
compatible API or an explicit dependency change, never invented functions.

## Load the relevant route

Read only the reference needed for the current question; combine routes when the
analysis crosses their boundaries.

| Task | Reference and decisions |
|---|---|
| Assemble images, targets, folds, or fix alignment | [Data and validation](references/data-and-validation.md): geometry, matrix orientation, CV labels versus targets, training-only transformations |
| Classify/regress, choose regional/global/searchlight output, or diagnose execution | [Decoding and execution](references/decoding-and-execution.md): runnable baseline, result access, engines, parallelism, CLI |
| Compare RDMs, model pair relationships, or request RSA inference | [RSA](references/rsa.md): measurement versus statistic, nuisance terms, modulation, exchangeability and null scope |
| Predict neural responses from features | [Encoding and Feature RSA](references/encoding.md): banded ridge, nested selection, Feature RSA geometry, retained predictions |
| Compare encoding/retrieval or adapt between domains | [Cross-domain analyses](references/cross-domain.md): naive transfer, ERA, REMAP, ReNA and domain adaptation |
| Fit distributed patterns, interpret maps, confirm or pool loadings | [Pattern models](references/pattern-models.md): retained fits, frozen bases, independent confirmation, group contracts |
| Supply a custom ROI calculation or reusable model | [Extensions](references/extensions.md): callback versus plugin contract, schema and validation |

## Shared execution rules

- Use public constructors. The usual chain is dataset → design → model spec →
  runner. Runner support is family-specific: banded ridge has `run_banded_ridge()`;
  `run_global()` is not a universal substitute for regional execution.
- Match outer folds to the generalization claim. Keep scaling, selection,
  alignment, covariance estimation, and tuning inside eligible training data.
  `split_by` partitions scoring; it does not create independent train/test folds.
- Use `validate_analysis()` where supported and inspect actual fold membership.
  Its static checks cannot certify exchangeability or preprocessing independence.
- Exercise a small representative ROI or synthetic fixture before scaling a new
  pipeline. Preserve the intended method when reducing computational size.
- Choose retention before fitting: scalar searchlight maps cannot supply missing
  observation ledgers or fitted models afterward. Inspect failures, missing
  metrics, coverage, and diagnostics as well as the nominal result class.

Report the API/version used, data/fold contract, relevant outputs, observed checks,
and what the result supports. Separate prediction, descriptive geometry, and
calibrated inference. A smoke test or successful run does not establish scientific
validity.

For updating this skill, consult [sources and maintenance](references/sources.md)
and the [evaluation cases](tests/evaluation-cases.md). Current verification is
recorded in [VALIDATION.md](tests/VALIDATION.md).
