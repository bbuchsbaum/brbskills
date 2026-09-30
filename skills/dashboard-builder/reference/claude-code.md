# Claude Code integration

Read this when setting up the dashboard in Claude Code, or when messages, lanes or activity
don't appear as expected.

## What the hooks do

`scripts/dash_hook.py` handles every hook event. It does nothing (and exits within tens of
milliseconds) unless a `.dashboard/hub.json` exists at or above the session's working
directory, so a user-level install is safe for projects without a dashboard.

| Event | Records | Delivers |
|---|---|---|
| SessionStart | new lane; exports `DASH_SESSION` through `$CLAUDE_ENV_FILE` | — |
| UserPromptSubmit | prompt excerpt | queued messages (additionalContext) |
| PreToolUse | the in-flight tool, shown live on the page | pause: denies tool calls |
| PostToolUse / PostToolUseFailure | tool, target, duration, exit status, parsed test results | queued messages (additionalContext) |
| Notification | permission and idle waits ("needs you") | — |
| Stop | turn end | undelivered messages (blocks the stop once) |
| Stop, async (optional) | — | wakes an idle session when a message arrives |
| SubagentStop, SessionEnd | subagent and session ends | — |

Command lines, prompts and outputs are redacted for common secret patterns and truncated
before storage; full tool outputs are never stored. Everything stays in `.dashboard/`.

## Install

Installing edits the user's Claude settings, so ask before doing it.

```bash
DASH install-hooks --status                 # installed? which events? rewake?
DASH install-hooks --dry-run                # show only the hook entries that would change
DASH install-hooks --scope user             # ~/.claude/settings.json, with a timestamped backup
DASH install-hooks --scope project          # .claude/settings.local.json in this project
DASH install-hooks --scope user --with-rewake   # also wake idle sessions
DASH install-hooks --scope user --uninstall
```

The installer merges idempotently, preserves existing hooks, and identifies its own entries
by script path. Hooks load when a session starts; sessions already running need a restart.

## Delivery, verified live (Claude Code 2.1.285 and 2.1.286)

- Working session: the message arrives after the next tool call (PostToolUse).
- Idle session with `--with-rewake`: an async Stop hook waits for messages and wakes the
  session with the message, usually within a second. From 2.1.286 the wake-up turn starts with
  a synthetic prompt carrying that message; the hooks recognise it and do not deliver twice. Without it, the message arrives with
  the user's next prompt in that terminal. The page says which applies.
- Pause: PreToolUse denies tool calls with a reason naming the dashboard; `dash.py` calls stay
  allowed. Resume from the page.
- Permission prompts cannot be answered from the page; the user approves in the terminal.

## Session binding

`dash.py` finds its session from `--session`, then `$DASH_SESSION` (set by the SessionStart
hook), then the in-flight Bash command recorded by PreToolUse. An `init` run before the hooks
knew the hub creates a CLI lane that the Claude session adopts on its next hook event; the old
id keeps working. If a call is ambiguous, `dash.py` refuses and lists sessions instead of
guessing.

## Troubleshooting

- No lane for a session: hooks not installed, or the session started before installation.
- Nothing updates: check `.dashboard/hook-errors.log` (bounded) and `DASH show`.
- Server URL lost: `DASH url` prints the tokenized URL of the running server (share it only
  with the user), or says that no server is running.
