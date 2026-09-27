# alliance-hpc

A portable Codex / Claude Code skill for productive, policy-aware data analysis on **Trillium, Nibi, Fir, Rorqual, and Narval**. Cluster-source audit: 2026-09-21. Packaging and local safety fixes: 2026-09-27.

This folder is self-contained. In brbskills, edit the canonical `skills/alliance-hpc/`
and regenerate the `codex/` and `claude/` downloads. Codex bundles additionally
include `agents/openai.yaml` for display metadata; both share the same instructions.
Generated bundles include `SHA256SUMS`; verify from this directory with
`shasum -a 256 -c SHA256SUMS` (or `sha256sum -c SHA256SUMS` on Linux).

`SKILL.md` is the small operational core. Detailed sources, cluster differences, submission recipes, and the qexec audit are read only when needed. The package does not install software, change SSH configuration, submit jobs, or modify qexec merely by being loaded.

## Install once, expose to both agents

Unzip the download, then run this **from the directory containing `alliance-hpc/`**. The script below refuses to replace an existing installation. Inspect the files first.

```bash
set -eu
base="$HOME/.local/share/agent-skills"
skill="$base/alliance-hpc"
codex="$HOME/.agents/skills/alliance-hpc"
claude="$HOME/.claude/skills/alliance-hpc"
for p in "$skill" "$codex" "$claude"; do
  if [ -e "$p" ] || [ -L "$p" ]; then
    printf 'Already exists; inspect before updating: %s\n' "$p" >&2
    exit 1
  fi
done
mkdir -p "$base" "$HOME/.agents/skills" "$HOME/.claude/skills"
cp -R alliance-hpc "$skill"
ln -s "$skill" "$codex"
ln -s "$skill" "$claude"
```

For repository-scoped use, place the skill under `.agents/skills/alliance-hpc` and `.claude/skills/alliance-hpc`, or link both to a checked-in canonical directory. Relative symlinks are preferable inside a repository. Avoid duplicate same-name installations that point at different versions. These are local **Codex and Claude Code** instructions, not a promise that a browser/cloud session reads the laptop's home directory. Official installation sources: `references/sources.md`.

Invoke in Codex with `$alliance-hpc` or in Claude Code with `/alliance-hpc`, or ask a matching task. For example:

> Use alliance-hpc to prepare a 120-subject R analysis. Compare legal placements on Trillium, Nibi, Fir, Rorqual, and Narval using current access, cached data, and representative timings. Dry-run first; do not submit until the pilot plan is reviewed.

The user prompt governs authorization; the skill does not imply permission to run that campaign.

## Included

| File | Purpose |
|---|---|
| `SKILL.md` | Compact operating contract and routing |
| `references/systems.md` | Five-cluster map, Trillium GPU branch, drift checks |
| `references/submission.md` | Native CPU, array, packed-work, dependency, GPU/MPI recipes |
| `references/operations.md` | Storage/S3 caches, offline environments, queue diagnosis, recovery |
| `references/qexec.md` | Audit of the actual Bash wrapper and helper behavior |
| `references/sources.md` | Primary sources, hashes, conflicts, and verification gaps |
| `scripts/probe.sh` | Bounded read-only cluster/account/resource/storage snapshot |
| `scripts/array-task.sh` | Safe data-only array manifest dispatch |
| `templates/cpu.sbatch` | One-node / one-task launcher with explicit environment and thread budget |
| `tests/test_skill.py` | Local syntax, safety and mocked-execution tests |
| `tests/VALIDATION.md` | Test results and untested boundaries |
| `tests/evaluation-cases.md` | Unrun behavior scenarios for both products |

## Use the probe

Run on an authorized target login host, not on the laptop. `WORKDIR` must already exist. It does not probe external network access, change files, submit/cancel jobs, or expose the full environment. It prints diagnostics only. Some command fields are version-dependent; failures are shown and return code 2 means incomplete evidence.

```bash
# After installing/copying the inspected probe onto the target host:
umask 077
bash /absolute/path/alliance-hpc/scripts/probe.sh /absolute/workdir \
  > /private/path/cluster-profile.txt
```

Capture the profile on durable authorized storage, outside the dataset's public outputs. An optional `ALLIANCE_PROBE_QOS=verified-qos` scopes one QOS query. Do not query every cluster repeatedly or paste full snapshots into every agent turn; retain a short selected-profile summary. The snapshot cannot establish all inherited policy limits, scratch retention, robot authorization, or compute-node mounts.

## Validation and honesty

Run `python3 tests/test_skill.py` locally. The shipped checks require Bash and Python 3; they do not require Slurm and never submit a job. Tests establish helper behavior under mocks, not acceptance by a live Alliance scheduler.

The Alliance wiki blocked full-page retrieval during authoring. Accessible operator pages, institutional operational documentation, upstream Slurm manuals, and the exact qexec source were inspected. Facts based only on indexing or software configuration are labelled. Current account permissions, walltime/QOS limits, quotas/purge rules, GPU slices, and site-specific automation access **must still be verified on the target**. The skill is designed to perform that verification rather than quietly reuse obsolete constants.
