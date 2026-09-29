# Experimental status — 2026-09-29

This is an initial, unvalidated teaching protocol. It contains instructions,
examples, and optional decision-attribution conventions; it supplies no execution
engine, learner model, enforced decision schema, or fault-isolation mechanism.

Repository validation covers frontmatter, reference availability, generated
Codex/Claude consistency, and package contents. Existing repository and fMRI
Workbench tests check their tooling. These checks do not establish that an agent
waits appropriately, gives accurate feedback, or improves learning.

Local authoring checks on 2026-09-29 passed: skill frontmatter validation,
repository sync/check, 24 repository tests, the Workbench audit and 42 tests,
41 Alliance offline tests, 14 lme4 structural/algebra checks, and ShellCheck for
the Alliance shell helpers. These existing suites exercise repository tooling
and neighboring skills, not the trainee protocol's behavior. Both trainee-mode
download formats were generated; no behavioral pass is inferred from packaging.

From the repository root, reproduce the relevant tooling checks with Python
3.10+ and the repository's development dependencies:

```sh
python scripts/skills.py sync
python scripts/skills.py check
python -m unittest discover -s tests -v
python collections/fmri-workbench/tools/audit_bundle.py
python -m unittest discover -s collections/fmri-workbench/tests -v
python scripts/skills.py package trainee-mode
```

Fresh Codex/Claude interaction cases, automatic skill selection, learner retention
and transfer, and a comparison with ordinary assistance remain **unrun**. The
[candidate cases](evaluation-cases.md) document possible future checks without
claiming results. No learner study, real fault drill, cluster execution, or hosted
CI result is supplied. Research motivation is summarized separately in the
[evidence reference](../references/evidence.md).
