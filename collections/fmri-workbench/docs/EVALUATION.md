# Evaluation and release gates

## Three independent evidence levels

1. Offline structure/Python behavior: `python3 tools/audit_bundle.py` and
   `python3 -m unittest discover -s tests -v`. These can run without R or a model.
2. Package compatibility: run the two synthetic R smokes in the pinned target
   environment. Inspect explicit preflight, numerical recovery and the first-level
   export→fmrigds→neuromosaic bridge on tiny fixtures. Source review is not execution.
3. Agent behavior and scientific calibration: fresh-session tests with and without
   the skill, followed by planted-effect/null datasets, independent reference fits,
   representative real-data pilots, and expert review. None is implied by level 1.

## Current native Claude plugin eval layout

`evals/<case>/prompt.md` and `graders/*.md` use the native plugin-eval format.
They are NOT skill-creator's separate eval JSON format. The local suite uses
hypothetical, synthetic scenarios and read-only tool permissions. No human data,
API credentials, paid task automation, or model invocation is included in tests.
The official page reviewed on 2026-09-27 requires Claude Code 2.1.269 or newer;
check the installed CLI before use. Native plugin validation/evals were not run here.

```sh
claude plugin validate .
claude plugin eval . --case first-level-only --runs 1 --ablation none --no-publish
```

For a release comparison, run both enabled and baseline arms, multiple seeds/runs,
and report all cases rather than selecting favorable runs. Retain `--no-publish`
for local evaluation artifacts. Inspect CLI help for current cost controls. Model
runs consume the operator's account usage. Plugins execute with the operator's
permissions; a trusted test suite is not a security sandbox.

## Codex and cross-provider comparison

`quality/scenarios.json` is a deliberately provider-neutral case list, NOT a
claimed Codex native eval schema. Use a fresh scratch project/session per case,
install only the intended skill(s), and run the same prompts under the installed
Codex. Keep an identical baseline with no skill installed. Do not expose this
repository's maintainer AGENTS.md to the baseline. Record model/build, prompt,
skills loaded, references read, final response, commands, output artifacts,
clarification rounds, errors, time, and token/usage telemetry when available.
Apply the criteria in each case, not just a regex for confident wording.

## What to optimize

Treat data misuse, invented API/metadata, pseudoreplication, false corrected
inference, stale approval, and silent preference persistence as release blockers.
Measure trigger precision/recall, correctness, API validity, first useful plan,
questions/rounds, unnecessary reference loading, total context, and agent usage.
For narrow API questions, penalize loading unrelated stages and demanding a full
workflow. For actual fitting, penalize skipping design/pilot checks. A shorter
prompt is not better if it hides scientific failure.

Use separate development and held-out tasks. Tune descriptions for routing before
adding body text. Add a small invariant or deterministic check for recurring
failures; do not keep appending a new paragraph for every observed mistake.
Re-run after package or model upgrades, and archive failed runs as well as successes.

## Numerical/real-data fixtures still required before a production release

Test run/session collisions, missing run entities, inherited events, multiple
pipelines/spaces/resolutions/echoes, varied or irregular timing, dummy scans,
leading derivative NA, missing condition levels, collinear confounds, planted
contrasts, null calibration under AR noise, covariance-aware run combination,
known/unknown variance group paths, restricted LMM designs, global multiplicity
families under streaming, grid/affine mismatch, empty clusters, interactive
payload disclosure, interrupted jobs, and resumptions after input/code changes.

The bundle is an installable v0.1 skill resource, not an already calibrated,
automatic analysis engine. R smokes, full bridge fixtures, native provider evals,
and representative scientific validation remain explicit release work.

Sources: https://code.claude.com/docs/en/plugin-evals ;
https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills ;
https://developers.openai.com/blog/eval-skills .
