# Primary sources and maintenance

Inspected 2026-09-28. Resolve documentation to the selected software version before
execution. These are reference addresses, not commands to copy blindly.

| ID | Primary source | Address |
|---|---|---|
| S1 | fMRIPrep usage and CLI | `https://fmriprep.org/en/stable/usage.html` |
| S2 | fMRIPrep spaces / TemplateFlow semantics | `https://fmriprep.org/en/stable/spaces.html` |
| S3 | fMRIPrep installation | `https://fmriprep.org/en/stable/installation.html` |
| S4 | fMRIPrep workflows | `https://fmriprep.org/en/stable/workflows.html` |
| S5 | fMRIPrep outputs | `https://fmriprep.org/en/stable/outputs.html` |
| S6 | fMRIPrep FAQ / indexing / timing | `https://fmriprep.org/en/stable/faq.html` |
| S7 | BIDS common principles / inheritance | `https://bids-specification.readthedocs.io/en/stable/common-principles.html` |
| S8 | BIDS MRI / fieldmap associations | `https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html` |
| S9 | Versioned usage and derivative reuse | `https://fmriprep.org/en/25.2.5/usage.html` |
| S10 | NiPreps Singularity and offline execution | `https://www.nipreps.org/apps/singularity/` |
| S11 | NiPreps Docker execution | `https://www.nipreps.org/apps/docker/` |
| S12 | Apptainer environment and metadata | `https://apptainer.org/docs/user/latest/environment_and_metadata.html` |
| S13 | fMRIPrep 25.2.5 source: CLI parser, changelog, config | `https://github.com/nipreps/fmriprep/tree/25.2.5` (`fmriprep/cli/parser.py`, `fmriprep/cli/workflow.py`, `fmriprep/config.py`, `CHANGES.rst`) |
| S14 | fmriprep-docker wrapper CLI | `https://github.com/nipreps/fmriprep/blob/25.2.5/wrapper/src/fmriprep_docker/__main__.py` |
| A1 | Agent Skills specification | `https://agentskills.io/specification` |
| A2 | Anthropic authoring guidance | `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices` |
| A3 | OpenAI skill authoring and discovery | `https://developers.openai.com/codex/skills/` |
| A4 | Claude Code skills | `https://code.claude.com/docs/en/skills` |

Repository references are pinned to commit
`747775e3da01e3a86e0c7e9462d9fa0c381e2715`:

| ID | Path in bbuchsbaum/rriscripts |
|---|---|
| R1 | `fmriprep/README.md` and `fmriprep/fmriprep.ini.example` |
| R2 | `fmriprep/fmriprep_shared.py` |
| R3 | `fmriprep/fmriprep_backend.py` |
| R4 | `docs/src/content/docs/fmriprep/subcommands.md` |
| R5 | `fmriprep/fmriprep_launcher.py` (CLI, config loading, defaults, container choice, `print-cmd`, `rerun-failed`) and `fmriprep/install.sh` |

Repository base:
`https://github.com/bbuchsbaum/rriscripts/tree/747775e3da01e3a86e0c7e9462d9fa0c381e2715`

That commit is on the unmerged branch `fix/fmriprep-issues-3-5`; the same files were
also compared at `acb0a38` (origin/main, which `install.sh` downloads) on
2026-09-28. See [rriscripts](rriscripts.md) for which behaviors differ. Primary fMRIPrep 25.2.5 usage, outputs, workflows,
spaces and FAQ, and BIDS 1.11.1 inheritance/MRI sources were checked during
adaptation. Use matching documentation for a different selected installation.
See [validation](../tests/VALIDATION.md) for executed checks and unrun gates.

Maintenance: on a dependency change, recheck CLI/method changes, wrapper image
forwarding, path mounts, array packing, and the behavioral evaluations. Keep
stable decision rules in SKILL.md and changing syntax/site facts here or in
versioned execution profiles. Proposed defaults and operational safeguards are
this companion's design, not assertions that the upstream tools enforce them.
