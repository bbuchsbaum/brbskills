# lme4-mixed-models

**Portable Codex / Claude Code skill · v0.1.0-candidate · evidence checked 2026-09-25**

Audit/reporting update: 2026-09-27; audit schema 0.2.0. The general modeling
policy is unchanged. See [validation evidence](VALIDATION.md).

A decision protocol for planning, fitting, diagnosing, comparing, interpreting, and reporting Gaussian LMMs and GLMMs with R's lme4. The compact [SKILL.md](SKILL.md) routes to topic references and the [full analysis protocol](references/workflow.md) only when needed. The bundle deliberately does not implement a blind “best model” search.

Imported into brbskills on 2026-09-27. The separately supplied research synthesis
matched the bundled copy exactly. Codex and Claude downloads share the workflow;
Codex additionally receives optional `agents/openai.yaml` display metadata.

## What is included

| Component | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Agent entry point, routing, required decisions, and stopping conditions. |
| [Full analysis protocol](references/workflow.md) | Original detailed decision protocol, retained for conditional reading. |
| [Research synthesis](RESEARCH_SYNTHESIS.md) | Human-readable conclusions from the canvass and disputed recommendations. |
| [Reference router](references/index.md) | Find the relevant short note without loading the whole collection. |
| [Source registry](references/sources.md) / [JSON](references/sources.json) | 48 scoped entries: papers, package documentation, expert references, forums, blogs, and installation documentation. |
| [R audit utilities](scripts/model_audit.R) | Capture fit/covariance conditions, inspect available derivative evidence, guard comparison rows, audit bootstrap output, and specify DHARMa mode. |
| [LMM example](examples/lmm.R) / [GLMM example](examples/glmm.R) | Reproducible demonstration scripts, with explicit targets and review gates; no precomputed results are fabricated. |
| [Analysis plan](templates/analysis-plan.yml) / [Report template](templates/report.md) | Persist the estimand, design, policy, diagnostics, model changes, and reporting contract. |
| [Validation guide](tests/README.md) / [Agent evaluation cases](evals/scenarios.yml) | Runtime tests and 28 adversarial behavioral cases, separately from static checks. |

## Fresh installation

Extract the archive. Place the **entire `lme4-mixed-models` folder**, not just SKILL.md, in the relevant skill directory. Choose the installation for the tool being used.

**Codex, project scope:** `.agents/skills/lme4-mixed-models/SKILL.md`

**Claude Code, project scope:** `.claude/skills/lme4-mixed-models/SKILL.md`

Personal installations use `~/.agents/skills/lme4-mixed-models/` or `~/.claude/skills/lme4-mixed-models/`, respectively. These placements were checked against official documentation [CODEX; CLAUDE]. This package contains only common `name`/`description` frontmatter; it grants no special permissions. Follow the installed client's discovery/reload behavior when adding a skill.

For a new project-scoped installation, run ONE of these from the directory containing the extracted folder:

```sh
# Codex — require a fresh destination to avoid accidental nested/overwritten copies.
mkdir -p .agents/skills
test ! -e .agents/skills/lme4-mixed-models && test ! -L .agents/skills/lme4-mixed-models && cp -R lme4-mixed-models .agents/skills/
```

```sh
# Claude Code — require a fresh destination.
mkdir -p .claude/skills
test ! -e .claude/skills/lme4-mixed-models && test ! -L .claude/skills/lme4-mixed-models && cp -R lme4-mixed-models .claude/skills/
```

Keep the source bundle/version under normal project version control. Do not add every reference to a root AGENTS.md or CLAUDE.md file: that defeats on-demand loading. No user repository or skill directory has been modified by delivery of this archive.

## Invocation

A useful initial request is:

> Use the lme4-mixed-models skill to analyze these data. First write the estimand and design contract, identify the crossed/nested sampling units and justified slopes, and declare the random-structure and inference policies. Fit and diagnose before drawing conclusions. Deliver code, contrasts, plots, sensitivity results, and a report with source-backed decisions.

For a review:

> Use the lme4-mixed-models skill to audit this existing model and report. Distinguish fixed-design rank loss, singular random covariance, numerical warnings, and model misspecification. Verify the reported contrast and prediction targets. Do not change the scientific model solely to obtain significance.

## Dependencies and execution

The skill text requires no package installation. Actual analyses require R and lme4. The examples additionally use emmeans, lmerTest, and pbkrtest; DHARMa is optional in the GLMM demonstration but its absence is explicitly recorded. Install dependencies deliberately in the analysis environment and record their versions. The scripts never install packages or change global optimizer options.

Run from this folder:

```sh
Rscript tests/smoke.R
Rscript examples/lmm.R
Rscript examples/glmm.R
# Optional execution check only, NOT an adequate inferential bootstrap:
RUN_SLOW=true Rscript tests/smoke.R
```

The examples write under `examples/output/` and may stop for a review gate. Inspect the audit rather than bypassing the gate. They are demonstrations on bundled lme4 datasets, not completed substantive reanalyses. The helper's comparison guard is intentionally conservative; it does not prove model nesting or validate an inferential reference distribution. Negative-binomial family descriptions and unusual encodings may need manual comparability review.

Optional static/algebra validation uses Python with NumPy and PyYAML:

```sh
python tests/validate_bundle.py
# Optional: save a new receipt outside the installed skill directory.
python tests/validate_bundle.py --output /path/to/validation-result.json
```

The validator prints its current result without modifying the historical
`VALIDATION.json`. Downloaded bundles include a generated `SHA256SUMS` inventory;
run `shasum -a 256 -c SHA256SUMS` from this directory to verify it.

## Release status

**This is a source-grounded release candidate, not an independently validated statistical autopilot.** The original creation environment recorded fourteen passing static/algebra check groups and no R execution. See [VALIDATION.md](VALIDATION.md) for historical and import-time evidence, and [the original machine-readable result](VALIDATION.json). No Codex/Claude behavioral pass rate, cross-version compatibility result, independent expert approval, Type-I-error simulation, or coverage validation is claimed.

The main methodological policy—design-supported simplification when no policy was supplied—is explicitly labeled as this bundle's choice. It is not presented as consensus over “keep it maximal.” Source authority, access limitations, and disagreement are preserved in the evidence notes.
