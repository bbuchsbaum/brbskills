# cobidas

An agent skill for recording MRI/fMRI analysis provenance while the analysis happens, auditing it, and writing methods sections and supplements in which every claim points to evidence. The reporting baseline is the OHBM COBIDAS MRI report v1.0 (2016-05-19; Nichols et al., 2017, *Nature Neuroscience*).

The project's reporting record is the source of truth; the manuscript is a view of it. The skill is a reporting layer. It does not choose or run analyses, is not an OHBM product, and does not certify validity.

## What it does

- **Start / checkpoint:** declares study, acquisition and analysis scopes with explicit membership and records actual settings, receipts, QC, exclusions and deviations at stage boundaries.
- **Audit:** separates planned from executed, and known from unknown, not applicable, not performed and conflicting; flags stale or unsupported claims.
- **Write:** drafts `methods.md`, `supplementary_methods.md`, a claim-to-evidence table and a gap report; a full audit also maps the official Appendix D rows.

`SKILL.md` is the agent entry point. Domain references in `references/` load only when relevant. `scripts/cobidas.py` is an offline, standard-library Python 3.10+ helper (`init`, `record`, `audit`, `build`); [references/helper.md](references/helper.md) documents what it checks and what it cannot.

## Install

The skill is self-contained: copy this folder into your agent host's skills directory (for example `.claude/skills/cobidas/` for Claude Code or `.agents/skills/cobidas/` for Codex, per project or per user). It needs no other skill, pipeline or package; the optional helper needs only Python 3.10+.

Skills are selected by task matching, not lifecycle hooks. To make checkpoints durable, review and add a short reminder to the project's `AGENTS.md` or `CLAUDE.md`:

```markdown
## MRI methods provenance
For MRI/fMRI work, use the cobidas skill at setup, after consequential
analysis/QC/model/inference changes, and before manuscript drafting.
Record actual settings, execution evidence, QC/exclusions and deviations;
keep planned and executed separate; leave unknowns explicit.
```

## Example and tests

`examples/synthetic-project/` is a fabricated, deliberately incomplete task-GLM ledger with generated drafts and a nonempty gap report; no images or human data were used. Run these from the skill directory (the folder containing `SKILL.md`):

```bash
python examples/make_demo.py --output "$(mktemp -d)/cobidas-demo"
python scripts/cobidas.py audit --root examples/synthetic-project/reporting/cobidas
python -m unittest discover -s tests -v
```

## Limits

The local field catalogue (`assets/fields.json`) is a grouped operational aid, not a transcription of Appendix D; its IDs and `required` flags are local. The helper verifies record structure, evidence hashes, currentness and draft bindings, not semantic truth, sample counts or analytic validity. ASL/DSC perfusion, spectroscopy, quantitative MRI, PET and EEG/MEG need modality-specific guidance. No agent-session evaluation has been run yet; see [VALIDATION.md](VALIDATION.md) and [references/evaluation.md](references/evaluation.md). Sources and their review dates are in [references/sources-and-scope.md](references/sources-and-scope.md).
