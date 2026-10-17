---
name: codex-wakeup
description: Set up, inspect, or stop bounded cron wakeups into an existing Codex conversation so authorized team work can resume. Uses durable acknowledgement to prevent repeated wakeups from building a backlog.
---

# Codex wakeup

Use cron as a clock, Codex queue as transport, and the project's existing Mote
workflow as authority for work. This skill supplies a reusable helper; it does
not start peers, create a Mote store, expand authorization, or wake Claude.
Claude peers use their own verified continuation mechanism.

Requires macOS/Linux, Python 3.10+, cron, and a Codex CLI advertising
`queue --thread --message` connected to the existing app server.

## Set up a bounded run

Read [operations](references/operations.md) for commands and recovery. Inspect
existing wakeup entries before adding one. Use one host, state root, and alarm
per exact Codex thread UUID; never guess a thread or use a mutable display name.
Remove or disable legacy producers for that thread before activating this one.
Keep other projects' schedules intact.

Record the project, thread, Mote actor/store, approved task/tranche, run deadline,
and stop conditions in a saved prompt using the
[mandate template](assets/prompt.txt). Preserve the project's peer-work protocol.
Confirm the receiver can read and write the private state directory under its
existing sandbox policy. Do not relax permissions to make wakeups work.

Use [the helper](scripts/wakeup.py) to initialize disabled state and probe the
installed CLI. Preview the cron edit. Apply and enable only when the user has
authorized a scheduled run with a concrete mandate and duration. Packaging or
discussing the skill does not authorize activating an alarm. Existing explicit
authorization is sufficient; do not ask again.

During activation, submit one test tick and verify its token appears in the
intended conversation. A zero queue exit means submission was accepted, not
that the receiver ran or completed work. Check acknowledgement and stop behavior
before calling the installation operational. The existing app server and host
must remain available; cron does not wake a sleeping computer or start a new
Codex session. Default cadence is five minutes, with no catch-up burst.

## Receive a wakeup

1. Read helper status first. Verify the token, current conversation UUID,
   project, enabled state, and deadline. Ignore stale, disabled, or expired
   wakeups. Honor newer user instructions and stops.
2. Read applicable project instructions and current Mote ownership, requests,
   claims, and ready work. If coordination is unavailable, report that blocker;
   do not invent a substitute. Continue only authorized work, respecting peer
   reservations, review gates, budgets, and resource windows.
3. At the **end** of the turn, checkpoint useful evidence and run the supplied
   token-bound `finish` command. Choose `continue` for remaining authorized work,
   `stop` for completion/user stop, or `blocked` for a boundary requiring human
   input or repair. A bounded wait for a known peer/job may continue if the
   mandate permits it. Do not fill idle time with invented tasks.

Never acknowledge at the beginning. The outstanding token spans submission,
queueing, and the receiving turn. Further ticks skip it. If the turn crashes or
forgets to finish, wakeups stall for inspection. A timeout or nonzero CLI exit
also retains the token: delivery might already have happened. Do not clear it
on a timer, auto-retry, or renew the run deadline yourself.

## Stop and report

Disable the alarm immediately on a user stop, then remove only its marked cron
entry. Disable does not cancel an already accepted message or interrupt a turn;
the receiver must honor the stop. Preserve state and evidence for recovery.
Report thread, state location, expiry, cron status, and what was actually
verified. See [validation limits and trial cases](tests/VALIDATION.md) before
claiming live delivery, model compliance, or reliable unattended collaboration.
