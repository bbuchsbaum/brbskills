# Validation — 2026-10-14

This is an instruction skill with synthetic review fixtures. It adds no runtime
helper, service requirement, or test dependency.

Two fresh Codex collaboration subagents explicitly invoked the reviewed skill
against separate local fixtures, without the assessor rubric. The pilot trial
found the failing default CLI despite passing component tests; the repeat trial
verified the repaired path and reconciled obsolete findings with accepted scope.
Both met the bounded rubrics. The parent independently reproduced the decisive
CLI behavior and component tests and verified unchanged fixture hashes.

Exact model identity was not exposed by the collaboration tool response. These
are not full Codex/Claude product-session comparisons or automatic-selection
tests. No original-skill or no-skill baseline was run. Scientific review quality,
tracker writes, and authorized repair behavior remain untested.

The repository import record at `docs/imports/project-reality-check.md` retains
input hashes, user prompts, selected files, reports, command/output records,
parent subprocess receipts, and assessor reasons. Agent command records are not
complete raw tool transcripts.

Skill-creator validation and the 24 root repository tests passed. The final
sync/check and extracted ZIP validation results are recorded in the import
evidence. These structural checks establish packaging properties, not review quality.

Reproduce the packaging checks from the repository root with its development
environment active:

```sh
python scripts/skills.py sync
python scripts/skills.py check
python -m unittest discover -s tests -v
python scripts/skills.py package project-reality-check
```

For behavioral trials, follow [evaluation cases](evaluation-cases.md), keeping
the rubric separate from the evaluating session. Do not treat deliberately flawed
fixture implementations as approved application code.
