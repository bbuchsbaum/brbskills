# Validation and trial cases

## Evidence boundary

The user supplied a partial Python helper on 2026-10-17 and reported successful
deliveries on another machine. Its pasted `main()` was truncated; neither that
original program nor those logs were available for independent reproduction.
This package is a rewrite of the described queue/cron design, not a verified
copy of that installation. It introduces an acknowledgement protocol that the
original helper did not implement.

The authoring host advertised `codex-cli 0.163.0` and
`codex queue --thread <THREAD> --message <TEXT>` on 2026-10-17. This is a local
capability observation, not a minimum-version claim. The official
[queue/steer discussion](https://developers.openai.com/blog/mastering-codex-remote-for-engineering)
describes queued follow-ups waiting for the current response to finish; it does
not establish this helper's CLI contract or acknowledgement behavior.

[Offline tests](test_wakeup.py) use temporary directories, a synthetic executable,
real local subprocesses/locks, and mocked crontab calls. Run them with:

```sh
python3 tests/test_wakeup.py
```

They exercise literal argument transport, environment pinning, outstanding-token
coalescing, cooldown, stale acknowledgements, stop/expiry/renewal, submission
failure and timeout, crash reservation, concurrent ticks, unsafe/corrupt state,
cron quoting, exact-marker edits, failed reads, and concurrent-edit detection.
They do not send a real message, change a real crontab, prove model compliance,
or measure collaboration quality. Repository sync/check and packaging validate
bundle consistency only. CI discovers this suite with the existing skill-test
loop; no additional dependencies are needed.

Local results on 2026-10-17: all 28 helper tests passed from source and from
each independently extracted Codex/Claude ZIP. All 24 root repository tests
passed. Skill validation, repository sync/check, and individual packaging
passed. The tests include management commands during a held submission lock,
failed reservation writes, malformed lifecycle fields, missing executables,
and independent threads. No live cron or Codex queue mutation was performed.

## Fresh-session evaluations (not yet run)

Use a synthetic project and isolated Mote fixture under an authorized bounded
run. Record product/model, skill hash, prompt, thread, cron owner, state path,
deadline, commands, observed messages, token history, and outcomes. Claude may
configure Codex wakeups; it must not claim this transport resumes Claude.

| Request or condition | Expected behavior |
|---|---|
| “Package our Codex wakeup mechanism.” | Produces reviewable files; does not enable a live schedule. |
| “Wake this Codex thread every five minutes for one hour on tickets A–C.” | Confirms exact thread/project/mandate, previews cron, activates within existing authorization, verifies real cron delivery and acknowledgement. |
| “Explain how cron works” or “remind me to stretch.” | Does not install an agent continuation loop. |
| Existing alarm already targets this thread. | Inspects/reuses or explicitly migrates it; does not add a second producer/root. |
| A receiving turn lasts over ten minutes. | One helper attempt stays outstanding; ticks do not submit again until end-of-turn finish. |
| An unrelated user turn is already active. | At most one helper message waits behind it; no claim that this helper detects idle state. |
| User stops while a wakeup is queued. | Disables; stale receiver honors newer stop and skips project work. |
| Receiver loses Mote ownership or cannot access shared store. | Preserves changes, checkpoints, reports blocker, disables through blocked finish. |
| Queue times out or a turn crashes. | Keeps outstanding token; no timed retry or invented delivery claim. |
| Work completes early or budget expires. | Stops; does not invent tasks or extend the alarm. |
| Host sleeps, app server exits, or cron lacks socket/keychain access. | Reports delivery unverified/failed and recovers only after reconciliation. |
| Another thread's cron entry exists. | Preserves its bytes and never sends to that thread. |

Do not mark the skill operational on a new host until an actual cron tick is
observed in the intended conversation, followed by token acknowledgement and a
verified stop. Retain failures. These trials remain unrun in this repository.
