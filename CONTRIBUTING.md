# Authoring and maintaining skills

Edit `skills/<skill-name>/` or `collections/<collection>/skills/<skill-name>/`;
generated `codex/` and `claude/` folders are downloads. Every skill is independent.
Use lowercase hyphenated names and a `SKILL.md` with common `name` and `description`
YAML fields. Preserve portable optional fields such as `license`, `compatibility`,
and string-valued `metadata`. Keep vendor UI metadata in
`agents/openai.yaml`; the builder includes it only in Codex bundles.

Collections retain their own tests, documentation, and shared source resources.
Edit a collection's `shared/` files once; root `sync` copies them and the collection
license into each member skill before building both products. Root `check` rejects
stale shared copies. Skill names must be unique across all collections and `skills/`.
When deleting or renaming a shared resource, remove its old per-skill copies too.

## Context discipline

The root [guidance register](README.md#authoritative-guidance) links to the primary
sources and records when they were reviewed. Apply them proportionally:

- Front-load the workflow and real trigger terms in a short description. Discovery
  loads descriptions for all installed skills. Avoid generic keywords that select
  a skill for unrelated tasks.
- Keep the entrypoint focused on decisions the model needs help making. Put
  substantial conditional procedures in references, with a direct link and a
  reason to read each one. Avoid mandatory reading tours and repeated general
  advice.
- Use specific third-person descriptions, a body under 500 lines, and shallow
  reference links. Add contents to references over 100 lines so selective reading
  works. Use scripts for reliable repeated operations, with clear inputs and failures.

The line limit is a ceiling, not a target. Our review target is a description of
roughly 200 characters and an entrypoint of roughly 600 words or fewer where the
workflow allows it; these are repository preferences, not vendor limits. The
checker reports characters and words, not measured model tokens. Retain operational
invariants even when shortening prose. Assets and tests on disk do not enter
context unless read.

Keep the core product-neutral: no tool names available only in one harness,
absolute author-machine paths, implicit shell expansion, hooks, or undocumented
dependencies. Add product-specific behavior only for a demonstrated need and test
both generated versions. Do not fork the entire workflow to change branding.

## Add or change a skill

1. Create `skills/<name>/SKILL.md` and only the resources it uses. Define a few
   representative requests, including one that should not select the skill.
2. Verify relative links and bundled scripts in isolation. Keep dates, provenance,
   live-policy uncertainty, and dependencies explicit where relevant.
3. Run the checks below and commit source plus regenerated folders together.
   Add the skill to the root catalog and register additional test dependencies in
   CI. No global installation is required to author a skill.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/skills.py sync
python scripts/skills.py check
python -m unittest discover -s tests -v
python skills/alliance-hpc/tests/test_skill.py
python collections/fmri-workbench/tools/audit_bundle.py
python -m unittest discover -s collections/fmri-workbench/tests -v
python skills/lme4-mixed-models/tests/validate_bundle.py
shellcheck skills/alliance-hpc/scripts/*.sh skills/alliance-hpc/templates/*.sbatch
python scripts/skills.py package alliance-hpc
```

Python 3.10+ is required for repository tooling. Alliance's offline tests also need
Bash and GNU `timeout` (macOS: `brew install coreutils`); ShellCheck is a development
check. Runtime cluster requirements remain in the skill. Removing a skill requires
explicitly removing its two generated folders after review; sync refuses unknown
output folders rather than deleting them silently.

## Behavioral evidence

Static checks and mocked helpers do not prove skill selection or model quality.
For consequential wording changes, exercise the cases in the skill's
`tests/evaluation-cases.md` in fresh Codex and Claude Code sessions, with only the
permitted fixtures. Record product/model, prompt, selected files, output, and
pass/fail reasons. Compare against the previous version or a no-skill baseline
when claiming improvement. Never label unrun scenarios as passed or use token/word
counts as proof of effectiveness.
