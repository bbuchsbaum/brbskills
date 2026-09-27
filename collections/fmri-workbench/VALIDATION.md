# Validation status — 27 September 2026

## Executed successfully

- **42 Python unit/integration tests**: preference consent and conditional scope,
  protocol conflicts, typed exact matching, explicit approval, pilot gates,
  stale plan/code detection, resource limits, inventory ambiguity, table profiles,
  local locking, no-overwrite installation, and independent first-level installation.
- Offline structural audit: five portable skill frontmatters; all local Markdown
  links remain inside their individual skill; shared-file byte identity; JSON
  schemas are structurally valid; manifest identity fields match; Codex default
  prompts identify the intended skills.
- All Python source files compile. R files received source review and a basic
  delimiter-balance check, **not** R parsing or execution.
- ZIP integrity checked after packaging; no actual neuroimaging data, credentials,
  generated user preferences, symlink dependencies or bytecode caches included.

See `quality/python-tests.txt` and `quality/structural-audit.json` for outputs.
Measured entry-point sizes: 63–65 lines and 383–424 body words per skill;
all five descriptions total 1,087 characters. These are not token benchmarks.

## Not executed / not established

There is no R/Rscript executable in this build environment. Therefore the two
synthetic R smokes, discovery script, package adapters, native templates, full
first-level→fmrigds→neuromosaic round trip, and real-data scientific validation
have **not** been executed. The package review records observed public interfaces
and specific limitations; it is not a tested package lock.

Claude Code and Codex native skill/plugin loading, plugin validation, actual
trigger behavior, evaluation scores, provider usage and runtime context costs
have **not** been measured. Fourteen behavior-evaluation cases are included, all
marked not run, with native Claude graders and a provider-neutral index.

The Python helpers test mechanics, not neuroimaging correctness. Their approval
flags record a decision and are not security capabilities. The discovery script
produces an unselected/uncertified inventory, not a ready-to-fit manifest. Sealed
file checks hash exactly the named files, not transitive members of a manifest.
Scientific validity, preprocessing QC and inference remain explicit gates.

## Release recommendation

Use this as an installable, source-grounded v0.1 skill resource. Follow
`docs/EVALUATION.md` to establish package compatibility, bridge correctness,
agent behavior and scientific calibration before a production release. Do not
call this production-validated or claim an empirically optimal token budget.
