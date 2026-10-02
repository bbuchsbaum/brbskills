# brbskills

Modular skills for **Codex and Claude Code**, maintained from one shared source.
Each skill can be downloaded and installed independently.

| Skill | Purpose | Codex folder | Claude Code folder |
|---|---|---|---|
| [design-computational-tests](skills/design-computational-tests/SKILL.md) | Design independent correctness tests for numerical algorithms and computational pipelines | [codex/design-computational-tests](codex/design-computational-tests) | [claude/design-computational-tests](claude/design-computational-tests) |
| [scientific-check](skills/scientific-check/SKILL.md) | Assess evidence for scientific inference, numerical results, and measured performance claims | [codex/scientific-check](codex/scientific-check) | [claude/scientific-check](claude/scientific-check) |
| [cobidas](skills/cobidas/SKILL.md) | Record MRI/fMRI analysis evidence during work and write COBIDAS-aligned methods with explicit reporting gaps | [codex/cobidas](codex/cobidas) | [claude/cobidas](claude/cobidas) |
| [trainee-mode](skills/trainee-mode/SKILL.md) **(experimental)** | Guided practice at selected analysis checkpoints; learning benefits unvalidated | [codex/trainee-mode](codex/trainee-mode) | [claude/trainee-mode](claude/trainee-mode) |
| [lme4-mixed-models](skills/lme4-mixed-models/SKILL.md) | Design, fit, audit, and interpret lme4 mixed models with explicit evidence and inference limits | [codex/lme4-mixed-models](codex/lme4-mixed-models) | [claude/lme4-mixed-models](claude/lme4-mixed-models) |
| [visual-hill-climb](skills/visual-hill-climb/SKILL.md) | Bounded visual improvement with fixed specimens, independent critiques, and regression checks | [codex/visual-hill-climb](codex/visual-hill-climb) | [claude/visual-hill-climb](claude/visual-hill-climb) |
| [dashboard-builder](skills/dashboard-builder/SKILL.md) | Live local page for agent sessions in a project: hook-captured activity, needs-you, and messages to agents | [codex/dashboard-builder](codex/dashboard-builder) | [claude/dashboard-builder](claude/dashboard-builder) |
| [bids-atlas](skills/bids-atlas/SKILL.md) | Offline interactive dashboard of a BIDS dataset: inventory, oddities, events, fieldmaps, fMRIPrep/MRIQC motion and QC | [codex/bids-atlas](codex/bids-atlas) | [claude/bids-atlas](claude/bids-atlas) |
| [fmriprep](skills/fmriprep/SKILL.md) | Portable BIDS preprocessing plans, execution, recovery, and QC | [codex/fmriprep](codex/fmriprep) | [claude/fmriprep](claude/fmriprep) |
| [alliance-hpc](skills/alliance-hpc/SKILL.md) | Alliance/DRAC Slurm planning, execution, and troubleshooting | [codex/alliance-hpc](codex/alliance-hpc) | [claude/alliance-hpc](claude/alliance-hpc) |
| [fmri](collections/fmri-workbench/skills/fmri/SKILL.md) | Coordinate multi-stage task-fMRI analyses | [codex/fmri](codex/fmri) | [claude/fmri](claude/fmri) |
| [fmri-bids](collections/fmri-workbench/skills/fmri-bids/SKILL.md) | Discover BIDS data and assess analysis readiness | [codex/fmri-bids](codex/fmri-bids) | [claude/fmri-bids](claude/fmri-bids) |
| [fmrireg](collections/fmri-workbench/skills/fmrireg/SKILL.md) | First-level task-fMRI models, diagnostics, and exports | [codex/fmrireg](codex/fmrireg) | [claude/fmrireg](claude/fmrireg) |
| [fmrigds](collections/fmri-workbench/skills/fmrigds/SKILL.md) | Group-level models, uncertainty, and inference | [codex/fmrigds](codex/fmrigds) | [claude/fmrigds](claude/fmrigds) |
| [neuromosaic](collections/fmri-workbench/skills/neuromosaic/SKILL.md) | Map montages and statistical reports | [codex/neuromosaic](codex/neuromosaic) | [claude/neuromosaic](claude/neuromosaic) |

