# Agent dashboard 2.0

Status: approved 2026-09-30. Owner: main session. Tracks: backend, page, hill climb, E2E.

## Why

The v1 `dashboard-builder` skill showed only what the agent remembered to report,
could not receive anything from the user, produced one page per run with a different
per-run design, and knew nothing about other sessions or mote. It fired on almost
every task because of a "more than 5 steps" threshold.

## Decisions (user, 2026-09-30)

1. A local server enables two-way messaging. It is **optional**; the page must be
   fully useful read-only from `file://`.
2. The skill moves into brbskills as `skills/dashboard-builder/` (name kept; the per-run
   builder agent is gone). Installed copies link to the generated `codex/` and `claude/` folders.
3. The per-run Opus builder agent is retired. One fixed, versioned, tested page ships
   with the skill. The style file remains for theme, density and accent preferences.
4. Claude Code gets the full loop (hooks: capture + delivery). Codex gets the page,
   narrative commands, and message delivery through `dash.py` output at milestones.

## Verified mechanisms (spike, Claude Code 2.1.285)

- PostToolUse hook `hookSpecificOutput.additionalContext` reached the model mid-turn.
- Stop hook `{"decision":"block","reason":...}` delivered a late message and the model
  acted on it before finishing.
- Idle session (waiting at the prompt): with the optional async Stop hook
  (`"async": true, "asyncRewake": true`, `dash_hook.py --watch-inbox`) a queued message wakes
  the session, verified live in an interactive tmux session: delivered via "rewake" about 1 s
  after posting, and the agent acted on it. Without that hook, queued messages are delivered by
  the UserPromptSubmit hook on the user's next prompt. The page states which applies per
  session (`wakeable`).
- Live E2E (2026-09-30, Claude Code 2.1.285, Haiku, tmux): delivery via next prompt, rewake,
  mid-turn PostToolUse redirect, and pause deny/resume all verified. Evidence kept in the
  session scratchpad.

## Architecture

One hub per project: `<project>/.dashboard/` (git-excluded via `info/exclude`).

```
.dashboard/
  hub.json                 {schema:2, project, created}
  index.html               copied from assets/dashboard.html (versioned)
  data.js                  window.__hub(<snapshot>) — atomic mirror for file:// mode
  server.json              {port, pid, started} (0600; token stored separately)
  .token                   random token (0600), never written into data.js
  mote.json                cached mote snapshot {fetched, ...}
  sessions/<sid>/
    session.json           {id, agent, label, cwd, started, last_seen, ended?}
    plan.json              narrative state (v1 state schema, per session)
    events.jsonl           hook-captured events (rotated at 5000 lines)
    inbox.jsonl            messages from the page (append-only; status by id)
    paused                 flag file while the user has paused the session
```

Two data layers:

- **Ground truth** (automatic, Claude hooks): SessionStart, UserPromptSubmit, PreToolUse,
  PostToolUse, PostToolUseFailure (if available), Notification, Stop, SubagentStop,
  SessionEnd. Hooks only act when a hub exists at or above the session cwd; otherwise
  they exit 0 in well under 100 ms. Hook failures never affect the agent (always exit 0,
  except intentional deny/block outputs).
- **Narrative** (agent-reported through `dash.py`): plan, tasks, questions, blockers,
  metrics, deliverables, log. Sparse by design: milestones, decisions, blockers.

Every session in a project with a hub appears automatically as a lane, even without a plan.

## Snapshot contract (`data.js` and `GET /api/hub`)

`data.js` is `window.__hub(SNAPSHOT);`. All times are ISO-8601 with offset. The page
computes every relative time from `Date.now()`. Unknown values are `null`, never 0.

