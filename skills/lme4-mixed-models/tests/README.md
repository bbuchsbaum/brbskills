# Validation layers

`python tests/validate_bundle.py` checks packaging, internal links/source IDs, YAML/JSON, and simple derived numerical identities. Its R delimiter check is **not** an R parser, type checker, or runtime test.

The validator prints JSON without changing the skill directory. Use
`--output /path/to/receipt.json` to retain a new run separately; the bundled
`VALIDATION.json` is the original authoring receipt.

`Rscript tests/smoke.R` executes helper checks and representative lmer/glmer fits. It optionally tests the installed DHARMa branch. `RUN_SLOW=true Rscript tests/smoke.R` adds a small bootstrap execution check. This does not establish Type-I-error control, power, coverage, robustness, or cross-version portability.

Audit regression cases use bundled/synthetic data: disabled derivatives, a singular
binomial fit, deliberately damaged saved derivative evidence, and public `vcov`
results for Hessian/RX/fallback routes. They distinguish missing evidence from
failure and preserve conditions without requiring one version's derivative-omission
behavior. No external corpus or fitted corpus objects are required.

Run `Rscript examples/lmm.R` and `Rscript examples/glmm.R` separately, inspect every generated table/plot and any stopped review gate, and retain `sessionInfo()`. Example results are not shipped as though they had already been obtained.

`evals/scenarios.yml` defines behavioral cases for an actual Codex/Claude session or evaluation harness. It has not been executed merely because the file exists. Use a fresh session per case, record model/provider/version/settings, test with and without the skill, retain outputs and tool traces, and grade hard failures as failures regardless of fluency. The desired outcomes are specifications, not measured pass rates.

For a future validated release, run an R/package-version matrix including pre-0.5.0 and 0.5.x DHARMa APIs; test the full examples; run adversarial agent cases; have an independent mixed-model statistician review substantive policies; and simulate the entire declared fitting/inference policy on relevant designs. Publish omissions and failures rather than only successful runs.
