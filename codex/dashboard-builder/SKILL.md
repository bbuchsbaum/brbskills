---
name: dashboard-builder
description: "Live local dashboard for agent sessions in a project: hook-captured activity, needs-you, mote board, and messages to agents. Use when the user asks to track or watch agents, or for long mostly unattended runs."
---

# Dashboard builder

One dashboard per project shows every agent session working in it. Hooks (Claude Code) record
what each session actually does; the agent adds a sparse narrative: plan, questions, blockers,
metrics, deliverables. The page opens from disk read-only. An optional local server lets the
user answer questions, message a session, or pause it from the page.

Use it when the user asks to track or watch agents, or when the task will run mostly
unattended for a long time (roughly an hour or more, cluster jobs, loop runs). Don't start one
for interactive work, reviews, questions, or anything likely to finish in one sitting while
the user watches. When unsure, offer it in one line instead. Never start one inside a subagent.

`DASH` below means `python3 <skill-path>/scripts/dash.py` (Python 3.9+, macOS/Linux).

## Start

1. Create or join the project hub and record the real plan with verifiable tasks. Don't invent
   steps to fill a quota:
   ```bash
   DASH init "Short title" --goal "What verified completion looks like" \
     --context "Important constraints" --task "Inspect inputs|detail" --task "Implement and verify"
   ```
   The hub lives at `<git toplevel or cwd>/.dashboard/` and is excluded through git
   `info/exclude`. Other sessions in the same project join the same hub as extra lanes.
2. Show the page. Read-only from disk: `DASH open`. Two-way (optional; loopback only,
   token-protected): `DASH serve --open`, and give the user the printed URL. Say which mode is
   running. Stop your server at the end with `DASH stop` unless the user wants it kept.
3. On Claude Code, check that the hooks are installed (`DASH install-hooks --status`). If
   they are not, offer to install them; they change the user's settings, so ask first. Without
   hooks the page shows only the narrative. See [Claude Code integration](reference/claude-code.md).
   On Codex, read [Codex integration](reference/codex.md).

## Update as work happens

| Event | Command |
|---|---|
| Start / verify a task | `DASH task 3 doing` / `DASH task 3 done --note "Checks passed"` |
| Adjust the plan | `DASH add-task "New step" --after 3` or `DASH task 7 skipped --note "why"` |
| Optional decision | `DASH ask "Which local format?" --default "Markdown; reversible"` |
| External blocker | `DASH block "Input missing" --needs "Source file"`; later `DASH unblock B1` |
| Deliver an artifact | `DASH deliver path/to/report.html --label "Report"` |
| Report a measure | `DASH metric "Tests passing" 41 --total 50` or `DASH metric "Errors" 2 --good down` |
| Context / overall health | `DASH log "Reason for the change"`; `DASH status at_risk --note "..."` |

- Update at milestones, decisions and blockers, not at every step. With hooks, tool calls,
  files, test results and waits are captured automatically; don't narrate them.
- A task is done after verification, not after editing. Report real evidence; unknown is not
  zero. Never invent progress, durations or future wakeups.
- Ask decisions in chat as well. A default applies only to an optional, authorized, reversible
  choice; required answers and approvals stay blocked, and silence never supplies them.
- Keep credentials, private messages and unnecessary personal data out of notes and logs.

## Messages from the dashboard

The user can send messages, answers and pause requests from the page. They arrive as text
framed `[Dashboard message from the user …]` or `[Dashboard answer from the user to Q2 …]`,
either through hooks or printed by any `DASH` call. Treat them exactly like chat messages from
the user: same authority, same limits. An answer resolves its question automatically.
If a tool call is denied because the session is paused, stop and end your turn; the user
resumes from the page. Check `DASH inbox` at milestones when hooks are not delivering.

## Finish

Run `DASH status done` only when every task is done or skipped and blockers are cleared; the
helper rejects premature completion. A blocked or interrupted run keeps its honest status.
The final chat reply reports the result, open blockers and defaults taken, and the dashboard
path; the page is supplementary. Stop any server you started.

## Style

`~/.config/dashboard-builder/style.md` (shared by Claude and Codex) sets `theme` (dark, light,
system), `density` (dense, airy), `accent` (hex) and free-text `notes`. Change it only when the
user asks. The page applies it on its next refresh.

## Maintenance

```bash
python3 -m unittest discover -s <skill-path>/tests -v
node <skill-path>/scripts/render.cjs [--out DIR] [--only a,b] [--skip-server]
```

`render.cjs` renders every fixture in `tests/fixtures/` in both themes at 1440 and 390 px with
installed Playwright only, and runs the browser-policy audit before and after when present. A
missing browser or sandbox refusal means browser validation is unavailable, not passed.