```jsonc
{
  "schema": 2,
  "generated": "2026-09-30T10:12:03.120-04:00",
  "revision": 1841,                       // monotonic across the hub
  "project": {
    "name": "neuroim2", "root": "/abs/path",
    "git": {"branch": "main", "head": "a1b2c3d", "subject": "…", "dirty": 7} // or null
  },
  "server": {"running": true, "started": "…"},   // never contains the token or port secret
  "style": {"theme": "dark", "density": "dense", "accent": "#6366f1", "notes": ""},
  "sessions": [{
    "id": "8f3c…", "short": "8f3c", "agent": "claude", "label": "fix check NOTES",
    "cwd": "/abs", "started": "…", "last_seen": "…", "ended": null,
    "activity": "working",   // working | waiting_permission | waiting_user | idle | stalled | paused | ended
    "activity_since": "…",
    "current": {"tool": "Bash", "summary": "R CMD check --as-cran", "started": "…"}, // or null
    "last_prompt": {"ts": "…", "text": "first 280 chars"},       // or null
    "attention": [ {"kind": "permission", "text": "Claude needs permission to use Bash", "ts": "…"} ],
    "plan": {                                   // or null when the agent never ran dash.py init
      "title": "…", "goal": "…", "context": "…",
      "status": "on_track", "status_note": "…", "status_updated": "…",
      "tasks": [{"id": 1, "title": "…", "detail": "…", "status": "doing", "note": "…",
                 "started": "…", "finished": null}],
      "questions": [{"id": "Q1", "text": "…", "default": "…", "asked": "…",
                     "answer": null, "answered": null, "answered_via": null}],
      "blockers": [{"id": "B1", "text": "…", "needs": "…", "opened": "…", "closed": null}],
      "metrics": [{"name": "Tests passing", "value": 41, "total": 50, "unit": null,
                   "good": "up", "updated": "…", "history": [["…", 38], ["…", 41]]}],
      "deliverables": [{"path": "/abs/report.html", "label": "Report", "ts": "…", "note": null}],
      "log": [{"ts": "…", "text": "…"}]
    },
    "stats": {"tool_calls": 212, "edits": 31, "commands": 64, "failures": 5,
              "turns": 9, "subagents": 2, "files_touched": 18},
    "tests": [{"ts": "…", "runner": "testthat", "passed": 120, "failed": 2,
               "skipped": 3, "command": "devtools::test()"}],       // oldest → newest, ≤50
    "files": [{"path": "R/read_vol.R", "edits": 6, "reads": 3, "last": "…"}], // top 40 by recency
    "events": [{                                // newest last, ≤300
      "id": 5512, "ts": "…", "kind": "tool",    // tool | prompt | turn_end | notify | session | note | message | test
      "tool": "Edit", "summary": "R/read_vol.R", "detail": "optional short text",
      "ok": true, "duration_ms": 210, "subagent": null   // subagent type/label when inside one
    }],
    "inbox": [{"id": "m3", "ts": "…", "kind": "message", "text": "…", "qid": null,
               "status": "delivered", "delivered": "…", "via": "PostToolUse"}],
    "paused": false
  }],
  "conflicts": [{"path": "R/read_vol.R", "sessions": ["8f3c", "a91e"], "mote_reserved_by": null}],
  "mote": null /* or */ {
    "store": "/abs/.mote", "fetched": "…", "error": null,
    "counts": {"open": 31, "doing": 4, "blocked": 2, "review": 1},
    "doing": [{"id": "bd-…", "title": "…", "assignee": "chief", "tags": ["…"], "priority": 1}],
    "ready": [ /* same shape, ≤12 */ ],
    "blocked": [ /* same shape, ≤12 */ ],
    "reservations": [{"actor": "…", "paths": ["…"], "issue": "bd-…", "expires": "…"}],
    "actors": [{"actor": "…", "status": "…", "expires": "…"}],
    "posts": [{"id": "post-…", "topic": "…", "from": "…", "ts": "…", "excerpt": "…", "replies": 3}]
  }
}
```

Activity derivation: `waiting_permission` when a permission Notification follows the
last tool event; `working` inside a turn (prompt seen, no Stop); `stalled` when working,
no current tool, and no event for 10 minutes; `idle` after Stop; `paused` when the flag
exists; `ended` after SessionEnd or no heartbeat for 6 hours.

## Server (optional)

`dash.py serve` — stdlib `ThreadingHTTPServer` bound to 127.0.0.1 only, random free port,
random token in `.dashboard/.token` (0600). URL printed as `http://127.0.0.1:PORT/#k=TOKEN`
(fragment is never sent in requests; the page keeps it in `sessionStorage` and sends
`X-Dash-Token`). Rejects: wrong/missing token (all `/api/*`), `Host` not
`127.0.0.1:PORT`/`localhost:PORT` (DNS rebinding), cross-origin `Origin`, non-JSON bodies,
bodies over 16 KB. Auto-exits after 2 h without any session activity; `dash.py stop` stops it.

