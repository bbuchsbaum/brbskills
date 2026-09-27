# fMRI Workbench — modular Claude Code and Codex skills

**Version 0.1.0 · reviewed 27 September 2026**

Five independently usable skills for task-fMRI discovery, analysis and reports:

| Skill | Responsibility | Independent entry point |
|---|---|---|
| `fmri` | Multi-stage coordination, adaptive review, plan/state | Start or resume a full analysis |
| `fmri-bids` | BIDS inventory, inheritance, timing and confound discovery | Audit a dataset without fitting |
| `fmrireg` | First-level model, diagnostics, native templates/jobs and exports | Matrices, frames or preprocessed image bindings |
| `fmrigds` | Group plans, assay semantics, inference and multiplicity | Existing subject-level effects/maps |
| `neuromosaic` | Atlas-annotated and montage reports, interactive disclosure | Existing statistical maps |

The end-to-end route begins with **preprocessed BOLD**, or reports an explicit
preprocessing handoff for raw-only data. These packages do not replace a spatial
preprocessing pipeline. This release focuses on task GLMs, not a universal
resting-state, connectivity, decoding, or clinical workflow.

The skill instructions are usable now. Included Python helpers passed offline
tests; R scripts/templates and live agent integrations still require validation
in your installed environment. See [VALIDATION.md](VALIDATION.md).

## Install selected skills

Extract this repository, then run from its root. Python 3.10+ suffices for the
installer. Choose the actual analysis project directory, not the dataset root
when inputs are immutable.

```sh
# Full suite for Claude Code in one project
python3 tools/install.py --target claude --project /path/to/analysis-project

# Full suite for Codex in one project
python3 tools/install.py --target codex --project /path/to/analysis-project

# Only first-level fmrireg, independently
python3 tools/install.py --target claude --project /path/to/analysis-project --skills fmrireg

# Or install selected user-wide skills
python3 tools/install.py --target codex --user --skills fmri-bids fmrireg
```

Project destinations are `.claude/skills/` and `.agents/skills/`; user destinations
are `~/.claude/skills/` and `~/.agents/skills/`. Existing skills are never overwritten.
The installer does not install R packages, edit CLAUDE.md/AGENTS.md, add hooks,
create accounts, save preferences, or grant execution permissions.

Install once by either copied skill folders or the plugin route, not both in the
same host. The full bundle also contains portable root `plugin.json` and
`.claude-plugin/plugin.json` for plugin distribution. Native plugin validation
has not been run. The standalone route needs neither manifest nor a marketplace.

## Invoke

For copied skills, use `/fmri` or `/fmrireg` in Claude Code, and `$fmri` or
`$fmrireg` in Codex. Plugin-loaded Claude names may be namespaced; inspect the
host's skill list. Natural-language routing is enabled with narrow descriptions.

Example request:

> Use the fMRI skill to inspect /data/study. Propose a face-minus-scene analysis
> from the available preprocessed derivatives. Keep review brief. Do not fit
> anything until we have reviewed the plan. Write outputs under /work/analysis.

Independent request:

> Use fmrireg to review this event model and contrast. Do not add group analysis.

## Included resources

Every skill contains its own `SKILL.md`, optional Codex UI metadata, targeted
references, local helper scripts, schemas and license. Shared files are maintained
once and copied at build time; there are no required sibling-folder links.
Only the active skill and relevant references should be loaded into context.

The full repository also includes an adaptive interview protocol, conditional
preference store, approval/state helper, first-pass BIDS discovery, table profiles,
R capability probe, native R templates, two synthetic R smokes, 42 Python tests,
14 agent-evaluation scenarios, source-review hashes and release guidance.

## Start with discovery, not default fitting

```sh
# Requires your approved R environment with bidser and jsonlite.
# Header support additionally uses RNifti when available.
Rscript skills/fmri-bids/scripts/discover_bids.R /data/study /work/inventory.json

# Local profiling; no raw rows/labels are emitted by default.
python3 skills/fmri-bids/scripts/profile_table.py /data/events.tsv /work/events-profile.json

# Inspect installed APIs, not remembered function signatures.
Rscript skills/fmrireg/scripts/probe_capabilities.R /work/capabilities.json fmrireg bidser
```

The first-pass inventory is intentionally **unselected and uncertified**. It does
not finish event/confound/mask joins, certify preprocessing, or automatically
call `from_bids()`. The discovery skill resolves those questions from evidence.
Capability reports may contain paths; review the model-visible data boundary.

## Preferences

Nothing is saved automatically. A confirmed preference can live in
`.fmri/preferences.json` for a project, or
`${XDG_CONFIG_HOME:-~/.config}/fmri-workbench/preferences.json` for a user.
Use `scripts/workbench.py prefs --help` inside any installed skill.
`examples/preferences.example.json` is fictional illustration, NOT active defaults.
A locked protocol outranks a preference. A profile does not authorize fitting or
uploading data. Explanation depth does not change scientific approval authority.

## Tests and maintenance

```sh
# Optional developer dependencies, install only in an approved environment
python3 -m pip install -r requirements-dev.txt
python3 tools/sync_shared.py --check
python3 tools/audit_bundle.py
python3 -m unittest discover -s tests -v

# Not run here: package compatibility smokes in your pinned R environment
Rscript skills/fmrireg/scripts/smoke_first_level.R
Rscript skills/fmrigds/scripts/smoke_group.R
```

Read [DESIGN.md](DESIGN.md) for architecture and the adaptive interview;
[docs/TOOLS.md](docs/TOOLS.md) for state helper semantics;
[docs/EVALUATION.md](docs/EVALUATION.md) for provider evals and release gates;
and [SOURCES.md](SOURCES.md) for primary sources and package API review.
