# Validation record — 2026-09-30

Two self-contained instruction skills, with synthetic evaluation fixtures and
Codex UI metadata. No production runtime helper or new test dependency is added.

## Evidence boundary

Bounded explicit-invocation trials in fresh Codex subagents used synthetic
fixtures and excluded the acceptance rubric. These are not fresh full Codex and
Claude Code product-session comparisons, automatic-selection evidence, or an
efficacy study. No no-skill or original-skill baseline was run.

The first variance trial exposed an unstated accuracy guarantee and an
under-explained tolerance; its original result is retained and the entrypoint
was clarified. A fresh follow-up removed that overclaim but left tolerance
rationale under-explained, so it remains a partial result. The participant-bootstrap trial distinguished row resampling
from participant resampling and withheld exact coverage claims. Case-by-case
assessment, source hashes and actual output are recorded in the repository
import record at docs/imports/computational-assurance.md.

## Local verification

Isolated-source sync/check, 24 root tests, all required existing offline skill
checks, Workbench audit/tests, lme4 static validator and ShellCheck passed.
Standalone ZIPs are also validated after extraction. These are packaging and
regression checks, not efficacy or scientific qualification.

## Reproduction

At repository root with requirements-dev.txt installed:

    python scripts/skills.py sync
    python scripts/skills.py check
    python -m unittest discover -s tests -v
    python scripts/skills.py package design-computational-tests scientific-check

For behavioral trials, use tests/evaluation-cases.md as the assessor rubric and
provide only SKILL.md plus the relevant fixtures to the evaluating session.
Deliberately flawed fixtures are assessment inputs, not approved analysis code.
Additional approximation, native-path, calibration and selection cases remain
unrun. Passing a package check does not establish scientific validity.