- `GET /` → page; `GET /api/hub` → snapshot (page polls every 2 s in server mode).
- `POST /api/sessions/<sid>/messages` `{kind: "message"|"answer", text, qid?}`
- `POST /api/sessions/<sid>/pause` / `/resume`
- `POST /api/mote/post` `{topic?, text}` → `mote discuss post …` (only when mote present).

## Delivery

- Claude: PostToolUse → `additionalContext`; UserPromptSubmit → `additionalContext`;
  Stop → `decision: block` when undelivered messages exist (not when `stop_hook_active`).
  Answers also resolve the question in `plan.json` (`answered_via: "dashboard"`).
- Pause: PreToolUse denies tool calls (except `dash.py` itself) with a reason telling the
  agent the user paused it from the dashboard and it should end its turn; Stop is allowed.
- Codex / no hooks: every `dash.py` invocation prints undelivered messages to stdout and
  marks them delivered (`via: "cli"`). The skill tells Codex to run `dash.py inbox` at milestones.
- Messages are framed as user messages from the dashboard, treated with the same authority
  as a chat message; the framing text names the source.

## Page

Fixed page `assets/dashboard.html` (+ any bundled assets). Works in file mode (script
injection of `data.js?t=` every 3 s) and server mode (fetch `/api/hub` every 2 s, composer
enabled). Priorities, in order:

1. **Five-second read:** what is each agent doing right now, is it OK, does it need me.
2. **Actionable:** a "Needs you" surface (permission waits, open questions with inline
   answers, blockers, stalls, file conflicts), message composer per session, pause/resume.
3. **Window into the work:** live current tool with ticking elapsed time, activity timeline
   grouped by turn, files touched, test trend, plan progress, metrics, deliverables.
4. **Multi-session:** one lane per session; conflicts across sessions; mote panel.
5. Honest: stale-data warnings, sparse and empty states, no invented numbers.

Style: `style.md` theme/density/accent apply. Light and dark both first-class.

## Hill climb

Using `visual-hill-climb`. Specimens (fixture snapshots, rendered at 1440×900 and 390×844,
light and dark): `solo-rcheck` (mid-flight R CMD check with failures), `trio-mote`
(three sessions + mote + a file conflict), `needs-you` (permission wait + open question +
blocker), `slurm-long` (two-hour campaign, long current command), `fresh` (just started,
no plan), `done` (finished run), `stalled`.

Rubric (1–5 each): five-second read, actionability, insight/depth, visual quality
(typography, hierarchy, rhythm, colour), multi-session clarity, honesty/states,
accessibility (contrast, focus, keyboard). Independent fresh-context critics per round;
a round is accepted only when no dimension regresses and gates pass.

Gates: unit tests (dash.py, hook, server security, concurrency), `skills.py check`,
browser check of every specimen (no console errors, no horizontal scroll, contrast),
E2E message round trip with a live Claude session (requires user go-ahead for nested
`claude -p` runs).

Outcome (2026-09-30): seven rounds (r0–r6), three critics each (visual, function and
accessibility, target user). r2 was rejected on honesty and repaired in r3; the others were
accepted. Mean overall score rose from 3.71 (r1) to 4.21 (r6); honesty 3.83 → 4.5,
multi-session 3.5 → 4.33, accessibility 3.5 → 4.0, visual 3.67 → 4.17. The climb stopped when
gains fell to about +0.05 a round. Page 2.5.2 is r6 plus a gate-checked, unscored fix for
clipped destructive targets. Open at close: queued messages show no age, the server banner
does not age with stale data, the stale banner is long, and mobile has no "as of" time.
Live E2E on Claude Code 2.1.286 (Haiku, tmux) against 2.5.2 passed next-prompt, rewake,
mid-turn and pause/resume delivery; it found and fixed a duplicate delivery after rewake
(the wake-up turn now starts with a synthetic prompt). Scores are critics' judgements from
fixtures and probes, not user testing.

## Triggering

Replace the "more than 5 steps" rule in `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` and
the skill description with: use when the user asks, or for long mostly-unattended runs
(about an hour or more, cluster jobs, loop runs); otherwise offer in one line.

