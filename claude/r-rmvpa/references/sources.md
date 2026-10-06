# Sources and maintenance

Reviewed 2026-10-06. This is a curated workflow guide, not a frozen API manual.

## Package provenance

The authoring source was rMVPA **0.1.3**, commit
`fd7ac599476ae9128487a8879e3774e47145dcb1` in the
[upstream repository](https://github.com/bbuchsbaum/rMVPA/tree/fd7ac599476ae9128487a8879e3774e47145dcb1).
An older installed package also reported 0.1.3; therefore examples were checked
against a fresh installation of this commit in an isolated temporary library.
See the [verification record](../tests/VALIDATION.md) for exact coverage.

Each workflow reference names its owning help topics and vignettes. The
[package website](https://bbuchsbaum.github.io/rMVPA/) supplies discovery; the
[reference index](https://bbuchsbaum.github.io/rMVPA/reference/index.html) and
[articles](https://bbuchsbaum.github.io/rMVPA/articles/index.html) supply detail.
The website and local source can differ. Resolve callable behavior against the
loaded installation and its methods, then inspect source/tests when documentation
and execution disagree. The API lifecycle registry covers selected entrypoints;
absence from that registry is not proof that a function is stable.

Particular source contracts checked during authoring:

| Decision | Owning source in the pinned revision |
|---|---|
| Geometry, observation layout | `R/dataset.R`, `R/global_analysis.R` |
| CV labels versus targets | `R/design.R`, `R/crossval.R` |
| Public workflow and lifecycle | `R/workflow_api.R`, `R/api_lifecycle.R` |
| Regional result and searchlight payloads | `R/regional.R`, `R/searchlight.R` |
| RSA coefficients, pairs and null scope | `R/rsa_model.R`, `R/pair_rsa_design.R`, `R/permutation_searchlight.R` |
| Feature encoding, tuning and retention | `R/feature_rsa_model.R`, `R/feature_sets_design.R`, `R/banded_ridge_model.R` |
| REMAP target reuse in the default single-fit path | `R/remap_rrr_model.R`, `.remap_paired()` and `fit_roi.remap_rrr_model()` |
| Pattern retention, confirmation and groups | `R/pattern_model.R`, `R/pattern_inference.R`, `R/pattern_group.R` |
| Custom callback and plugin contracts | `R/custom.R`, `R/plugin_helpers.R` |

Planning documents may describe future adapters and statistical procedures. They
do not establish callable functionality. Snapshot limits should be revisited when
the package changes rather than promoted into permanent prohibitions.

## Authoring guidance applied

The current [OpenAI skill documentation](https://developers.openai.com/codex/skills)
supports precise discovery metadata, conditional loading, a focused task, and
testing actual trigger prompts. This skill's task is constructing and reviewing
rMVPA analyses; its references select different model families within that task.

[OpenAI's prompt/skill guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
supports removing unnecessary reading itineraries and overprescription. The
entrypoint carries shared decisions, while detailed API and scientific boundaries
are loaded by route. No mandatory package-wide documentation dump is included.

[Anthropic's authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
supports concise third-person descriptions, shallow references, explicit script
behavior, and evaluations from realistic requests. The runtime helper supplies
deterministic provenance/signature lookup; the examples exercise actual public
APIs. Behavioral cases cover both appropriate and inappropriate activation.

These sources guide the design; they do not establish that this skill improves
agent quality. Static checks, API examples, explicit-invocation forward tests,
implicit selection, and comparisons across products/models are separate evidence.

## Update procedure

When rMVPA changes, inspect only the affected help/source/tests, update the relevant
reference, and rerun the linked examples. Run `scripts/inspect_runtime.R` with the
same R library paths as the intended analysis. Record source revision, package
path/version, optional dependencies, and observed failures. Revisit behavioral
cases after changes to routing or consequential scientific guidance.

In brbskills, edit this source skill, regenerate both product bundles, and run the
repository checks. No installation into personal skill directories is required.
