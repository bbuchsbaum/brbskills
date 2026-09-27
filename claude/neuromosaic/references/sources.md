# Sources and API review ledger

Reviewed 2026-09-27. These are primary sources, not guarantees about a different
installed package or host version. Repository file blob hashes are in the full
bundle's `quality/source-review.json`; they are NOT repository commit pins.
No package was installed or executed during source review.

## Agent packaging and evaluation

- OpenAI, **Rethinking skills and prompts for GPT-6 Astra**:
  https://learn.chatgpt.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  Narrow routing, selective references, fewer rigid itineraries.
- OpenAI, **Build skills**: https://learn.chatgpt.com/docs/build-skills
  Skill directories, progressive disclosure and optional interface metadata.
- OpenAI, **Package your plugin**: https://developers.openai.com/plugins/build/plugins
  Root portable `plugin.json`; `.codex-plugin` remains a compatibility fallback.
- OpenAI, **Testing Agent Skills systematically with evals**:
  https://developers.openai.com/blog/eval-skills
- Anthropic, **Extend Claude with skills**: https://code.claude.com/docs/en/skills
- Anthropic, **Skill authoring best practices**:
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Anthropic, **Improving skill-creator** (2026-03-03):
  https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills
- Anthropic, **Plugin reference**: https://code.claude.com/docs/en/plugins-reference
- Anthropic, **Test plugins with evals**: https://code.claude.com/docs/en/plugin-evals
- Agent Skills specification: https://agentskills.io/specification

## BIDS

- Inheritance and common principles:
  https://bids-specification.readthedocs.io/en/stable/common-principles.html
- Events (negative onsets, zero durations, stored-volume timing origin):
  https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files/events.html
- MRI acquisition metadata (TR, VolumeTiming, timing units):
  https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html

## Reviewed package interfaces

- `fmrireg/README.md` — Preprocessed-data boundary.
  https://github.com/bbuchsbaum/fmrireg/blob/master/README.md
  Git blob: `b9b085e0c18646c8879677c83af595bea3b5d1c4`.
- `fmrireg/R/from_bids.R` — Run-only sorting, first TR, common mask; explicit binding escape hatch.
  https://github.com/bbuchsbaum/fmrireg/blob/master/R/from_bids.R
  Git blob: `e06efa1b0f0709bd3df3e8858fcb1eb95a40128d`.
- `fmrireg/man/from_bids.Rd` — Convenience importer public contract.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/from_bids.Rd
  Git blob: `ee4d27a5ffa5adff6d9bab0395eff3c0d9cfb7d4`.
- `fmrireg/vignettes/multisubject_fanout.Rmd` — Templates, preflight, jobs, future and exports.
  https://github.com/bbuchsbaum/fmrireg/blob/master/vignettes/multisubject_fanout.Rmd
  Git blob: `70060b64bb9fc96bf02459e6a2804dfb367df99b`.
- `fmrireg/man/fmri_template.Rd` — Template signature and default runwise_meta.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/fmri_template.Rd
  Git blob: `476a39637cabafd9599c0a602f54a43514584db1`.
- `fmrireg/man/fmri_lm_control.Rd` — Typed statistical configuration.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/fmri_lm_control.Rd
  Git blob: `ff699d403b19d533339e91440f7f02a675daf45b`.
- `fmrireg/man/baseline_spec.Rd` — Baseline/drift public interface.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/baseline_spec.Rd
  Git blob: `0342c8f0a0edcbdf5b59bce3f0a9b192c6764643`.
- `fmrireg/man/estimation_spec.Rd` — Joint versus runwise fitting.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/estimation_spec.Rd
  Git blob: `73cc946f95c61383bc796b68f446dab10ba975e8`.
- `fmrireg/man/noise_spec.Rd` — Censor is AR-estimation/whitening only; engine restrictions.
  https://github.com/bbuchsbaum/fmrireg/blob/master/man/noise_spec.Rd
  Git blob: `1302498cdf962b6513c749177c95d4ab1c9bf9e0`.
- `fmrireg/vignettes/fmrireg.Rmd` — Current frames, event/baseline model and fitting.
  https://github.com/bbuchsbaum/fmrireg/blob/master/vignettes/fmrireg.Rmd
  Git blob: `3eae1812cd930a5ec83f3ca3a1572e9ad218f33c`.
- `bidser/README.md` — Discovery and public confound sets.
  https://github.com/bbuchsbaum/bidser/blob/master/README.md
  Git blob: `f84ea430162a8b23306f218f71782dc2dd5cd666`.
- `bidser/man/get_metadata.Rd` — Inherited metadata with provenance.
  https://github.com/bbuchsbaum/bidser/blob/master/man/get_metadata.Rd
  Git blob: `b83675fc79a8ec355e94023ec9bbcb294612a630`.
- `bidser/man/read_confounds.Rd` — Confound return shape and cleaning defaults.
  https://github.com/bbuchsbaum/bidser/blob/master/man/read_confounds.Rd
  Git blob: `70c2cac072e64c3ce164bbc42fa3c9da51725867`.
- `bidser/man/query_files.Rd` — Exact queries, scopes, refresh and entity tables.
  https://github.com/bbuchsbaum/bidser/blob/master/man/query_files.Rd
  Git blob: `02810f7a4f8ebfb07d78dd1d7edf5a5ec8bd877c`.
- `fmrigds/README.md` — Lazy group grammar, reducers, LMM scope, examination.
  https://github.com/bbuchsbaum/fmrigds/blob/main/README.md
  Git blob: `da74601ed2a70afe83b4d58f6ccfa1c7487ac433`.
- `fmrigds/vignettes/fmrigds.Rmd` — Assay semantics and table handoff; effects versus evidence.
  https://github.com/bbuchsbaum/fmrigds/blob/main/vignettes/fmrigds.Rmd
  Git blob: `c5a08949a1613875ca4bf033a5cf59856c8e34c4`.
- `neuromosaic/README.md` — Map manifest, CLI, rendering and recoverable interactive voxels.
  https://github.com/bbuchsbaum/neuromosaic/blob/main/README.md
  Git blob: `81f2dcd2e1744e4845cb481f4ffdbe93d6eaa1dc`.