The independent computational assurance skills have complementary roles:
`design-computational-tests` chooses tests for a computational contract;
`scientific-check` assesses whether evidence supports the broader scientific
or performance claim. Either works alone. See the
[import and validation record](docs/imports/computational-assurance.md) for
the workshop changes and bounded evaluation evidence.

The five fMRI skills form the [fMRI Workbench collection](collections/fmri-workbench/README.md).
Download the stage you need; `fmri` coordinates multiple installed stages and does
not automatically install the others. These skills cover task-fMRI analysis from
preprocessed inputs. The independent `fmriprep` skill supplies an optional spatial
preprocessing workflow using an available fMRIPrep installation; rriscripts and
Alliance guidance are optional. Consult the [fmriprep validation record](skills/fmriprep/tests/VALIDATION.md)
and [Workbench import status](docs/imports/fmri-workbench.md) for their respective
verification limits.

The standalone `cobidas` skill records MRI/fMRI methods evidence and drafts
COBIDAS-aligned methods for any pipeline or toolchain (SPM, FSL, AFNI, fMRIPrep,
custom code). It requires none of the skills above and does not choose or run
analyses ([import record](docs/imports/cobidas.md)).

The experimental `trainee-mode` skill extends teaching interactions with selected
pause points, graduated hints, and attribution in the existing decision record.
It does not replace an analysis skill or change its execution permissions.
Protocol behavior and learning benefits remain unvalidated; see its
[rationale](skills/trainee-mode/references/evidence.md) and
[validation status](skills/trainee-mode/tests/VALIDATION.md).

## Download an individual skill

Use **Git sparse checkout** to download the complete folder for just the skill you
want. This includes its references and scripts: downloading only `SKILL.md` is not
sufficient. You need Git; you do not need Python or the repository's build tools.

Set the repository's HTTPS clone URL:

```bash
BRBSKILLS_REPO_URL='https://github.com/bbuchsbaum/brbskills.git'
```

Choose one example. Both download `alliance-hpc`; replace that name with any skill
listed in the catalog above to download a different skill. For example, use
`codex/fmrireg` or `claude/fmrireg` for first-level modeling. Make the same name
substitution in the installation commands below.

**Codex version:**

```bash
git clone --depth 1 --filter=blob:none --sparse --no-checkout "$BRBSKILLS_REPO_URL" brbskills-codex
cd brbskills-codex
git sparse-checkout set --cone codex/alliance-hpc
git checkout
```

The downloaded skill is now in `codex/alliance-hpc/`.

**Claude Code version** (run from outside an existing checkout):

```bash
git clone --depth 1 --filter=blob:none --sparse --no-checkout "$BRBSKILLS_REPO_URL" brbskills-claude
cd brbskills-claude
git sparse-checkout set --cone claude/alliance-hpc
git checkout
```

The downloaded skill is now in `claude/alliance-hpc/`. Git also checks out the
repository's top-level documentation, but leaves the other skills out.

**Want both versions in one checkout?** From the Codex checkout, run:

```bash
git sparse-checkout add claude/alliance-hpc
```

