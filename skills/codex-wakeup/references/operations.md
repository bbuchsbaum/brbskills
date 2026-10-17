# Operations

Contents: [setup](#setup), [activation](#activation), [recovery](#recovery),
[guarantees](#guarantees-and-limits), [portability](#portability).

## Setup

Keep the entire skill at a stable installed location. The helper uses Python's
standard library and never searches private app-release directories, invokes
`exec/resume`, starts an app server, or supplies model/permission overrides.
Resolve a stable installed `codex` executable and inspect `codex queue --help`
on the actual host. Use an existing, working local app-server connection.
Remote endpoints and custom credential bootstrapping are outside this version.

Examples use shell variables solely to shorten commands. Replace all values;
do not copy the example UUID as a real destination. Use the actual absolute
Python/helper paths. `init` snapshots the prompt, so later edits to its input
file do not silently change the running mandate.

```sh
WAKEUP_PYTHON=/absolute/path/to/python3
WAKEUP_HELPER=/absolute/path/to/codex-wakeup/scripts/wakeup.py
WAKEUP_THREAD=00000000-0000-0000-0000-000000000001
WAKEUP_STATE=/absolute/private/state/codex-wakeup

"$WAKEUP_PYTHON" "$WAKEUP_HELPER" --state-root "$WAKEUP_STATE" --thread "$WAKEUP_THREAD" init \
  --project /absolute/project --prompt /absolute/approved-prompt.txt \
  --codex /absolute/path/to/codex --hours 8
"$WAKEUP_PYTHON" "$WAKEUP_HELPER" --state-root "$WAKEUP_STATE" --thread "$WAKEUP_THREAD" status
"$WAKEUP_PYTHON" "$WAKEUP_HELPER" --state-root "$WAKEUP_STATE" --thread "$WAKEUP_THREAD" install
```

The state root defaults to `~/.local/state/codex-wakeup`; explicitly choose a
private, durable directory writable by both cron and the receiving agent. Keep
it out of Git and shared/network filesystems. The helper rejects roots with
group/other permissions or a symlink as the final component. Use a single root
for all alarms on this host. One canonical UUID keys each thread's state.

`install` previews the resulting crontab as JSON. Inspect the exact marked entry
and preservation of unrelated jobs. The interval defaults to five minutes;
`init --minutes` accepts divisors of an hour. The absolute deadline starts at
initialization. `--hours` is required, finite, and positive. The expiry bounds
future submissions; it cannot forcibly terminate work already in progress.

## Activation

Once the scheduled run is authorized, use `install --apply`, then `enable`, then
`tick`, with the same global arguments as above. `install` alone never enables
delivery. `tick` sends at most one message. Verify the visible token in the
correct conversation, the end-of-turn acknowledgement, and a stopped tick that
submits nothing. Resume with `enable` only within the approved deadline.

Record host, exact thread, helper version/hash, state root, deadline, owning user,
cron line, and live result in the existing project handoff/Mote record. The
helper does not send peer messages or modify Mote itself. Each project/worker
has its own prompt and thread; cron supplies no coordination semantics.

`status` excludes prompt text and reports enabled/expired state, outstanding
token, submission status, and the last 50 lifecycle events. It does not prove a
cron entry still exists; inspect `crontab -l` separately. Queue stdout/stderr
are discarded to avoid copying prompts or credentials into logs; exit codes
and exception types are retained. Helper failures go to stderr (cron mail if
configured). Configure host monitoring separately if unattended availability
matters; do not claim cron mail is a guaranteed alert.

At the end of a receiving turn, use the exact command embedded in the message:

```sh
"$WAKEUP_PYTHON" "$WAKEUP_HELPER" --state-root "$WAKEUP_STATE" --thread "$WAKEUP_THREAD" finish \
  --token ACTUAL_PENDING_TOKEN --outcome continue
```

`continue` clears only the matching token and imposes one interval of cooldown.
With five-minute cron ticks, the next submission is normally five to ten minutes
after acknowledgement. `stop` and `blocked` also disable the alarm. Finishing
never re-enables a user-disabled alarm or changes the deadline.

## Recovery

`disable` prevents later submissions and retains an outstanding token. Use
`remove` to preview deletion of the exact marker; `remove --apply` disables
first, then removes that entry, retaining all state and unrelated jobs. If the
cron edit fails, the alarm remains disabled. These commands do not cancel an
accepted message. Never delete state or lock files while any producer is live.

For an outstanding `submitting`, `uncertain`, or unacknowledged `accepted` token:

1. Disable; inspect the intended conversation, queue, and owned process state.
2. If it arrived, let the receiving turn finish with its token. If an old message
   arrives after disable, it must skip project work; reconcile it once consumed.
3. Only after establishing that no old submission, queued message, or receiving
   turn remains, use `recover --token TOKEN --confirmed-not-pending`. This leaves
   the alarm disabled. If delivery cannot be determined, leave it disabled and
   report the ambiguity. Never probe by resending the original command.
4. Enable again only within the existing authorization. After expiry, a newly
   authorized duration can be set with `renew --hours N`, then `enable`. Renewal
   rejects an outstanding attempt and leaves disabled until explicitly enabled.

For a changed mandate, disable/remove and reconcile first, archive the old
thread directory as evidence once no producer is live, then initialize afresh.
Do not use a second root to evade an outstanding token or expired boundary.
Migration from the original helper also requires draining its already queued
prompts. Never install both producers for the same thread.

## Guarantees and limits

The helper writes an outstanding token atomically and fsyncs it **before** invoking
queue. A per-thread advisory lock serializes commands and is passed to the CLI
child. A killed parent cannot free that lock while its child is still submitting.
Ticks use a nonblocking lock and skip busy submissions. A hung queue has a
bounded timeout (30 seconds by default); all uncertain outcomes retain the
reservation. A crash before submission may therefore stall a run without sending
anything. This trades automatic recovery for protection against duplicate work.

Status reads an atomic snapshot without waiting for the submission lock. Other
commands report busy immediately rather than hang behind an orphaned CLI child;
retry after the submission ends. If a crashed parent leaves a hung child, inspect
the specific owned process before intervention. Never delete its lock file to
force progress. A failed/busy disable is not a confirmed stop.

This is one outstanding helper attempt, not server-side exactly-once delivery.
It depends on durable local storage, one state root/producer, and acknowledgement
only at turn end. It cannot deduplicate another producer or inspect Codex's
internal queue, detect an unrelated active turn, enforce the model's behavior,
or stop inference at the deadline. At most one helper message can sit behind an
unrelated long turn. A premature acknowledgement can defeat this guarantee.

Crontab edits use an exact end-of-line UUID marker, serialize this helper's
writers, compare before writing, and verify readback. Crontab has no portable
compare-and-swap: coordinate with other editors during install/remove. A failure
to read the existing table aborts; it never implies an empty table.

## Portability

macOS/Linux only: `fcntl.flock`, local filesystem fsync, Python 3.10+, and cron.
The cron line shell-quotes paths and escapes cron's special `%`; newline paths
are refused. Run as the same OS user as the working Codex client. The saved
HOME, CODEX_HOME, working directory, and a small explicit PATH avoid dependence
on interactive shell startup files. Existing nonstandard app-server discovery,
keychain access, or socket permissions may still differ under cron: the live
test must use cron's actual environment. An interactive successful tick alone
does not prove cron delivery. A sleeping/offline host misses ticks; there is no
catch-up queue. Recheck capability and delivery after CLI/app upgrades.
