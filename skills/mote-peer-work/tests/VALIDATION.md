# Validation status — 2026-10-16

This is an experimental instruction-only protocol, adapted from a user-supplied
draft. It has no scheduler, enforced locks, automatic reviewer, or execution
service. Mote must already be available, and the worker sessions must be started
separately under the user's authorization.

The [evaluation cases](evaluation-cases.md) specify future selection and
cross-terminal trials. Live two-/three-worker Codex and Claude Code trials,
automatic selection, interruption/recovery under real concurrency, and
comparisons against the original draft or a no-skill baseline remain **unrun**.
Static validation and read-only case review cannot establish those behaviors.

Local authoring checks passed: skill-creator frontmatter validation and all 24
repository unit tests. One independent read-only reviewer considered three
synthetic situations (reciprocal handoffs, a quiet run, and expired ownership
with changed review artifacts). The follow-up found the identified instruction
ambiguities resolved. This was a case walkthrough, not execution by independent
Claude and Codex terminals.

Reproduce the relevant local structural and packaging checks with Python 3.10+
and the repository's development dependencies, from its root:

```sh
python scripts/skills.py sync
python scripts/skills.py check
python -m unittest discover -s tests -v
python scripts/skills.py package mote-peer-work
```

Check each extracted package in isolation, including relative references and
its `SHA256SUMS`. These checks cover portable metadata, reference availability,
source/bundle parity, and packaging mechanics. They do not establish useful
coordination, accepted work, or reduced human dispatch.
