# Validation — 2026-09-28

## Local evidence

- Record helper: 30 synthetic tests pass, including scientific/execution revision
  separation, stale approval, altered artifacts, normalized script binding,
  duplicate attempt, submission-token and target/job-ID detection, rejection of
  identity values with surrounding whitespace, job-ID versus submission-state
  consistency, required process status, literal empty argv/env values, completed
  bundled example shapes, a size cap enforced on a FIFO, and CLI exit 2 with a
  one-line reason for malformed, non-UTF-8, oversized or deeply nested JSON and
  symlink loops.
- Host probe: 32 tests pass, including the 13 imported behaviors, capped output
  without cleanup errors, closed-pipe timeouts, descendant cleanup, real SIGINT,
  SIGTERM and SIGHUP delivered to the CLI mid-probe (exit 128+signal, fake child
  stopped), a deterministic signal inside process creation (child group still
  stopped), a signal at every handler install/restore position (delivered once,
  handlers restored), a stuck leader reported as `cleanup_status: incomplete`
  without masking a timeout, TERM-ignoring timeouts reported as complete cleanup,
  ignored SIGHUP left ignored (nohup), symlink-loop paths reported rather than
  raised, and an end-to-end `--versions` run proving qsub/bsub are located but never run.
  Temporary executables are synthetic; tests do not invoke installed fMRIPrep or
  a scheduler.
- Helper suites were run on macOS with CPython 3.10.18, 3.12.11 and 3.14.7, five
  times each without flakes. Randomized SIGTERM stress runs of the real CLI
  (300 iterations on 3.12, 150 each on 3.10 and 3.14; 405 fake children started)
  left none surviving. The Linux-only paths
  (`os.waitid(WNOWAIT)` leader retention; no pre-SIGKILL reap) were checked by
  reasoning only; the Ubuntu hosted-CI job would run them but has not yet been run.
- Ten independent synthetic task exercises reviewed: wrapper absence, whitespace
  argv, unknown submission, metadata inheritance, module-wrapped container, offline
  assets, PBS blocker, stale approval, pilot reuse and unavailable QC. Captured
  argv/env match supplied values; unknown submission produced no duplicate submit.
  One fresh-context Codex subagent performed four cases, then six in the same
  continued session, without the rubric. Exact model build was not pinned.
- A later hardening pass ran fresh Claude subagents on 13 further cases (7 on the
  pre-hardening text, then 9 including 3 reruns and 3 new high-risk cases on the
  revised text): all rubric passes, no critical failures. Final wording edits after
  that run were not re-exercised. On 2026-09-30 the three remaining cases
  (host-compute-difference, fieldmap-ambiguity, arm-host) passed, and four
  launcher-dependent reruns after the rriscripts refresh passed; all 26 cases have
  now run at least once, each as a single sample. None of this is a Codex/Claude
  product-session comparison or no-skill baseline.
- Separate read-only review reproduced a probe cancellation leak and nonfinite JSON
  parsing; both were repaired and rechecked. An actual SIGINT regression and an
  injected read-error regression now exercise cleanup.
- Root packaging regression runs both helper suites in independently extracted
  Codex and Claude ZIPs with isolated Python imports and no sibling skills.
- Repository sync/check, 24 root tests, 42 Workbench tests and its collection audit,
  skill frontmatter validation, and diff whitespace checks passed. Hosted CI was
  not run. Root tests include the two-product isolation regression.

## Reproduce

### Commit-review follow-up

The cancellation reporting path was subsequently repaired: interrupting a probe
whose cleanup fails now retains the failure and cause instead of claiming the
group stopped. The current suite has 64 helper tests (34 host-probe, 30 record).
The two added tests cover SIGINT/SIGTERM combined with cleanup timeout/OSError,
and interruption with no cleanup evidence. The 62-test multi-version and stress
runs above describe the earlier snapshot, not this follow-up. Current checks and
source hashes are recorded in the repository import notes.

```bash
python3 -m unittest discover -s tests -v
```

Run from this skill directory. Only Python 3.10+ standard library is required for
helpers/tests. Opt-in version probes require POSIX; the default inventory is local
observation only. [Behavioral cases](evaluation-cases.md) need separate agent
execution and do not run as part of unittest.

## Limits

Record checks establish declared identity/byte consistency, not authentic consent,
scientific correctness, resource entitlement or launch readiness. References to
manifests bind their bytes, not every underlying image. Unknown scheduler state
still requires reconciliation; supplying distinct IDs cannot prove safe retry.

Version probes are bounded for their direct processes and attempt cleanup of the
owned POSIX process group, including when the helper receives SIGINT, SIGTERM or
SIGHUP in the main thread, during process creation or while handlers are installed
or restored (such signals are deferred, then delivered once). SIGINT is handled
only while it has Python's default handler; a caller's own SIGINT handler is left
alone. A child that creates a separate session can escape, and SIGKILL of the
helper cannot run Python cleanup. Called from a non-main thread, signals keep
their default behavior. On Linux the exited leader stays unreaped until its group
is signalled, so its group ID cannot be reused; elsewhere the leader is reaped
before the final group signal, leaving a small PID-reuse window. A leader stuck in
uninterruptible I/O (for example a hung network mount) is reported as
`cleanup_status: incomplete` with `leader_reaped: false`; an earlier `error` such
as `timeout` is kept. Arbitrary PATH wrappers are not a security sandbox.
Remaining cleanup errors stay visible in `cleanup_error`.
On interruption, the CLI reports the retained cleanup outcome and any cause on
stderr, preserving exit status 128+signal. Missing evidence is reported as
unverified cleanup, never as successful cleanup.

No real BIDS dataset validation, fMRIPrep execution, container runtime or live
scheduler qualification is claimed. Full Codex/Claude product-session evaluation,
automatic selection, no-skill comparisons and hosted CI remain separate unrun
gates unless explicitly recorded. Package size is not behavioral evidence.
