# General guidance update: 2026-11-06

Scope: brbskills issues [#1](https://github.com/bbuchsbaum/brbskills/issues/1),
[#2](https://github.com/bbuchsbaum/brbskills/issues/2),
[#3](https://github.com/bbuchsbaum/brbskills/issues/3),
[#4](https://github.com/bbuchsbaum/brbskills/issues/4),
[#5](https://github.com/bbuchsbaum/brbskills/issues/5),
[#6](https://github.com/bbuchsbaum/brbskills/issues/6), and
[#7](https://github.com/bbuchsbaum/brbskills/issues/7), adapted to the user's
instruction to keep skills general and applicable across analyses. No issue was
closed and no study-specific trial counts, radii, pooling recipe or hypothesis
became a skill default. `CONTRIBUTING.md` records that authoring principle.

## Reproduced bug and numerical checks

On macOS, R 4.5.1, fmrigds 0.1.0 at
`e9863f6527844db01e628c61aa6b817ab93b720d`, the original `smoke_group.R`
failed at `length(ids) == 2L`: assay dimnames were absent. The corrected script
uses `space(result)$labels` and validates identity, uniqueness and dimensions.
Unequal-variance fixtures and reversed input order pass independent beta/variance/Z
arithmetic checks. This is a smoke-script fix, not a change to fmrigds itself.

`smoke_design.R` passed with fmrireg 0.3.0.9000 at
`576a2f6dc251006215b823916a6cfe068d68fb3f`. It verifies public event-design
assembly against separately constructed trial columns, independent QR recovery,
an interaction null direction before/after convolution, equivalent timing
representations, duration misspecification and omitted-response allocation under
two synthetic HRFs. Trial columns share the package's HRF engine, so their
agreement is not independent verification of that engine. The separate continuous
HRF examples check general linear-model behavior, not fmrireg's noise estimator.

The optional R test launcher distinguishes an absent package (skip) from an
installed package that fails to load (failure). Both R tests executed locally.

## Repository checks

- Root unit tests: 24 passed.
- Workbench tests: 44 passed, including both R regressions. The two R launcher
  tests passed again after refining the missing-package check.
- fMRIPrep helper tests: 64 passed.
- Alliance offline tests: 41 passed; no real scheduler was contacted.
- lme4 structure/algebra validator: 14 passed.
- Source sync/check, collection audit, ShellCheck and whitespace check passed.
- Codex and Claude ZIP packaging passed for the eight affected skills.

The external system `skill-creator/quick_validate.py` rejects the pre-existing
`compatibility` frontmatter field for fmri/fmrireg. The same rejection was
reproduced on unchanged HEAD; the repository validator and collection audit
accept this supported portable field. Metadata was not removed to satisfy the
older validator. Python checks used the existing `.venv` development environment.

## Explicit-invocation scenario checks

Fresh Codex subagent (model identifier not exposed in its result) and fresh Claude
Code (`claude-haiku-5-5`, reported by the CLI) read the selected fmrireg and r-rmvpa
skills and relevant references. Claude ran with read-only tools, no other MCPs,
no session persistence and customizations disabled. No participant data or cluster
execution was permitted. These were checks of three hypothetical requests:

1. A six-second routine contains a 1–3-second image and a later button press;
   scanner triggers align. Can the routine beta be interpreted as the image response?
2. A full-rank feature matrix has a nearly constant ordinal confidence score;
   some runs lack scores. Can all feature-by-confidence interactions be fitted?
3. Images repeat across two sessions. How should an analysis of stronger
   content-distance relationships for highly confident pairs be specified and checked?

Both outputs separated event meaning from clock alignment, inspected joint
interaction support rather than feature rank alone, and distinguished pair-mean
confidence from confidence differences. They required explicit pair support,
independent repetitions and an appropriate inference model, without selecting
study-specific parameters. Codex preserved the scientific choices in all cases.

The initial Claude answer implied that sharing slopes could make an unrated run
inform the confidence slope. The text was clarified: borrowing an estimate under
a common-slope assumption creates no direct score information in that run.
Imbalance alone also does not prove rank deficiency. A fresh targeted Claude rerun
correctly distinguished borrowed slopes from direct information. It still turned
the optional missingness example into a recommendation and overstated that sparse
support proves non-estimability; it also claimed a per-run comparison was the only
way to assess heterogeneity. Those claims are not supported by the guidance.
Claude's scenario result is therefore mixed, not a full behavioral pass. Do not
infer that correct written caveats reliably prevent every model overstatement.

Temporary local raw CLI evidence was retained under
`/private/tmp/brbskills-general-guidance-forward/` (`prompt.txt`, `result.json`,
`recheck-prompt.txt`, `recheck-result.json`). Test logs and exit metadata are under
`/private/tmp/brbskills-general-guidance-*.log*`. These paths are local execution
artifacts, not portable dependencies. The Codex output is retained in the task's
`skill_forward_check` agent transcript; its principal findings are summarized here.

These checks do not measure automatic discovery, comparative improvement against
the previous skill, or success in every supported client. The remaining evaluation
scenarios were not rerun. No real-data noise calibration, full trial-beta/RSA
pipeline, or live Trillium policy validation was performed in this update.