Each skill folder is self-contained and can be copied out of the checkout. Follow
[Install the selected folder](#install-the-selected-folder) below to make it
available to your agent.

## Install the selected folder

From the checkout, choose one command block for each agent you use. These
examples refuse to overwrite an existing installation, including a dangling link.

Codex:

```bash
(
  set -eu
  destination="$HOME/.agents/skills/alliance-hpc"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    printf 'Already installed; inspect before updating: %s\n' "$destination" >&2
    exit 1
  fi
  mkdir -p "$HOME/.agents/skills"
  cp -R codex/alliance-hpc "$destination"
)
```

Claude Code:

```bash
(
  set -eu
  destination="$HOME/.claude/skills/alliance-hpc"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    printf 'Already installed; inspect before updating: %s\n' "$destination" >&2
    exit 1
  fi
  mkdir -p "$HOME/.claude/skills"
  cp -R claude/alliance-hpc "$destination"
)
```

For project installation, use `.agents/skills/` and `.claude/skills/` in the target
project instead. With a ZIP, extract it and use `alliance-hpc` as the copy source.
To update, compare the new bundle with the installed copy and back up local edits
before replacing it. Installed copies do not update automatically.

Invoke with `$alliance-hpc` in Codex or `/alliance-hpc` in Claude Code. Matching
requests can also select the skill automatically. See the official installation
guides in [Authoritative guidance](#authoritative-guidance) for cloud products, which use their own installation mechanisms.

## Authoritative guidance

Last reviewed **2026-09-27**. Maintain these links and our conventions as guidance
evolves; the date records a review, not a promise that upstream pages are unchanged.

| Source | What to consult it for |
|---|---|
| [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Concise descriptions, conditional reference loading, and avoiding excessive instructions. |
| [OpenAI: Codex skills](https://developers.openai.com/codex/skills) | Discovery, installation locations, portable structure, and optional Codex metadata. |
| [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Context efficiency, progressive disclosure, reliable helpers, and behavioral evaluations. |
| [Anthropic: Claude Code skills](https://code.claude.com/docs/en/skills) | Installation, invocation, frontmatter, and Claude Code-specific capabilities. |
| [Agent Skills specification](https://agentskills.io/specification) | Shared directory format, metadata constraints, and portable resource conventions. |

Our working rules are in [CONTRIBUTING.md](CONTRIBUTING.md). Shared principles:
precise triggers, concise entrypoints, references loaded only when needed, and
behavioral evidence for effectiveness claims. Repository size targets are local
preferences; they are not universal vendor requirements.

When updating guidance, check the primary page, update this review date and any
affected authoring rules, then regenerate both versions and run relevant checks.
Record meaningful changes in the Git commit; do not copy whole vendor manuals into
every skill. The Alliance cluster-source audit has its own separate date.

## Build individual ZIPs

You can also build separate ZIP downloads from a full checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/skills.py package alliance-hpc
```

This writes `dist/alliance-hpc-codex.zip` and `dist/alliance-hpc-claude.zip`.
Use `--target codex` or `--target claude` for one version. Each archive has a single
`alliance-hpc/` folder and its own `SHA256SUMS`. CI also builds downloadable ZIPs:
open a successful [Check skills workflow run](https://github.com/bbuchsbaum/brbskills/actions/workflows/check.yml)
and download its `individual-skill-downloads` artifact. The artifact contains one
ZIP per skill and product. No release download is required for the sparse-checkout
method above.

## Maintain both versions

```text
skills/<name>/                        Independent skill source
collections/<group>/skills/<name>/    Skill source maintained within a collection
collections/<group>/shared/           Authoritative shared resources for that group
codex/<name>/                         Generated, self-contained Codex version
claude/<name>/                        Generated, self-contained Claude Code version
scripts/skills.py                     Sync, validation, and individual ZIP packaging
```

Edit the appropriate source, then run `python scripts/skills.py sync`. This also
refreshes each collection's shared resources in its member skills. Commit the
source and both generated folders together. `python scripts/skills.py check` fails
on shared-resource drift, duplicate skill names, missing files, or stale checksums.
Both versions use identical workflow text;
Codex additionally receives `agents/openai.yaml` when supplied. There are no
separately maintained copies of the instructions.

See [CONTRIBUTING.md](CONTRIBUTING.md) for authoring and checks, and the
[Alliance HPC](docs/imports/alliance-hpc.md),
[fMRI Workbench](docs/imports/fmri-workbench.md),
[fMRIPrep](docs/imports/fmriprep/IMPLEMENTATION.md),
[COBIDAS](docs/imports/cobidas.md), and
[visual hill climb](docs/imports/visual-hill-climb.md) import records for provenance and validation limits.
The repository uses standalone skill folders for selective Git downloads. Native
plugin packaging can be added if marketplace installation is wanted.

## License

A repository-wide license has not yet been selected. The imported fMRI Workbench
skills retain their [MIT license](collections/fmri-workbench/LICENSE), included in
each standalone download. That license does not apply to unrelated repository
content or the Alliance HPC skill.
