# Local CLI pilot reassessment

## Verdict

**Continue: ready for the accepted local CLI pilot.** This review assesses the
supplied `pilot-candidate-2` fixture on Python 3.14.7, without network access.
The fixture has no Git metadata, so no revision or local-dirty-state receipt is
available beyond `VERSION`. The accepted 2026-10-12 scope supersedes the
September dashboard requirement: the pilot is the source-local `python3 main.py
<file>` workflow on Python 3.10+.

| Claim / source | Implementation | Evidence / receipt | Consequence / next gate |
|---|---|---|---|
| User file yields count and mean (README; accepted scope) | connected | demonstrated: `python3 main.py readings.json` exited 0 with `{"count": 3, "mean": 10}` | RC-01 from the previous review is resolved: `main.py` defaults to the file backend. |
| Bad, missing, empty, and non-finite input fails clearly (README; accepted scope) | connected | demonstrated: each probe exited 2 and printed an `error:` message; component suite also passed 3/3 | Meets the stated pilot input contract on the exercised cases. |
| Dashboard is required for the pilot (old roadmap; prior RC-02) | not applicable | contradicted as a current prerequisite by `decisions.md`: dashboard and hosted service are deferred | RC-02 is superseded, not an open implementation gap. |

`summary.summarize` is a useful, narrow core: it rejects non-lists, empty
arrays, non-numeric values, and non-finite numbers. `main.py` connects that core
to the documented command and maps expected file/validation failures to a clear
nonzero result. Preserve this small dependency-free path.

## Remaining decisive gaps

None for the accepted local CLI pilot. The component tests do not themselves
exercise the CLI boundary, but this review did so directly for the stated happy
path and four failure classes. The retained `--backend demo` option is outside
the documented pilot route; no accepted requirement says it must be removed.

## Next executable action

Run the documented pilot command against the designated representative user
file: `python3 main.py <pilot-readings.json>`. Accept the pilot gate when its
JSON count and mean match independently checked values; retain the command,
input identity, stdout/stderr, and exit status. Reassess if the pilot needs an
installed/package-distributed command, dashboard, hosted service, or inputs
outside nonempty JSON arrays of finite numbers.

## Limits

This is a bounded local review of the supplied fixture only. It did not inspect
external services, package installation, cross-version Python behavior, or real
pilot data. Those were not required to decide the stated source-local pilot.
