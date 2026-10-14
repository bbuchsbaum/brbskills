# Local CLI pilot readiness review

## Verdict

**No-go for the documented local CLI pilot at `pilot-candidate-1`.** The summary core is implemented and its component tests pass, but the public command named in the README ignores its input by default. It returns the demo mean (`2`) for the provided file, whose required mean is `10`, and it reports success for a missing file. That contradicts both accepted pilot requirements.

This is a read-only local assessment of the supplied fixture. The fixture is not a Git worktree, so no revision or dirty-state receipt is available. It was run with Python 3.14.7, which meets the stated Python 3.10+ floor. No network or external services were accessed. The shell emitted an unrelated RVM `ps` permission warning before commands; the Python commands completed and produced the receipts below.

| Claim / source | Implementation | Evidence / receipt | Consequence / next gate |
|---|---|---|---|
| RC-01: `python3 main.py readings.json` reports that file's count and mean (README; accepted scope) | partial | **Contradicted by execution:** documented command returned `{"count": 3, "mean": 2}`; `readings.json` is `[4, 10, 16]`, so its mean is 10. `main.py` defaults `--backend` to `demo`, which substitutes `[1, 2, 3]`. | Blocks pilot: the advertised invocation does not consume the user's file. |
| RC-02: missing or invalid input fails clearly with nonzero exit (README; accepted scope) | partial | **Contradicted by execution for missing input:** `python3 main.py missing.json` returned the same demo JSON and exit 0. The latent `--backend file` path gives a clear missing-file error and exit 2. | Blocks pilot: the documented invocation violates the error contract. |
| RC-03: nonempty finite-number arrays are summarized correctly (README) | connected | **Supported by inspection and component execution:** `summary.py` validates a nonempty list of finite built-in numbers and uses `statistics.mean`; all three `checks/test_summary.py` tests passed. The explicit file backend returned `{"count": 3, "mean": 10}` for the supplied file. | Preserve this validation and summary core; it is a suitable basis for the CLI. |

The narrow countercase is that a caller can add `--backend file`; the representative run then satisfies the valid-file result and missing-file failure. That is not enough for this decision because README explicitly specifies the command without that option, and accepted scope requires the user's file under that pilot interface.

## First executable action

**RC-01/02 — Make the documented invocation use the supplied file.** Change the CLI so its default path reads the positional input (remove the demo default or make `file` the default), then add subprocess-level regression checks for exactly:

```sh
python3 main.py readings.json       # stdout JSON: {"count": 3, "mean": 10}; exit 0
python3 main.py missing.json        # stderr begins "error:"; nonzero exit
```

Acceptance is the two outcomes above on Python 3.10+ plus the existing summary tests. The web dashboard and hosted service are explicit non-goals for this pilot. A rerun that produces those receipts would change this recommendation to ready for the bounded local CLI pilot; broader input compatibility and deployment are unexamined.

## Evidence artifacts

`commands.json` records the commands, directories, statuses, and outputs. No project files were changed. `selected-files.json` records the constrained review surface.
