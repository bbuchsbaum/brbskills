# Validation report

## Repository import validation — 2026-09-27

**41 tests passed** as one full run on macOS with Python 3.12 and GNU `timeout`.
ShellCheck also passed for both helpers and the CPU template. The portable skill
frontmatter passed the Codex skill-creator validator. No cluster was contacted.

Added regression coverage verifies that failed preflight prevents submission,
nonzero submission status with numeric output remains ambiguous, malformed receipts
are rejected, successful receipts record cluster and job ID, and truncated/timed-out
probe output is marked incomplete while later diagnostics continue. Three targeted
tests reproduced the preflight, submission-status, and truncation defects before
the fixes and passed afterward.

The shared entrypoint is 544 whitespace-delimited body words (previously 900).
This is a size measurement, not a tokenizer benchmark or proof of better model
behavior. The [behavioral evaluation cases](evaluation-cases.md) remain unrun in
fresh Codex and Claude Code sessions. Hosted CI has not run yet.

## Original archive validation — 2026-09-21

The imported report recorded **35 tests passed** in its authoring container,
executed in two groups: 24 array/launcher tests and 11 probe/static tests. No live
Alliance connection or Slurm job was used. The original findings follow.

## Verified locally

- Bash syntax for both helpers and the CPU template, plus every embedded Bash recipe.
- Minimal common skill frontmatter, all five cluster names, core under 1,000 words, and existing relative Markdown links.
- Array dispatch: 1-based IDs, exact argument boundaries, shell metacharacters treated as data, no trailing-newline requirement, rejection of invalid indices/blank rows/CRLF/missing inputs, and payload failure propagation.
- CPU launcher: one node/one task, allocation and CPU-request guards, trusted environment loading, numerical-library thread caps, rejection of excess threads, exact argv preservation, and environment/application failure propagation.
- Probe under mock commands: read-only Slurm call shapes, selected-QOS querying, bounded display, filtered configuration, secret values excluded from environment reporting, invalid-input rejection, and explicit incomplete-evidence status.

## Not established by these tests

Real scheduler acceptance, actual account/partition/QOS entitlements, current queue times or limits, compute-node mounts or egress, module compatibility, GPU/MIG/APU availability, application correctness/scaling, quotas, purge rules, or approved automation access. qexec was source-audited, not submitted to a cluster or replaced by this package. The GNU Parallel recipe must be checked against the installed version.

Initial full-suite runs hit the test harness's short process timeout; increasing the harness timeout and running the groups separately produced the passing results above. This did not reveal or require a change to cluster policies or the probe's per-command time bound.

## Reproduce

```bash
python3 tests/test_skill.py
```

Or run the same two groups used during authoring:

```bash
python3 tests/test_skill.py ArrayTests CpuTests
python3 tests/test_skill.py ProbeTests StaticTests
```

Tests use temporary local files and mocked Slurm tools; no network access or external Python packages are required. GNU `timeout` is required for probe tests, as it is for the Linux-targeted probe itself. Tests for array/launcher logic and static content can also be run separately.