## Contract notes (backend, 2026-09-30)

Clarifications made while implementing `dash.py` / `dash_hook.py`; the snapshot keys match
the page fixtures exactly (checked by `tests/test_snapshot.py`).

- `plan.json` stores the contract shape (`text`, `opened`/`closed`, metrics as a list with
  `[ts, value]` history, log `{ts, text}`), not the v1 field names. A v1 `state.json` is
  migrated once into session `v1-<run id>`; the old file is kept as `v1-state.json`.
- `waiting_user`: after Stop, when the plan has an unanswered question or Claude raised an
  `idle_prompt` or `elicitation_dialog` notification. `permission_prompt` gives `waiting_permission`;
  without `notification_type` the message text decides.
- Sessions without hooks (Codex, CLI): `working` while `dash.py` was called in the last
  10 minutes, then `idle`; `idle` once the plan status is `done`; `ended` after 6 h or `dash.py end`.
- `current` is the most recent in-flight tool (parallel and subagent calls are tracked by
  `tool_use_id`); in-flight calls are cleared at Stop.
- `short` is the first 4 characters of the id (after the `cli-`/`v1-` prefix).
- R CMD check test entries: `runner: "R CMD check"`, `passed: null`, `failed` = ERRORs +
  WARNINGs + NOTEs, `skipped: null`; the event `detail` keeps the `Status:` line. Go without
  `-v` counts packages (event detail says so).
- `style` keys are `null` when unset or invalid; the page supplies defaults.
- `mote` is `null` without a store or the CLI, and until the first background refresh. Mote
  actors map presence `live`→`active`, `recent`→`idle` (others omitted); `expires` is the lease end.
  Commands run sequentially with a 3 s timeout each; on a large store `mote board` can exceed
  it, in which case `error` names it and `counts` fall back to `mote ls`.
- Sessions ended more than 24 h ago are omitted; at most 16 sessions are shown.
- `revision` is a hub counter bumped on every mutation (hook event, narrative command,
  message, pause, server start/stop, mote refresh).
- `data.js` updates for PreToolUse and PostToolUse are debounced (1 s, unless activity changes)
  with a detached trailing rebuild,
  so the file lags by at most about a second. Server mode builds the snapshot per request.
- The page version marker is `<meta name="dashboard-page" content="agent-dashboard X.Y.Z">`
  (or `<!-- dashboard-page vX.Y -->`). `init`/`render`/`serve` replace an installed page when
  the shipped version is higher, or equal with different content.
- Session binding for Claude: SessionStart writes `export DASH_SESSION=<id>` to `$CLAUDE_ENV_FILE`
  (verified live); pending-command matching is the fallback and is anchored to the argv right
  after the `dash.py` word. `init` never attaches to "the only live session"; without an explicit
  session it starts a new one. When `init` runs inside Claude Code (`CLAUDECODE` set) before the
  hooks have seen the hub, the new `cli-*` session is adopted by the first hook event from a new
  Claude session within 2 minutes; the old id keeps working through `.dashboard/aliases.json`.
- Hook payloads: the live 2.1.285 shapes are the primary path (`tests/payloads/`); failed Bash
  calls arrive only as PostToolUseFailure with `error: "Exit code N\n<output>"`, which is parsed
  for the exit code and test summaries. Also accepted: `tool_output`, `prompt_text`, `tool_error`,
  exit codes under `returncode`/`exit_code`/`exitCode`.
- Idle wake-up (experimental): a message handed over by `--watch-inbox` counts as delivered via
  `rewake`; if the next event is a user prompt rather than a tool call or Stop, the wake-up is
  assumed to have failed and the message is delivered again with that prompt.
- Server: the hub folder is 0700; `/data.js` is not served (the page uses `/api/hub`).
  `GET /api/file?path=<abs>` (token required) serves regular files whose realpath is inside the
  project or equals a recorded deliverable, never anything under `.dashboard/`, up to 50 MB,
  `inline`, with `Content-Security-Policy: sandbox allow-scripts allow-popups allow-downloads`
  so a served HTML report cannot read the dashboard's token.
- Pending-command matching refuses when the same `dash.py` command is in flight in more than one
  session (no guessing). The pause exemption covers only commands that run an installed copy of
  this skill's `dash.py` (path resolves to a folder holding `dash_hook.py` beside a `SKILL.md`)
  plus harmless glue (`cd`, `echo`, redirects, `| tail`), or `$VAR inbox`.
- Delivery is atomic with the emitted output: if recording fails after messages were taken, or
  the hook cannot write its JSON to stdout, the messages are returned to the queue (an `op:
  status, status: queued` record) and a timeline event says so. Failures after the output is
  committed (rebuilding `data.js`, mote) are logged and never drop the output.
- `conflicts[]` (enriched): `{path, sessions, sources, live, last_edit, mote_reserved_by, detail}`.
  A path is listed when at least two distinct agents touch it through any mix of hook-recorded
  edits (last 2 h), unexpired mote reservations (a reservation covers a path or a directory
  prefix) and board posts from the last 24 h whose text names a repo-relative path that exists
  in the project (URLs ignored; the 40 newest posts, 10 paths each, 200 existence checks at most).
  Mote actors map to a session when the actor name is the session id or ends with `-<short>`;
  otherwise the actor name stands for the agent. `sessions` lists only dashboard session shorts;
  `detail[].session` is a short or an actor name, `ts` is the edit time, reservation expiry or
  post time, `expires` is the reservation expiry (null for edits and posts), and `ref` is the mote issue or post id. `live`: an edit within 30 min, or a
  reservation held by a session whose activity is `working`. Post mentions are cached in
  `mote.json` under a private `_mentions` key that never reaches the snapshot. At most 50,
  live first, then most recently edited.
- Timing tests: medians are compared with the spec budget times a load margin of 3
  (`DASH_PERF_SLACK` multiplies it; `DASH_PERF_STRICT=1` checks the bare budget).
- `sessions[].wakeable` (bool | null): `true` while a live `--watch-inbox` watcher waits for the
  idle session. The watcher writes `sessions/<sid>/watch.json` `{pid, started, heartbeat, poll}`
  every poll and removes it on exit; the flag is `true` only if the heartbeat is within
  max(10 s, 3 polls) and the pid is alive, `false` if the record is stale or dead, if the session
  has no hooks (Codex, CLI) or has ended, and `null` when there is no record (rewake not installed,
  or a turn is running). `data.js` is rebuilt when a watcher starts and stops. Delivery through the
  watcher records `via: "rewake"`.
- `mote.reservations[].created`: mote's reservation listings carry no creation field, so it is
  decoded from the reservation id, a ULID minted at creation (checked against a real reservation:
  id time = lease end minus the 1 h default TTL); `null` if the id is not a ULID. In
  `conflicts[].detail`, a reservation's `ts` is this creation time and `expires` is its lease end.
- Question and blocker ids are never reused within a session: the counters live in
  `session.json` (`seq`) and survive `init --force`. An inbox answer's `qid` therefore matches
  at most one question ever; after a reset it matches none, and `queue_message` refuses answers
  to questions that are not in the current plan. No generation field is needed.
- `destructive: {label, match, severity} | null` on `sessions[].current` and on every
  `sessions[].attention[]` item (non-null only for `permission` items, taken from the in-flight
  call recorded at PreToolUse). Computed on the full redacted Bash command before any truncation,
  per simple command after splitting at `;`, `&&`, `||`, pipes, `&`, subshells, `$(...)`, backticks
  and newlines; `bash/sh -c`, `eval`, `ssh host '...'` and wrapper words (`sudo`, `env`, `xargs`,
  `timeout`, `nohup`, assignments) are looked through. Arguments of echo/printf/git commit and
  heredoc bodies of non-interpreters are data, not commands. `label` names the pattern (e.g.
  `rm -rf`, `git push --force`, `SQL DELETE without WHERE`), `match` is the offending simple
  command (≤160 chars), `severity` is `high`, or `medium` for `git push --force-with-lease` and
  `chmod/chown/chgrp -R`. Other tools: `null`.
  `match` is shell-quoted (`shlex.join`), with wrapper words and their option values
  (`sudo -u bob`, `srun -n 1`, `nice -n 10`), redirects with their fd numbers (`2>/dev/null`) and
  unquoted `#` comments removed; a match cut at 160 characters ends in `…`, and the page then shows
  no target. Dry runs (`rsync -n`, `git clean -n`) are not flagged.
